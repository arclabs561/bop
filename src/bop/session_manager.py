"""Hierarchical session-based persistence for learning data with advanced features."""

from typing import Dict, List, Any, Optional, Set, Protocol, Callable, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, OrderedDict
import json
import uuid
import time
import hashlib
import logging
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field, field_validator, ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class EvaluationEntry:
    """A single evaluation entry within a session."""
    query: str
    response: str
    response_length: int
    score: float
    judgment_type: str
    quality_flags: List[str]
    reasoning: str
    metadata: Dict[str, Any]
    timestamp: str
    evaluation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Session:
    """A session containing multiple evaluations with lifecycle management."""
    session_id: str
    created_at: str
    updated_at: str
    status: str = "active"  # active, closed, archived
    closed_at: Optional[str] = None
    final_statistics: Optional[Dict[str, Any]] = None
    inactivity_timeout: float = 3600.0  # 1 hour default
    context: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    evaluations: List[EvaluationEntry] = field(default_factory=list)
    version: str = "1.0"  # For migration support
    
    def is_active(self) -> bool:
        """Check if session is still active."""
        if self.status != "active":
            return False
        # Check inactivity timeout
        last_update = datetime.fromisoformat(self.updated_at)
        elapsed = (datetime.now(timezone.utc) - last_update).total_seconds()
        return elapsed < self.inactivity_timeout
    
    def close(self, finalize: bool = True):
        """Close session and finalize statistics."""
        self.status = "closed"
        self.closed_at = datetime.now(timezone.utc).isoformat()
        if finalize:
            self.final_statistics = self.get_statistics()
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def add_evaluation(self, entry: EvaluationEntry):
        """Add an evaluation to this session."""
        self.evaluations.append(entry)
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session-level statistics."""
        if not self.evaluations:
            return {
                "evaluation_count": 0,
                "mean_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "quality_issues": {},
                "schemas_used": [],
            }
        
        scores = [e.score for e in self.evaluations]
        quality_issues = defaultdict(int)
        for e in self.evaluations:
            for flag in e.quality_flags:
                quality_issues[flag] += 1
        
        return {
            "evaluation_count": len(self.evaluations),
            "mean_score": sum(scores) / len(scores) if scores else 0.0,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "quality_issues": dict(quality_issues),
            "schemas_used": list(set(e.metadata.get("schema") for e in self.evaluations if e.metadata.get("schema"))),
        }


@dataclass
class SessionGroup:
    """A group of sessions (e.g., by time period, topic, or user)."""
    group_id: str
    name: str
    created_at: str
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_ids: List[str] = field(default_factory=list)
    
    def add_session(self, session_id: str):
        """Add a session to this group."""
        if session_id not in self.session_ids:
            self.session_ids.append(session_id)
            self.updated_at = datetime.now(timezone.utc).isoformat()


@dataclass
class SessionIndex:
    """Index entry for fast session lookups."""
    session_id: str
    created_at: str
    updated_at: str
    user_id: Optional[str]
    context: Optional[str]
    mean_score: float
    evaluation_count: int
    status: str


# ============================================================================
# Pydantic Validation Models
# ============================================================================

class SessionModel(BaseModel):
    """Pydantic model for session validation."""
    session_id: str
    created_at: str
    updated_at: str
    status: str = Field(default="active", pattern="^(active|closed|archived)$")
    closed_at: Optional[str] = None
    final_statistics: Optional[Dict[str, Any]] = None
    inactivity_timeout: float = 3600.0
    context: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    version: str = "1.0"
    checksum: Optional[str] = None
    
    @field_validator('created_at', 'updated_at', 'closed_at')
    @classmethod
    def validate_iso_datetime(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISO datetime format."""
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO datetime: {v}")
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for integrity verification."""
        data = self.model_dump_json(exclude={'checksum'})
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_checksum(self) -> bool:
        """Verify session integrity."""
        if not self.checksum:
            return False
        return self.calculate_checksum() == self.checksum


# ============================================================================
# Storage Abstraction (Repository Pattern)
# ============================================================================

class SessionStorage(Protocol):
    """Storage interface for sessions."""
    
    def save_session(self, session: Session) -> None: ...
    def load_session(self, session_id: str) -> Optional[Session]: ...
    def list_session_ids(self) -> List[str]: ...
    def delete_session(self, session_id: str) -> None: ...


class FileSessionStorage:
    """File-based session storage with atomic writes."""
    
    def __init__(self, sessions_dir: Path):
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session: Session) -> None:
        """Save session with atomic write."""
        session_file = self.sessions_dir / f"{session.session_id}.json"
        temp_file = session_file.with_suffix('.json.tmp')
        
        try:
            # Validate and calculate checksum
            session_model = SessionModel(
                session_id=session.session_id,
                created_at=session.created_at,
                updated_at=session.updated_at,
                status=session.status,
                closed_at=session.closed_at,
                final_statistics=session.final_statistics,
                inactivity_timeout=session.inactivity_timeout,
                context=session.context,
                user_id=session.user_id,
                metadata=session.metadata,
                evaluations=[asdict(e) for e in session.evaluations],
                version=session.version,
            )
            session_model.checksum = session_model.calculate_checksum()
            
            # Write to temp file
            temp_file.write_text(json.dumps(session_model.model_dump(), indent=2))
            # Atomic rename
            temp_file.replace(session_file)
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """Load session with validation."""
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return None
        
        try:
            data = json.loads(session_file.read_text())
            
            # Validate with Pydantic
            session_model = SessionModel(**data)
            
            # Verify checksum
            if not session_model.verify_checksum():
                logger.warning(f"Checksum mismatch for {session_file.name}, attempting repair")
                # Recalculate checksum
                session_model.checksum = session_model.calculate_checksum()
                # Could save repaired version here
            
            # Convert to Session dataclass
            session = Session(
                session_id=session_model.session_id,
                created_at=session_model.created_at,
                updated_at=session_model.updated_at,
                status=session_model.status,
                closed_at=session_model.closed_at,
                final_statistics=session_model.final_statistics,
                inactivity_timeout=session_model.inactivity_timeout,
                context=session_model.context,
                user_id=session_model.user_id,
                metadata=session_model.metadata,
                evaluations=[
                    EvaluationEntry(**e) if isinstance(e, dict) else e
                    for e in session_model.evaluations
                ],
                version=session_model.version,
            )
            return session
            
        except ValidationError as e:
            logger.error(f"Validation error for {session_file.name}: {e}")
            for error in e.errors():
                logger.error(f"  Field {error['loc']}: {error['msg']}")
            return None
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    def list_session_ids(self) -> List[str]:
        """List all session IDs."""
        return [
            f.stem for f in self.sessions_dir.glob("*.json")
            if f.name not in ("groups.json", "index.json")
        ]
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()


# ============================================================================
# LRU Cache for Sessions
# ============================================================================

class LRUSessionCache:
    """LRU cache for sessions."""
    
    def __init__(self, maxsize: int = 100):
        self.cache: OrderedDict[str, Session] = OrderedDict()
        self.maxsize = maxsize
    
    def get(self, session_id: str) -> Optional[Session]:
        """Get session, marking as recently used."""
        if session_id in self.cache:
            self.cache.move_to_end(session_id)
            return self.cache[session_id]
        return None
    
    def put(self, session_id: str, session: Session):
        """Add session, evicting LRU if at capacity."""
        if session_id in self.cache:
            self.cache.move_to_end(session_id)
        else:
            if len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)
            self.cache[session_id] = session
    
    def evict(self, session_id: str):
        """Remove session from cache."""
        self.cache.pop(session_id, None)
    
    def clear(self):
        """Clear all cached sessions."""
        self.cache.clear()


# ============================================================================
# Write Buffering
# ============================================================================

class WriteBuffer:
    """Buffers writes to reduce I/O operations."""
    
    def __init__(self, batch_size: int = 10, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._buffer: Dict[str, Session] = {}
        self._pending_writes = 0
        self._last_flush = time.time()
    
    def add(self, session: Session) -> bool:
        """Add session to buffer. Returns True if flush should occur."""
        self._buffer[session.session_id] = session
        self._pending_writes += 1
        
        should_flush = (
            self._pending_writes >= self.batch_size or
            time.time() - self._last_flush > self.flush_interval
        )
        return should_flush
    
    def flush(self, storage: SessionStorage) -> int:
        """Flush all buffered sessions to storage."""
        if not self._buffer:
            return 0
        
        count = 0
        for session in self._buffer.values():
            try:
                storage.save_session(session)
                count += 1
            except Exception as e:
                logger.error(f"Failed to flush session {session.session_id}: {e}")
                # Keep in buffer for retry
        
        self._buffer.clear()
        self._pending_writes = 0
        self._last_flush = time.time()
        return count
    
    def clear(self):
        """Clear buffer."""
        self._buffer.clear()
        self._pending_writes = 0


# ============================================================================
# Main Session Manager
# ============================================================================

class HierarchicalSessionManager:
    """
    Manages hierarchical session-based persistence with advanced features.
    
    Features:
    - Write buffering for performance
    - Session lifecycle management
    - Pydantic validation with checksums
    - Indexing for fast lookups
    - Lazy loading with LRU cache
    - Storage abstraction
    """
    
    def __init__(
        self,
        sessions_dir: Optional[Path] = None,
        auto_group_by: Optional[str] = "day",
        storage: Optional[SessionStorage] = None,
        enable_buffering: bool = True,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        cache_size: int = 100,
        enable_indexing: bool = True,
    ):
        """
        Initialize hierarchical session manager.
        
        Args:
            sessions_dir: Directory to store session data
            auto_group_by: How to automatically group sessions
            storage: Storage backend (defaults to FileSessionStorage)
            enable_buffering: Enable write buffering
            batch_size: Number of writes before flush
            flush_interval: Seconds before auto-flush
            cache_size: Maximum sessions in LRU cache
            enable_indexing: Enable indexing for fast lookups
        """
        # Use persistent cache directory if available (Fly.io Volumes)
        if sessions_dir is None:
            if Path("/data").exists():
                # Fly.io Volume mounted - use persistent directory
                sessions_dir = Path("/data/sessions")
            else:
                # Local development - use local sessions directory
                sessions_dir = Path("sessions")
        
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.auto_group_by = auto_group_by
        
        # Storage abstraction
        self.storage = storage or FileSessionStorage(self.sessions_dir)
        
        # Write buffering
        self.enable_buffering = enable_buffering
        self.write_buffer = WriteBuffer(batch_size, flush_interval) if enable_buffering else None
        
        # LRU cache for lazy loading
        self.cache = LRUSessionCache(maxsize=cache_size)
        
        # Indexing
        self.enable_indexing = enable_indexing
        self.index_file = self.sessions_dir / "index.json"
        self.index: Dict[str, SessionIndex] = {}
        
        # In-memory structures (metadata only, not full sessions)
        self._session_metadata: Dict[str, SessionIndex] = {}
        self.groups: Dict[str, SessionGroup] = {}
        self.current_session_id: Optional[str] = None
        
        # Load index and groups (not full sessions - lazy loading)
        if self.enable_indexing:
            self._load_index()
        self._load_groups()
    
    # ========================================================================
    # Session Lifecycle Management
    # ========================================================================
    
    def create_session(
        self,
        context: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        set_as_current: bool = True,
    ) -> str:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        session = Session(
            session_id=session_id,
            created_at=now,
            updated_at=now,
            context=context,
            user_id=user_id,
            metadata=metadata or {},
        )
        
        # Save immediately (not buffered for new sessions)
        self.storage.save_session(session)
        
        # Update cache and index
        self.cache.put(session_id, session)
        if self.enable_indexing:
            self._update_index(session)
        
        if set_as_current:
            self.current_session_id = session_id
        
        # Auto-group if enabled
        if self.auto_group_by:
            self._add_to_groups(session)
        
        return session_id
    
    def close_session(self, session_id: str, finalize: bool = True):
        """Close a session."""
        session = self.get_session(session_id)
        if not session:
            return
        
        session.close(finalize=finalize)
        self._save_session(session)
    
    def auto_close_inactive_sessions(self, timeout: Optional[float] = None):
        """Auto-close sessions that have been inactive."""
        timeout = timeout or 3600.0  # 1 hour default
        now = datetime.now(timezone.utc)
        
        # Check all sessions in index
        for session_id, idx in list(self.index.items()):
            if idx.status == "active":
                # Load session to check
                session = self.get_session(session_id)
                if session and not session.is_active():
                    last_update = datetime.fromisoformat(session.updated_at)
                    elapsed = (now - last_update).total_seconds()
                    if elapsed > timeout:
                        self.close_session(session_id, finalize=True)
    
    # ========================================================================
    # Lazy Loading with Cache
    # ========================================================================
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Lazy load session from cache or storage."""
        # Check cache first
        session = self.cache.get(session_id)
        if session:
            return session
        
        # Load from storage
        session = self.storage.load_session(session_id)
        if session:
            self.cache.put(session_id, session)
        return session
    
    # ========================================================================
    # Write Operations with Buffering
    # ========================================================================
    
    def _save_session(self, session: Session):
        """Save session (buffered if enabled)."""
        if self.enable_buffering and self.write_buffer:
            should_flush = self.write_buffer.add(session)
            if should_flush:
                self.write_buffer.flush(self.storage)
        else:
            self.storage.save_session(session)
        
        # Update cache and index
        self.cache.put(session.session_id, session)
        if self.enable_indexing:
            self._update_index(session)
    
    def flush_buffer(self):
        """Manually flush write buffer."""
        if self.write_buffer:
            return self.write_buffer.flush(self.storage)
        return 0
    
    # ========================================================================
    # Indexing
    # ========================================================================
    
    def _load_index(self):
        """Load index from disk."""
        if not self.index_file.exists():
            return
        
        try:
            data = json.loads(self.index_file.read_text())
            self.index = {
                sid: SessionIndex(**idx_data)
                for sid, idx_data in data.items()
            }
            self._session_metadata = self.index.copy()
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            self.index = {}
            self._session_metadata = {}
    
    def _save_index(self):
        """Save index to disk."""
        if not self.enable_indexing:
            return
        
        data = {
            sid: asdict(idx)
            for sid, idx in self.index.items()
        }
        # Atomic write
        temp_file = self.index_file.with_suffix('.json.tmp')
        try:
            temp_file.write_text(json.dumps(data, indent=2))
            temp_file.replace(self.index_file)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def _update_index(self, session: Session):
        """Update index entry for session."""
        if not self.enable_indexing:
            return
        
        stats = session.get_statistics()
        self.index[session.session_id] = SessionIndex(
            session_id=session.session_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            user_id=session.user_id,
            context=session.context,
            mean_score=stats.get("mean_score", 0.0),
            evaluation_count=stats.get("evaluation_count", 0),
            status=session.status,
        )
        self._session_metadata[session.session_id] = self.index[session.session_id]
        self._save_index()
    
    def query_sessions(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        user_id: Optional[str] = None,
        context: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[str]:
        """Fast query using index."""
        if not self.enable_indexing:
            # Fallback to full scan
            return [sid for sid in self.storage.list_session_ids()]
        
        matching_ids = []
        
        for sid, idx in self.index.items():
            # Date filtering
            if date_from:
                if datetime.fromisoformat(idx.created_at) < date_from:
                    continue
            if date_to:
                if datetime.fromisoformat(idx.created_at) > date_to:
                    continue
            
            # Score filtering
            if min_score is not None and idx.mean_score < min_score:
                continue
            if max_score is not None and idx.mean_score > max_score:
                continue
            
            # Other filters
            if user_id and idx.user_id != user_id:
                continue
            if context and idx.context != context:
                continue
            if status and idx.status != status:
                continue
            
            matching_ids.append(sid)
        
        return matching_ids
    
    # ========================================================================
    # Evaluation Management
    # ========================================================================
    
    def add_evaluation(
        self,
        query: str,
        response: str,
        response_length: int,
        score: float,
        judgment_type: str,
        quality_flags: List[str],
        reasoning: str,
        metadata: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> str:
        """Add an evaluation to a session."""
        # Use current session or create new one
        if not session_id:
            if not self.current_session_id:
                self.create_session()
            session_id = self.current_session_id
        
        session = self.get_session(session_id)
        if not session:
            session_id = self.create_session()
            session = self.get_session(session_id)
        
        # Create evaluation entry
        entry = EvaluationEntry(
            query=query,
            response=response[:1000],  # Truncate for storage
            response_length=response_length,
            score=score,
            judgment_type=judgment_type,
            quality_flags=quality_flags,
            reasoning=reasoning,
            metadata=metadata,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        # Add to session
        session.add_evaluation(entry)
        
        # Save session (buffered)
        self._save_session(session)
        
        return entry.evaluation_id
    
    # ========================================================================
    # Grouping
    # ========================================================================
    
    def _add_to_groups(self, session: Session):
        """Add a session to relevant groups based on auto_group_by."""
        now = datetime.now(timezone.utc)
        group_ids_to_add = set()
        
        if self.auto_group_by == "day":
            date = datetime.fromisoformat(session.created_at).date()
            group_ids_to_add.add(f"day_{date.isoformat()}")
        elif self.auto_group_by == "week":
            date = datetime.fromisoformat(session.created_at).date()
            year, week, _ = date.isocalendar()
            group_ids_to_add.add(f"week_{year}_{week:02d}")
        elif self.auto_group_by == "month":
            date = datetime.fromisoformat(session.created_at).date()
            group_ids_to_add.add(f"month_{date.year}_{date.month:02d}")
        elif self.auto_group_by == "topic" and session.context:
            group_ids_to_add.add(f"topic_{session.context.replace(' ', '_').lower()}")
        
        for group_id in group_ids_to_add:
            if group_id not in self.groups:
                self.groups[group_id] = SessionGroup(
                    group_id=group_id,
                    name=self._get_group_name(session, self.auto_group_by),
                    created_at=now.isoformat(),
                )
            if session.session_id not in self.groups[group_id].session_ids:
                self.groups[group_id].add_session(session.session_id)
        
        self._save_groups()
    
    def _get_group_name(self, session: Session, group_by: str) -> str:
        """Get human-readable group name."""
        if group_by == "day":
            date = datetime.fromisoformat(session.created_at).date()
            return f"Day: {date.isoformat()}"
        elif group_by == "week":
            date = datetime.fromisoformat(session.created_at).date()
            year, week, _ = date.isocalendar()
            return f"Week {week}, {year}"
        elif group_by == "month":
            date = datetime.fromisoformat(session.created_at).date()
            return f"{date.strftime('%B %Y')}"
        elif group_by == "topic":
            return f"Topic: {session.context or 'General'}"
        else:
            return "Default Group"
    
    def _load_groups(self):
        """Load groups from disk."""
        groups_file = self.sessions_dir / "groups.json"
        if groups_file.exists():
            try:
                groups_data = json.loads(groups_file.read_text())
                for group_id, group_data in groups_data.items():
                    self.groups[group_id] = SessionGroup(**group_data)
            except Exception:
                pass  # Groups will be rebuilt if needed
    
    def _save_groups(self):
        """Save groups to disk."""
        groups_file = self.sessions_dir / "groups.json"
        groups_data = {
            group_id: asdict(group)
            for group_id, group in self.groups.items()
        }
        # Atomic write
        temp_file = groups_file.with_suffix('.json.tmp')
        try:
            temp_file.write_text(json.dumps(groups_data, indent=2))
            temp_file.replace(groups_file)
        except Exception as e:
            logger.error(f"Failed to save groups: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    # ========================================================================
    # Query and List Operations
    # ========================================================================
    
    def get_current_session(self) -> Optional[Session]:
        """Get the current active session."""
        if self.current_session_id:
            return self.get_session(self.current_session_id)
        return None
    
    def get_group(self, group_id: str) -> Optional[SessionGroup]:
        """Get a group by ID."""
        return self.groups.get(group_id)
    
    def list_sessions(
        self,
        group_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Session]:
        """List sessions with optional filtering."""
        # Use index for fast filtering if available
        if self.enable_indexing:
            session_ids = self.query_sessions(
                user_id=user_id,
                status="active",  # Default to active only
            )
            
            # Filter by group
            if group_id:
                group = self.groups.get(group_id)
                if group:
                    session_ids = [sid for sid in session_ids if sid in group.session_ids]
            
            # Load sessions (lazy)
            sessions = [self.get_session(sid) for sid in session_ids]
            sessions = [s for s in sessions if s is not None]
        else:
            # Fallback: load all and filter
            session_ids = self.storage.list_session_ids()
            sessions = [self.get_session(sid) for sid in session_ids]
            
            if group_id:
                group = self.groups.get(group_id)
                if group:
                    session_ids = set(group.session_ids)
                    sessions = [s for s in sessions if s.session_id in session_ids]
            
            if user_id:
                sessions = [s for s in sessions if s.user_id == user_id]
        
        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        
        # Limit
        if limit:
            sessions = sessions[:limit]
        
        return sessions
    
    def list_groups(self) -> List[SessionGroup]:
        """List all groups."""
        return list(self.groups.values())
    
    def get_aggregate_statistics(
        self,
        group_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get aggregate statistics across sessions."""
        sessions = self.list_sessions(group_id=group_id, user_id=user_id)
        
        if not sessions:
            return {
                "session_count": 0,
                "total_evaluations": 0,
                "mean_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "quality_issues": {},
                "schemas_used": [],
            }
        
        all_evaluations = []
        for session in sessions:
            all_evaluations.extend(session.evaluations)
        
        if not all_evaluations:
            return {
                "session_count": len(sessions),
                "total_evaluations": 0,
                "mean_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "quality_issues": {},
                "schemas_used": [],
            }
        
        scores = [e.score for e in all_evaluations]
        quality_issues = defaultdict(int)
        for e in all_evaluations:
            for flag in e.quality_flags:
                quality_issues[flag] += 1
        
        schemas_used = set()
        for e in all_evaluations:
            schema = e.metadata.get("schema")
            if schema:
                schemas_used.add(schema)
        
        return {
            "session_count": len(sessions),
            "total_evaluations": len(all_evaluations),
            "mean_score": sum(scores) / len(scores) if scores else 0.0,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "quality_issues": dict(quality_issues),
            "schemas_used": list(schemas_used),
            "time_span": {
                "earliest": min(s.created_at for s in sessions),
                "latest": max(s.updated_at for s in sessions),
            },
        }
    
    # ========================================================================
    # Archive and Cleanup
    # ========================================================================
    
    def archive_session(self, session_id: str, archive_dir: Optional[Path] = None):
        """Archive a session to a separate directory."""
        session = self.get_session(session_id)
        if not session:
            return
        
        archive_dir = archive_dir or self.sessions_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Move session file
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            archive_file = archive_dir / f"{session_id}.json"
            session_file.rename(archive_file)
        
        # Update status
        session.status = "archived"
        self._save_session(session)
        
        # Remove from cache
        self.cache.evict(session_id)
        
        # Remove from groups
        for group in self.groups.values():
            if session_id in group.session_ids:
                group.session_ids.remove(session_id)
        
        self._save_groups()
        
        # Update index
        if self.enable_indexing and session_id in self.index:
            self.index[session_id].status = "archived"
            self._save_index()
