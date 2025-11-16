"""
Meta-learning capabilities for BOP: self-reflection, tool meta-learning, and dynamic context engineering.

Based on MetaAgent research: self-evolving agentic paradigm via tool meta-learning.
"""

import logging
from typing import Any, Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ExperienceStore:
    """
    Stores and retrieves task completion experiences for dynamic context engineering.
    
    Based on MetaAgent research: experience is dynamically incorporated into future contexts.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize experience store.
        
        Args:
            storage_path: Optional path to persist experiences
        """
        self.storage_path = storage_path or Path("data/results/experiences.json")
        self.experiences: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._load_experiences()
    
    def _load_experiences(self):
        """Load persisted experiences."""
        if self.storage_path and self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for q_type, exps in data.items():
                    self.experiences[q_type].extend(exps)
                logger.info(f"Loaded {sum(len(exps) for exps in self.experiences.values())} experiences")
            except Exception as e:
                logger.warning(f"Failed to load experiences: {e}", exc_info=True)
    
    def _save_experiences(self):
        """Persist experiences."""
        if not self.storage_path:
            return  # No persistence if no path provided
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {q_type: exps[-50:] for q_type, exps in self.experiences.items()}  # Keep last 50 per type
            self.storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save experiences: {e}", exc_info=True)
    
    def add_experience(
        self,
        query_type: str,
        query: str,
        response: str,
        reflection_text: str,
        reflection_type: str,
        tools_used: List[str],
        quality_score: Optional[float] = None,
    ):
        """
        Add a new experience.
        
        Args:
            query_type: Type of query (factual, procedural, etc.)
            query: Original query
            response: Generated response
            reflection_text: Reflection insights
            reflection_type: "self" or "verified"
            tools_used: Tools that were used
            quality_score: Optional quality score
        """
        experience = {
            "query": query,
            "query_type": query_type,
            "reflection_type": reflection_type,
            "reflection_text": reflection_text,
            "tools_used": tools_used,
            "quality_score": quality_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        self.experiences[query_type].append(experience)
        
        # Limit stored experiences per query type (keep most recent 50)
        if len(self.experiences[query_type]) > 50:
            self.experiences[query_type] = self.experiences[query_type][-50:]
        
        self._save_experiences()
    
    def get_relevant_experiences(
        self,
        query_type: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get relevant experiences for a query type.
        
        Args:
            query_type: Type of query
            limit: Maximum number of experiences to return
            
        Returns:
            List of formatted experiences ready for context injection
        """
        # Get experiences for this query type
        relevant = self.experiences.get(query_type, [])
        
        # Also get general experiences
        general = self.experiences.get("general", [])
        
        # Combine and sort by relevance (verified > self, recent > old)
        all_experiences = relevant + general
        all_experiences.sort(
            key=lambda x: (
                1 if x.get("reflection_type") == "verified" else 0,
                x.get("timestamp", ""),
            ),
            reverse=True,
        )
        
        # Select top experiences
        selected = all_experiences[:limit]
        
        # Format for context injection
        formatted = []
        for exp in selected:
            formatted.append({
                "query_type": exp.get("query_type", "general"),
                "insights": exp.get("reflection_text", "")[:300],  # Truncate for context
                "reflection_type": exp.get("reflection_type", "self"),
                "confidence": 0.8 if exp.get("reflection_type") == "verified" else 0.6,
            })
        
        return formatted
    
    def format_for_context(self, experiences: List[Dict[str, Any]]) -> str:
        """
        Format experiences as context string for injection.
        
        Args:
            experiences: List of formatted experiences
            
        Returns:
            Formatted context string
        """
        if not experiences:
            return ""
        
        context = "\n\n## Previous Task Experience:\n"
        for i, exp in enumerate(experiences, 1):
            context += f"\n{i}. {exp.get('insights', '')}\n"
        
        return context


class MetaLearner:
    """
    Meta-learning component that integrates reflection, tool learning, and context engineering.
    
    Integrates into KnowledgeAgent flow:
    1. Before research: Inject relevant experiences into context
    2. After quality evaluation: Trigger reflection and store insights
    3. Continuously: Learn from tool usage patterns
    """
    
    def __init__(
        self,
        experience_store: Optional[ExperienceStore] = None,
        enable_reflection: bool = True,
        enable_context_injection: bool = True,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize meta learner.
        
        Args:
            experience_store: Optional experience store (creates one if not provided)
            enable_reflection: Whether to automatically reflect on task completion
            enable_context_injection: Whether to inject experiences into context
            storage_path: Optional path for experience store persistence
        """
        self.experience_store = experience_store or ExperienceStore(storage_path=storage_path)
        self.enable_reflection = enable_reflection
        self.enable_context_injection = enable_context_injection
    
    def get_context_experience(
        self,
        query: str,
        query_type: str,
        max_experiences: int = 5,
    ) -> str:
        """
        Get experience context to inject before research/response generation.
        
        Args:
            query: User query
            query_type: Classified query type
            max_experiences: Maximum experiences to include
            
        Returns:
            Formatted context string (empty if no experiences or disabled)
        """
        if not self.enable_context_injection:
            return ""
        
        experiences = self.experience_store.get_relevant_experiences(
            query_type=query_type,
            limit=max_experiences,
        )
        
        if not experiences:
            return ""
        
        return self.experience_store.format_for_context(experiences)
    
    async def reflect_on_completion(
        self,
        query: str,
        response: str,
        query_type: str,
        tools_used: List[str],
        quality_score: Optional[float] = None,
        llm_service: Optional[Any] = None,
        reflection_type: str = "self",
        ground_truth: Optional[str] = None,
    ) -> Optional[str]:
        """
        Reflect on task completion and store insights.
        
        Args:
            query: Original query
            response: Generated response
            query_type: Classified query type
            tools_used: Tools that were used
            quality_score: Optional quality score
            llm_service: LLM service for reflection
            reflection_type: "self" or "verified"
            ground_truth: Required for verified reflection
            
        Returns:
            Reflection text if reflection was performed, None otherwise
        """
        if not self.enable_reflection:
            return None
        
        if reflection_type == "verified" and not ground_truth:
            logger.warning("Verified reflection requested but no ground truth provided")
            return None
        
        if not llm_service:
            logger.debug("No LLM service available for reflection")
            return None
        
        # Build reflection prompt
        reflection_prompt = f"""Reflect on this task completion:

Query: {query}
Response: {response[:500]}...
Tools Used: {', '.join(tools_used or [])}

"""
        
        if reflection_type == "verified":
            reflection_prompt += f"""Ground Truth: {ground_truth}

Analyze:
1. What worked well? (successful strategies, effective tool usage)
2. What didn't work? (errors, ineffective approaches)
3. Generalizable insights: What principles can be extracted?
4. How to improve next time?

Focus on meta-level insights that apply to similar tasks, not just this specific case.
"""
        else:
            reflection_prompt += """Analyze:
1. Review reasoning trajectory for validity and factual grounding
2. Identify any uncertainty or flaws
3. What could be improved?
4. What strategies were effective?

Focus on actionable insights for future tasks.
"""
        
        try:
            # Use LLM service for reflection
            reflection_text = await llm_service.generate_response(
                message=reflection_prompt,
                context=None,
                schema=None,
            )
            
            # Store experience
            self.experience_store.add_experience(
                query_type=query_type,
                query=query,
                response=response,
                reflection_text=reflection_text,
                reflection_type=reflection_type,
                tools_used=tools_used,
                quality_score=quality_score,
            )
            
            logger.info(f"Reflection completed and stored for {query_type} query")
            return reflection_text
        
        except Exception as e:
            logger.warning(f"Reflection failed: {e}", exc_info=True)
            return None

