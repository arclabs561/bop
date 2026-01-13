"""Main agent for knowledge structure research and reasoning."""

import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .adaptive_quality import AdaptiveQualityManager
from .knowledge_tracking import KnowledgeTracker
from .llm import LLMService
from .meta_learning import MetaLearner
from .orchestrator import StructuredOrchestrator
from .provenance import build_provenance_map
from .quality_feedback import QualityFeedbackLoop
from .query_refinement import refine_query_from_provenance
from .research import ResearchAgent, load_content
from .schemas import get_schema, hydrate_schema
from .skills import SkillsManager

logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """Main agent for knowledge structure research and interaction."""

    def __init__(
        self,
        content_dir: Optional[Path] = None,
        llm_service: Optional[LLMService] = None,
        enable_quality_feedback: bool = True,
        enable_skills: bool = False,
        skills_dir: Optional[Path] = None,
        enable_system_reminders: bool = False,
        hop_storage: Optional[Path] = None,
    ):
        """
        Initialize the knowledge agent.

        Args:
            content_dir: Directory containing knowledge base content
            llm_service: Optional LLM service (will create one if not provided)
            enable_quality_feedback: Enable quality feedback loop for continuous improvement
            enable_skills: Enable Skills pattern for dynamic context loading
            skills_dir: Directory containing skill files (default: skills/)
            enable_system_reminders: Enable system reminders to keep agent on track
            hop_storage: Optional path to HOP storage directory (enables hop retrieval integration)
        """
        self.research_agent = ResearchAgent()
        self.llm_service = llm_service

        # HOP integration: use hop's retrieval layer if storage provided
        self.hop_storage = hop_storage
        self.hop_store = None
        self.hop_retriever = None
        self._hop_search = None  # Function for hybrid search
        if hop_storage:
            try:
                # Prefer Rust hop_core for better performance
                from hop_core import SqliteDocumentStore, hybrid_search
                db_path = Path(hop_storage) / "storage.db"
                self.hop_store = SqliteDocumentStore(str(db_path))
                self._hop_search = lambda q, limit=10: hybrid_search(
                    str(hop_storage), q, limit=limit
                )
                logger.info(f"✓ HOP retrieval enabled (Rust): {hop_storage}")
            except ImportError:
                # Fallback to Python hop layer
                try:
                    from hop.retrieval import RetrievalLayer
                    from hop.storage import DocumentStore
                    self.hop_store = DocumentStore(hop_storage)
                    self.hop_retriever = RetrievalLayer(self.hop_store)
                    self._hop_search = lambda q, limit=10: self.hop_retriever.search(q, limit=limit)
                    logger.info(f"✓ HOP retrieval enabled (Python): {hop_storage}")
                except ImportError:
                    logger.warning("HOP not available. Install with: pip install hop")
            except Exception as e:
                logger.warning(f"Failed to initialize HOP retrieval: {e}")
        if not self.llm_service:
            try:
                # LLMService will auto-detect backend from environment
                self.llm_service = LLMService()
            except Exception as e:
                # LLM service not available (missing API key, etc.)
                logger.warning(f"LLM service not available: {e}")
                self.llm_service = None
        self.orchestrator = StructuredOrchestrator(
            self.research_agent,
            self.llm_service,
            use_constraints=os.getenv("BOP_USE_CONSTRAINTS", "false").lower() == "true",
            use_muse_selection=os.getenv("BOP_USE_MUSE_SELECTION", "false").lower() == "true",  # NEW: Enable MUSE selection via env var
        )
        self.content_dir = content_dir or Path(__file__).parent.parent.parent / "content"
        self.knowledge_base = load_content(self.content_dir)
        self.conversation_history: List[Dict[str, Any]] = []
        self.prior_beliefs: List[Dict[str, Any]] = []  # Track user's stated beliefs
        self.recent_queries: List[Dict[str, Any]] = []  # Track recent queries for context adaptation

        # Conversation history management (for long sessions)
        self.max_conversation_history = int(os.getenv("BOP_MAX_CONVERSATION_HISTORY", "50"))
        self.conversation_summary: Optional[str] = None  # Summary of truncated history
        # Option to use LLM for better compaction quality (adds latency/cost)
        self.use_llm_compaction = os.getenv("BOP_USE_LLM_COMPACTION", "false").lower() == "true"

        # Token tracking for accurate context window management
        # Approximate: 1 token ≈ 4 characters (common approximation)
        # More accurate: use tiktoken if available
        self._tokenizer = None
        try:
            import tiktoken
            # Try to use tiktoken for accurate token counting
            self._tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4/Claude compatible
            logger.debug("Using tiktoken for accurate token counting")
        except ImportError:
            logger.debug("tiktoken not available, using character-based estimation")
            self._tokenizer = None

        # Observability and self-reflection (for self-improvement)
        self.enable_observability = os.getenv("BOP_ENABLE_OBSERVABILITY", "true").lower() == "true"
        self._metrics = {
            "compaction_events": [],
            "todo_updates": [],
            "reminder_generations": [],
            "errors": [],
            "performance": [],
        } if self.enable_observability else None

        # Metrics persistence
        self.metrics_path = None
        if self.enable_observability:
            metrics_dir = Path(os.getenv("BOP_METRICS_DIR", "data/metrics"))
            metrics_dir.mkdir(parents=True, exist_ok=True)
            self.metrics_path = metrics_dir / "agent_metrics.json"
            self._load_metrics()  # Load historical metrics on startup

        # File-based scratchpad for persistent memory (optional, like Manus's todo.md)
        # Enables TODO list and notes to persist across context resets
        self.enable_scratchpad = os.getenv("BOP_ENABLE_SCRATCHPAD", "false").lower() == "true"
        self.scratchpad_dir = Path(os.getenv("BOP_SCRATCHPAD_DIR", ".bop_scratchpad"))
        if self.enable_scratchpad:
            self.scratchpad_dir.mkdir(parents=True, exist_ok=True)
            # Load existing TODO list from scratchpad if available
            self._load_todo_from_scratchpad()
        self.quality_feedback = QualityFeedbackLoop(
            use_sessions=True,
            session_context="agent_session",
        ) if enable_quality_feedback else None
        # Adaptive manager uses same directory as quality feedback for learning data
        learning_path = None
        if self.quality_feedback:
            learning_path = self.quality_feedback.evaluation_history_path.parent / "adaptive_learning.json"
        self.adaptive_manager = AdaptiveQualityManager(self.quality_feedback, learning_path) if self.quality_feedback else None

        # Knowledge tracking across sessions (with persistence)
        knowledge_path = None
        if self.quality_feedback:
            knowledge_path = self.quality_feedback.evaluation_history_path.parent / "knowledge_tracking.json"
        self.knowledge_tracker = KnowledgeTracker(
            persistence_path=knowledge_path,
            auto_save_interval=10,  # Save every 10 queries
        )

        # Meta-learning component (self-reflection, tool learning, context engineering)
        experience_path = None
        if self.quality_feedback:
            experience_path = self.quality_feedback.evaluation_history_path.parent / "experiences.json"
        self.meta_learner = MetaLearner(
            enable_reflection=True,
            enable_context_injection=True,
            storage_path=experience_path,
        )

        # Skills system (optional, opt-in)
        self.enable_skills = enable_skills
        self.skills_manager = SkillsManager(skills_dir) if enable_skills else None

        # System reminders (optional, opt-in)
        self.enable_system_reminders = enable_system_reminders
        self.todo_list: List[Dict[str, Any]] = []  # Track TODO list for reminders

    async def chat(
        self,
        message: str,
        use_schema: Optional[str] = None,
        use_research: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate response.

        Args:
            message: User message
            use_schema: Optional schema name to use for structured reasoning
            use_research: Whether to conduct deep research

        Returns:
            Response dictionary with fields:
            - response: Main response text (includes source references)
            - response_tiers: Progressive disclosure tiers (summary, structured, detailed, evidence)
            - prior_beliefs: Extracted user beliefs (if any were stated)
            - research: Research results with enhanced topology metrics (if research conducted)
            - quality: Quality evaluation results (if quality feedback enabled)
            - schema_used: Schema that was used
            - research_conducted: Whether research was performed
        """
        response: Dict[str, Any] = {
            "message": message,
            "response": "",
            "schema_used": None,
            "research_conducted": False,
        }

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": message})

        # Load relevant skills if enabled
        skills_context = ""
        if self.enable_skills and self.skills_manager:
            try:
                relevant_skills = self.skills_manager.find_relevant_skills(message, limit=2)
                if relevant_skills:
                    skills_context = "\n\n".join([
                        f"## {skill.name}\n{skill.content[:1000]}..."  # Limit each skill to 1000 chars
                        if len(skill.content) > 1000 else f"## {skill.name}\n{skill.content}"
                        for skill in relevant_skills
                    ])
                    logger.debug(f"Loaded {len(relevant_skills)} relevant skills")
            except Exception as e:
                logger.warning(f"Error loading skills: {e}")

        # Generate system reminders if enabled
        system_reminders = []
        if self.enable_system_reminders:
            system_reminders = self._generate_system_reminders(message)

        schema = None
        # Use structured schema if specified
        if use_schema:
            schema = get_schema(use_schema)
            if schema:
                response["schema_used"] = use_schema
                if self.llm_service:
                    try:
                        hydrated = await self.llm_service.hydrate_schema(schema, message)
                        response["structured_reasoning"] = hydrated
                    except Exception as e:
                        response["structured_reasoning_error"] = str(e)
                        # Fallback to simple hydration
                        response["structured_reasoning"] = hydrate_schema(schema, message)
                else:
                    response["structured_reasoning"] = hydrate_schema(schema, message)

        # Extract prior beliefs from conversation history
        self._extract_prior_beliefs(message)

        # Track recent queries for context-dependent adaptation
        self._track_recent_query(message)

        # Get expected length from adaptive strategy if available
        # CRITICAL: Classify query type EARLY so we can use it for experience injection BEFORE research
        expected_length = None
        query_type = None
        if self.adaptive_manager and self.quality_feedback:
            current_session = None
            if self.quality_feedback.session_manager:
                current_session = self.quality_feedback.session_manager.get_current_session()
            strategy = self.adaptive_manager.get_adaptive_strategy(message, current_session=current_session)
            expected_length = strategy.expected_length
            query_type = self.adaptive_manager._classify_query(message)
        elif self.adaptive_manager:
            # Fallback: classify query even without quality_feedback
            query_type = self.adaptive_manager._classify_query(message)

        # META: Inject experience context BEFORE research (so it can help with tool selection)
        experience_context = ""
        if self.meta_learner and query_type:
            try:
                experience_context = self.meta_learner.get_context_experience(
                    query=message,
                    query_type=query_type,
                    max_experiences=5,
                )
                if experience_context:
                    logger.debug(f"Injecting {len(experience_context)} chars of experience context")
            except Exception as e:
                logger.warning(f"Failed to get experience context: {e}", exc_info=True)

        # Context-dependent adaptation: adjust based on recent queries
        if self.recent_queries:
            # If user is asking similar questions, they might want exploration mode
            # If questions are very different, they want extraction mode
            recent_topics = [q.get("topic", "") for q in self.recent_queries[-3:]]
            topic_similarity = self._compute_topic_similarity(message, recent_topics)

            if topic_similarity > 0.5:
                # Exploration mode: user is diving deeper
                # Increase detail level
                if expected_length:
                    expected_length = int(expected_length * 1.2)
            else:
                # Extraction mode: user wants quick answers
                # Decrease detail level
                if expected_length:
                    expected_length = int(expected_length * 0.8)

        # Conduct research if requested
        # META: Include experience context in research query if available (helps with tool selection)
        research_query = message
        if experience_context and use_research:
            # Prepend experience context to help with query decomposition and tool selection
            research_query = experience_context + "\n\nUser Query: " + message

        if use_research:
            try:
                # Use structured orchestration if schema is provided
                if use_schema and schema:
                    research_result = await self.orchestrator.research_with_schema(
                        research_query,  # Use query with experience context
                        schema_name=use_schema,
                        prior_beliefs=self.prior_beliefs,  # Pass prior beliefs for alignment
                        adaptive_manager=self.adaptive_manager,  # NEW: Pass adaptive manager for early stopping
                    )
                else:
                    research_result = await self.research_agent.deep_research(research_query)
                response["research_conducted"] = True
                response["research"] = research_result
            except Exception as e:
                # If research fails, continue without it (graceful degradation)
                logger.warning(f"Research failed for query '{message[:50]}...': {e}")
                response["research_conducted"] = False
                response["research_error"] = str(e)


        # Generate response using LLM
        # This creates the actual response text that users read
        # It's based on message + context (which includes research.final_synthesis if available)
        #
        # CONTEXT INJECTION ORDER (highest to lowest priority):
        # 1. System reminders (keep agent on track - highest priority)
        # 2. Skills context (domain guidance)
        # 3. Experience context (learned patterns)
        # 4. User message (base query)
        #
        # This ordering ensures system instructions are most prominent, followed by
        # domain guidance, then learned patterns, then the actual query.
        message_with_context = message

        # Add experience context (learned patterns) - lowest priority context
        if experience_context and not use_research:
            # Only inject if research wasn't used (research already got it)
            # If research was used, experience context was already in research_query
            message_with_context = experience_context + "\n\n" + message_with_context

        # Add skills context (domain guidance) - medium priority
        if skills_context:
            message_with_context = skills_context + "\n\n" + message_with_context

        # System reminders (keep agent on track) - highest priority, prepended last
        # so they appear first in the final prompt
        if system_reminders:
            reminders_text = "\n\n".join([
                f"<system-reminder>\n{r}\n</system-reminder>"
                for r in system_reminders
            ])
            message_with_context = reminders_text + "\n\n" + message_with_context

        response["response"] = await self._generate_response(
            message_with_context,
            response,  # This context dict includes research results if available
            schema,
            expected_length=expected_length
        )

        # Store original response text BEFORE source references are added
        # This is needed for validation to check if sources match response
        original_response_text = response["response"]

        # Build provenance map for token-level matching
        provenance_data = {}
        if use_research and response.get("research"):
            try:
                provenance_data = build_provenance_map(
                    original_response_text,
                    response["research"],
                )
                # Store provenance in research metadata
                if "research" in response and isinstance(response["research"], dict):
                    response["research"]["provenance"] = provenance_data

                    # Generate query refinement suggestions
                    try:
                        query_refinement = refine_query_from_provenance(
                            message,
                            provenance_data,
                        )
                        if query_refinement:
                            response["query_refinement_suggestions"] = query_refinement
                    except Exception as e:
                        logger.debug(f"Failed to generate query refinement suggestions: {e}", exc_info=True)
            except Exception as e:
                logger.warning(f"Failed to build provenance map: {e}", exc_info=True)

        # Add source references to response text
        # FIXED: Now matches sources to actual response text, not synthesis
        response["response"] = self._add_source_references(
            response["response"],
            response.get("research", {})
        )

        # Create progressive disclosure tiers
        response["response_tiers"] = self._create_response_tiers(
            response["response"],
            response.get("research", {}),
            message
        )

        # Add belief alignment information if prior beliefs exist
        if self.prior_beliefs and response.get("research"):
            research_data = response.get("research", {})
            if isinstance(research_data, dict):
                # Check for belief alignment in topology nodes
                topology = research_data.get("topology", {})
                if topology:
                    # Compute average belief alignment from nodes
                    # This would require accessing the topology object directly
                    # For now, add prior beliefs info
                    response["prior_beliefs"] = [
                        {
                            "text": b["text"],
                            "source": b["source"],
                        }
                        for b in self.prior_beliefs[-3:]  # Last 3 beliefs
                    ]

        # Evaluate and learn from response (quality feedback loop)
        # This runs BEFORE validation, so validation issues aren't available yet
        # But we'll add them to response metadata after validation
        if self.quality_feedback:
            # Extract expected concepts from query and knowledge base
            expected_concepts = self._extract_expected_concepts(message)
            context = self._get_relevant_context(message)

            quality_result = self.quality_feedback.evaluate_and_learn(
                query=message,
                response=response["response"],
                schema=use_schema,
                research=use_research,
                expected_concepts=expected_concepts,
                context=context,
            )

            # Update adaptive manager
            if self.adaptive_manager:
                tools_used = []
                if use_research and response.get("research"):
                    research_data = response.get("research", {})
                    if isinstance(research_data, dict):
                        tools_called = research_data.get("tools_called", [])
                        # Handle both int (count) and list (tool names) formats
                        if isinstance(tools_called, int):
                            # Extract tool names from subsolutions
                            for subsolution in research_data.get("subsolutions", []):
                                tools_used.extend(subsolution.get("tools_used", []))
                        elif isinstance(tools_called, list):
                            tools_used = tools_called

                self.adaptive_manager.update_from_evaluation(
                    query=message,
                    schema=use_schema,
                    used_research=use_research,
                    response_length=len(response["response"]),
                    quality_score=quality_result["relevance"],
                    tools_used=tools_used,
                )

                # Get current session for context-aware strategy
                current_session = None
                if self.quality_feedback and self.quality_feedback.session_manager:
                    current_session = self.quality_feedback.session_manager.get_current_session()

                # Get adaptive suggestions
                adaptive_suggestions = self.adaptive_manager.get_improvement_suggestions(
                    message,
                    quality_result["relevance"],
                )
                # Merge with quality suggestions
                quality_result["suggestions"].extend(adaptive_suggestions)

            # META: Reflect on task completion and store insights
            if self.meta_learner:
                try:
                    tools_used_for_reflection = []
                    # Track skills usage if enabled
                    if self.enable_skills and self.skills_manager and skills_context:
                        # Extract skill names from skills_context
                        relevant_skills = self.skills_manager.find_relevant_skills(message, limit=5)
                        for skill in relevant_skills:
                            tools_used_for_reflection.append(f"skill:{skill.name}")

                    if use_research and response.get("research"):
                        research_data = response.get("research", {})
                        if isinstance(research_data, dict):
                            for subsolution in research_data.get("subsolutions", []):
                                tools_used_for_reflection.extend(subsolution.get("tools_used", []))

                    # Ensure query_type is set (fallback to "general" if classification failed)
                    reflection_query_type = query_type or "general"

                    reflection_text = await self.meta_learner.reflect_on_completion(
                        query=message,
                        response=response["response"],
                        query_type=reflection_query_type,
                        tools_used=tools_used_for_reflection,
                        quality_score=quality_result.get("relevance"),
                        llm_service=self.llm_service,
                        reflection_type="self",  # Could be "verified" if ground truth available
                    )

                    if reflection_text:
                        response["meta_reflection"] = reflection_text[:500]  # Store truncated version
                        response["meta_reflection_query_type"] = reflection_query_type
                except Exception as e:
                    # Reflection failure shouldn't break the response
                    logger.warning(f"Meta-reflection failed: {e}", exc_info=True)

            # Auto-retry with better schema if quality is low
            if quality_result["relevance"] < 0.5:
                # Try adaptive strategy first
                best_schema = None
                if self.adaptive_manager:
                    # Get current session for context
                    current_session = None
                    if self.quality_feedback and self.quality_feedback.session_manager:
                        current_session = self.quality_feedback.session_manager.get_current_session()

                    strategy = self.adaptive_manager.get_adaptive_strategy(
                        message,
                        current_session=current_session,
                    )
                    if strategy.confidence > 0.6:
                        best_schema = strategy.schema_selection

                # Fall back to quality feedback recommendation
                if not best_schema:
                    best_schema = self.quality_feedback.get_best_schema_for_query(message)

                if best_schema and best_schema != use_schema:
                    # Retry with better schema
                    try:
                        schema_obj = get_schema(best_schema)
                        if schema_obj:
                            if self.llm_service:
                                structured_reasoning = await self.llm_service.hydrate_schema(schema_obj, message)
                            else:
                                structured_reasoning = hydrate_schema(schema_obj, message)
                            if structured_reasoning:
                                response["response"] = structured_reasoning.get("final_result", response["response"])
                                response["schema_used"] = best_schema
                                # Re-evaluate with new response
                                quality_result = self.quality_feedback.evaluate_and_learn(
                                    query=message,
                                    response=response["response"],
                                    schema=best_schema,
                                    research=use_research,
                                    expected_concepts=expected_concepts,
                                    context=context,
                                )
                    except Exception:
                        pass  # Fall back to original response

            # Add quality information to response
            response["quality"] = {
                "score": quality_result["relevance"],
                "flags": quality_result["quality_flags"],
                "suggestions": quality_result["suggestions"],
            }

            # Add adaptive insights if available
            if self.adaptive_manager:
                # Get current session for context
                current_session = None
                if self.quality_feedback and self.quality_feedback.session_manager:
                    current_session = self.quality_feedback.session_manager.get_current_session()

                strategy = self.adaptive_manager.get_adaptive_strategy(
                    message,
                    current_session=current_session,
                )
                response["quality"]["adaptive_strategy"] = {
                    "schema": strategy.schema_selection,
                    "expected_length": strategy.expected_length,
                    "should_use_research": strategy.should_use_research,
                    "confidence": strategy.confidence,
                }

        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": response["response"]})

        # Manage conversation history length (prevent unbounded growth)
        # Based on Claude Code compaction pattern: trigger at 70% capacity (not 100%)
        # Research shows compaction at 70% prevents performance degradation
        # Use token-based threshold if available for accuracy, otherwise message count

        should_compact = False
        if self._tokenizer is not None:
            # Token-based compaction (more accurate)
            estimated_tokens = self._get_conversation_token_count()
            token_threshold = int(os.getenv("BOP_TOKEN_THRESHOLD", "140000"))  # 70% of 200K default
            if estimated_tokens > token_threshold:
                logger.debug(f"Token-based compaction trigger: {estimated_tokens} tokens > {token_threshold}")
                should_compact = True
        else:
            # Message count-based compaction (fallback)
            compaction_threshold = int(self.max_conversation_history * 0.7)
            if len(self.conversation_history) > compaction_threshold:
                should_compact = True

        if should_compact:
            try:
                await self._compact_conversation_history()
            except Exception as e:
                # Compaction failure is non-fatal - log and continue
                # History is preserved by _compact_conversation_history's rollback
                logger.error(f"Compaction attempt failed: {e}", exc_info=True)

        # Save knowledge tracker state on agent cleanup (if persistence enabled)
        # Note: This is best-effort - proper cleanup would need __del__ or context manager

        # Add temporal information (timestamp tracking)
        current_timestamp = datetime.now(timezone.utc).isoformat()
        response["timestamp"] = current_timestamp

        # Extract source timestamps from research results if available
        if response.get("research") and isinstance(response["research"], dict):
            source_timestamps = {}
            subsolutions = response["research"].get("subsolutions", [])
            for subsolution in subsolutions:
                if isinstance(subsolution, dict):
                    results = subsolution.get("results", [])
                    for result in results:
                        source = result.get("tool", "unknown")
                        if "timestamp" in result:
                            source_timestamps[source] = result["timestamp"]
                        elif "accessed_at" in result:
                            source_timestamps[source] = result["accessed_at"]

            if source_timestamps:
                response["source_timestamps"] = source_timestamps

            # Build temporal evolution from source matrix if available
            source_matrix = response["research"].get("source_matrix")
            if source_matrix:
                temporal_evolution = []
                for claim, data in list(source_matrix.items())[:5]:
                    sources = data.get("sources", {})
                    if sources:
                        temporal_evolution.append({
                            "claim": claim[:60] + ("..." if len(claim) > 60 else ""),
                            "full_claim": claim,
                            "source_count": len(sources),
                            "consensus": data.get("consensus"),
                            "conflict": data.get("conflict", False),
                        })
                if temporal_evolution:
                    response["temporal_evolution"] = temporal_evolution

        # Track knowledge learned across sessions
        if self.quality_feedback and self.quality_feedback.session_manager:
            current_session = self.quality_feedback.session_manager.get_current_session()
            if current_session:
                session_id = current_session.session_id
                confidence = response.get("quality", {}).get("score") if response.get("quality") else None
                context = message[:100]  # Use query as context

                # Track concepts learned from this query-response pair
                self.knowledge_tracker.track_query(
                    session_id=session_id,
                    query=message,
                    response=response.get("response", ""),
                    timestamp=current_timestamp,
                    confidence=confidence,
                )

                # Add session-level temporal evolution to response
                session_evolution = self.knowledge_tracker.get_session_evolution(session_id)
                if session_evolution:
                    response["session_knowledge"] = session_evolution

                # Add cross-session concept evolution
                cross_session_evolution = self.knowledge_tracker.get_cross_session_evolution(limit=5)
                if cross_session_evolution:
                    response["cross_session_evolution"] = cross_session_evolution

                # Add concepts learned in this session
                concepts_in_session = self.knowledge_tracker.get_concepts_by_session(session_id)
                if concepts_in_session.get("concepts"):
                    response["session_concepts"] = concepts_in_session

        # Validate response for bugs and inconsistencies (introspection)
        # This runs automatically and integrates with quality feedback
        # Ground-level validation: checks actual code behavior vs intended behavior
        try:
            from .validation import IntrospectionLogger, validate_response

            # Store original response text for validation (before source references)
            # Validation needs to check if sources match the actual response, not synthesis
            validation_response = response.copy()
            validation_response["response"] = original_response_text  # Use original, not with source refs

            validation_issues = validate_response(validation_response, message, self)
            if validation_issues:
                IntrospectionLogger.log_validation_issues(validation_issues, context=f"chat: {message[:50]}")
                IntrospectionLogger.log_response_metadata(response, validation_issues)

                # Integrate with quality feedback: add validation issues as quality flags
                if self.quality_feedback and response.get("quality"):
                    quality_flags = IntrospectionLogger.convert_to_quality_flags(validation_issues)
                    if quality_flags:
                        # Add validation flags to quality assessment
                        if "quality_flags" not in response["quality"]:
                            response["quality"]["quality_flags"] = []
                        response["quality"]["quality_flags"].extend(quality_flags)

                # Re-evaluate quality with validation issues if quality feedback is enabled
                # This allows quality scores to reflect validation issues
                if self.quality_feedback and validation_issues:
                    # Update quality result with validation-aware assessment
                    # The semantic evaluator will pick up validation issues from metadata
                    pass  # Already handled via metadata
        except Exception as e:
            # Don't fail on validation errors, just log
            logger.debug(f"Response validation failed: {e}", exc_info=True)

        return response

    def _extract_expected_concepts(self, query: str) -> List[str]:
        """Extract expected concepts from query and knowledge base."""
        concepts = []
        query_lower = query.lower()

        # Extract from query
        concept_keywords = {
            "trust": ["trust", "credibility", "confidence"],
            "uncertainty": ["uncertainty", "epistemic", "aleatoric"],
            "knowledge": ["knowledge", "information", "understanding"],
            "structure": ["structure", "organization", "architecture"],
            "reasoning": ["reasoning", "inference", "logic"],
        }

        for concept, keywords in concept_keywords.items():
            if any(kw in query_lower for kw in keywords):
                concepts.append(concept)

        # Extract from knowledge base
        for doc_content in self.knowledge_base.values():
            content_lower = doc_content.lower()
            for concept, keywords in concept_keywords.items():
                if concept not in concepts and any(kw in content_lower for kw in keywords):
                    if any(kw in query_lower for kw in ["about", "discuss", "explain", "what", "how"]):
                        concepts.append(concept)

        return concepts[:5]  # Limit to top 5

    def _get_relevant_context(self, query: str) -> Optional[str]:
        """Get relevant context from knowledge base for query."""
        if not self.knowledge_base:
            return None

        query_lower = query.lower()
        relevant_docs = []

        for doc_name, doc_content in self.knowledge_base.items():
            # Simple relevance: check if query words appear in content
            query_words = set(query_lower.split())
            content_words = set(doc_content.lower().split())
            overlap = len(query_words & content_words)

            if overlap > 0:
                relevant_docs.append((overlap, doc_content[:2000]))  # First 2000 chars

        if relevant_docs:
            # Return most relevant
            relevant_docs.sort(reverse=True)
            return relevant_docs[0][1]

        return None

    async def _generate_response(
        self,
        message: str,
        context: Dict[str, Any],
        schema: Optional[Any] = None,
        expected_length: Optional[int] = None,
    ) -> str:
        """
        Generate response based on message and context.

        Args:
            message: User message (may already include system reminders, skills, experience context)
            context: Context dictionary
            schema: Optional reasoning schema
            expected_length: Optional target response length (for adaptation)

        Note: System reminders, skills, and experience context are injected in chat()
        before calling this method, following BOP's context injection priority order.
        """
        if self.llm_service:
            try:
                # Pass target_length to LLM service for better control
                # Note: message already contains system reminders, skills, experience context
                # in the correct priority order (injected in chat() method)
                response_text = await self.llm_service.generate_response(
                    message,
                    context,
                    schema,
                    target_length=expected_length
                )

                # Post-process if still too long (fallback)
                if expected_length and expected_length > 0:
                    current_length = len(response_text)
                    if current_length > expected_length * 1.5:
                        # Response is too long - truncate intelligently
                        target_length = int(expected_length * 1.2)  # Allow 20% over
                        if current_length > target_length:
                            # Find last sentence before target length
                            truncated = response_text[:target_length]
                            last_period = truncated.rfind('.')
                            if last_period > target_length * 0.7:  # If we found a period reasonably close
                                response_text = response_text[:last_period + 1]
                            else:
                                response_text = truncated + "..."

                return response_text
            except Exception as e:
                return f"[LLM Error] {str(e)}\n\nFallback response: I received your message: {message}"
        else:
            # Fallback if LLM service not available
            return f"Response to: {message}\n[LLM service not available - please set OPENAI_API_KEY]"

    def search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """
        Search the knowledge base using HOP's retrieval layer if available,
        otherwise fallback to simple keyword matching.

        Args:
            query: Search query

        Returns:
            List of matching content snippets
        """
        # Use HOP's retrieval layer if available
        if self.hop_retriever:
            try:
                # Use hop's text search
                hop_results = self.hop_retriever.search(query, limit=10)

                # Convert hop results to BOP format
                results = []
                for doc in hop_results:
                    # Extract content from hop document structure
                    doc_id = doc.get("id", "unknown")
                    content_dict = doc.get("content", {})

                    # Handle different content formats
                    if isinstance(content_dict, dict):
                        # Chat format: extract messages
                        messages = content_dict.get("messages", [])
                        if messages:
                            content_text = "\n".join([
                                f"{msg.get('author', 'Unknown')}: {msg.get('content', '')}"
                                for msg in messages[:5]  # First 5 messages
                            ])
                        else:
                            content_text = str(content_dict)
                    else:
                        content_text = str(content_dict)

                    results.append({
                        "document": doc_id,
                        "content": content_text[:500],  # First 500 chars
                        "source": "hop_retrieval",
                        "metadata": doc.get("metadata", {}),
                    })

                if results:
                    logger.debug(f"HOP retrieval found {len(results)} documents")
                    return results
            except Exception as e:
                logger.warning(f"HOP retrieval failed: {e}, falling back to simple search")
                import traceback
                logger.debug(traceback.format_exc())

        # Fallback: simple keyword matching in local knowledge base
        results = []
        query_lower = query.lower()

        for doc_name, content in self.knowledge_base.items():
            if query_lower in content.lower():
                # Simple keyword matching - could be improved
                results.append({
                    "document": doc_name,
                    "matches": content.count(query_lower),
                    "source": "local_knowledge_base",
                })

        return results

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.conversation_history

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        self.prior_beliefs = []
        self.recent_queries = []

    def _extract_prior_beliefs(self, message: str) -> None:
        """
        Extract prior beliefs from user message.

        Looks for statements like "I think", "I believe", "I know", etc.
        Gracefully handles errors and returns empty list on failure.
        """
        try:
            if not message or not isinstance(message, str):
                return

            message_lower = message.lower()
            belief_indicators = [
                "i think", "i believe", "i know", "i'm convinced",
                "i assume", "i understand", "my understanding is",
                "from what i know", "as far as i know"
            ]

            for indicator in belief_indicators:
                if indicator in message_lower:
                    # Extract the belief statement
                    idx = message_lower.find(indicator)
                    # Try to extract a sentence or phrase after the indicator
                    rest = message[idx + len(indicator):].strip()
                    if rest:
                        # Take first sentence or first 100 chars
                        sentence_end = rest.find('.')
                        if sentence_end > 0:
                            belief_text = rest[:sentence_end].strip()
                        else:
                            belief_text = rest[:100].strip()

                        if belief_text and len(belief_text) > 10:  # Minimum length
                            self.prior_beliefs.append({
                                "text": belief_text,
                                "source": "user_statement",
                                "timestamp": len(self.conversation_history),
                            })
                            # Limit to last 20 beliefs (improved from 10 for better alignment)
                            if len(self.prior_beliefs) > 20:
                                self.prior_beliefs = self.prior_beliefs[-20:]
                            break  # Only extract one belief per message
        except Exception as e:
            logger.warning(f"Failed to extract prior beliefs: {e}", exc_info=True)
            # Graceful degradation: continue without belief extraction
            return

    def _track_recent_query(self, message: str) -> None:
        """
        Track recent queries for context-dependent adaptation.

        Stores query with extracted topic/keywords for similarity matching.
        """
        # Extract key terms from message (simple approach)
        words = message.lower().split()
        # Remove common stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "must", "can", "what", "how", "why", "when",
                     "where", "which", "who", "this", "that", "these", "those"}
        key_terms = [w for w in words if w not in stop_words and len(w) > 3]

        # Extract topic (first few key terms or first sentence)
        topic = " ".join(key_terms[:5]) if key_terms else message[:50]

        self.recent_queries.append({
            "message": message,
            "topic": topic,
            "key_terms": key_terms[:10],
            "timestamp": len(self.conversation_history),
        })

        # Keep last 20 queries with recency weighting (improved from 10)
        # Based on research: more history needed for accurate topic similarity
        if len(self.recent_queries) > 20:
            self.recent_queries = self.recent_queries[-20:]

    def _compute_topic_similarity(self, current_message: str, recent_topics: List[str]) -> float:
        """
        Compute similarity between current message and recent topics.

        Uses recency weighting: more recent topics contribute more to similarity.
        Based on research finding that recency matters for context adaptation.

        Returns:
            0.0 to 1.0 similarity score (weighted average)
        """
        if not recent_topics:
            return 0.0

        current_lower = current_message.lower()
        current_words = set(current_lower.split())

        # Remove stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "must", "can", "what", "how", "why", "when",
                     "where", "which", "who", "this", "that", "these", "those"}
        current_words = current_words - stop_words

        similarities = []
        weights = []

        # Compute similarity with recency weighting
        # More recent topics (higher index) get higher weight
        for idx, topic in enumerate(recent_topics):
            topic_words = set(topic.lower().split())
            topic_words = topic_words - stop_words

            if not current_words or not topic_words:
                continue

            # Jaccard similarity
            intersection = len(current_words & topic_words)
            union = len(current_words | topic_words)
            if union > 0:
                similarity = intersection / union
                similarities.append(similarity)
                # Recency weight: linear decay from 1.0 (most recent) to 0.5 (oldest)
                # idx 0 = oldest, idx -1 = most recent
                recency_weight = 0.5 + 0.5 * (idx + 1) / len(recent_topics)
                weights.append(recency_weight)

        if not similarities:
            return 0.0

        # Weighted average (more recent = higher weight)
        weighted_sum = sum(s * w for s, w in zip(similarities, weights))
        total_weight = sum(weights)

        return float(weighted_sum / total_weight) if total_weight > 0 else 0.0

    def _generate_system_reminders(self, message: str) -> List[str]:
        """
        Generate system reminders to keep agent on track during long sessions.

        Based on Claude Code patterns:
        - Remind about TODO list state
        - Reinforce key instructions
        - Keep agent focused on task

        Args:
            message: Current user message

        Returns:
            List of reminder strings (will be wrapped in <system-reminder> tags)
        """
        reminders = []

        # Core instruction reminder (always included)
        reminders.append(
            "Do what has been asked; nothing more, nothing less.\n"
            "NEVER create files unless they're absolutely necessary for achieving your goal.\n"
            "ALWAYS prefer editing an existing file to creating a new one.\n"
            "NEVER proactively create documentation files (*.md) or README files. "
            "Only create documentation files if explicitly requested by the User.\n"
            "IMPORTANT: this context may or may not be relevant to your tasks. "
            "You should not respond to this context or otherwise consider it in your response "
            "unless it is highly relevant. Most of the time, it is not relevant."
        )

        # TODO list state reminders
        if not self.todo_list:
            # Empty TODO list - suggest creating one for multi-step tasks
            # Only suggest if message seems like a multi-step task
            multi_step_indicators = [
                "build", "create", "implement", "develop", "design", "analyze",
                "research", "write", "generate", "refactor", "fix", "add"
            ]
            message_lower = message.lower()
            if any(indicator in message_lower for indicator in multi_step_indicators):
                reminders.append(
                    "This is a reminder that your todo list is currently empty. "
                    "DO NOT mention this to the user explicitly because they are already aware. "
                    "If you are working on tasks that would benefit from a todo list "
                    "please use the TodoWrite tool to create one. If not, please feel free to ignore. "
                    "Again do not mention this message to the user."
                )
        else:
            # TODO list exists - show current state
            completed = sum(1 for item in self.todo_list if item.get("status") == "completed")
            total = len(self.todo_list)
            in_progress = [item for item in self.todo_list if item.get("status") == "in_progress"]
            pending = [item for item in self.todo_list if item.get("status") == "pending"]

            # Format TODO list more readably (based on Claude Code pattern)
            todo_items = []
            for item in self.todo_list:
                status_icon = "✓" if item.get("status") == "completed" else "→" if item.get("status") == "in_progress" else "○"
                priority = item.get("priority", "medium")
                todo_items.append(
                    f"{status_icon} [{item.get('id', '?')}] {item.get('content', '')} "
                    f"(status: {item.get('status', 'pending')}, priority: {priority})"
                )

            todo_summary = (
                "Your todo list has changed. DO NOT mention this explicitly to the user. "
                "Here are the latest contents of your todo list:\n"
                + "\n".join(todo_items)
                + f"\n\nProgress: {completed}/{total} completed. "
                "Continue on with the tasks at hand if applicable. "
                "Keep using the TODO list to track your work and follow the next task on the list."
            )

            reminders.append(todo_summary)

            # If there's an in-progress task, remind to focus on it
            if in_progress:
                current_task = in_progress[0]
                reminders.append(
                    f"Current task in progress: {current_task.get('content', 'Unknown')}. "
                    f"Focus on completing this task before moving to the next one. "
                    f"Update the TODO list when you complete this task."
                )
            elif pending:
                # If no task in progress but there are pending tasks, suggest starting one
                next_task = pending[0]
                reminders.append(
                    f"Next task to work on: {next_task.get('content', 'Unknown')}. "
                    f"Consider starting this task and updating the TODO list status to 'in_progress'."
                )

        # Conversation length reminder (for very long sessions)
        if len(self.conversation_history) > 20:
            reminders.append(
                "This conversation has been going on for a while. "
                "Make sure you're staying focused on the user's original request and "
                "not getting sidetracked by intermediate steps."
            )

        # Record metrics for observability
        if self._metrics is not None:
            self._metrics["reminder_generations"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reminder_count": len(reminders),
                "has_todo": len(self.todo_list) > 0,
                "conversation_length": len(self.conversation_history),
            })

        return reminders

    def update_todo_list(self, todos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update the TODO list (used by tools or agent itself).

        Based on Claude Code pattern: complete list is provided on each update,
        not incremental changes. Returns result with embedded instructions.

        Args:
            todos: Complete TODO list with items containing:
                - id: Unique identifier (string)
                - content: Task description (string)
                - status: "pending", "in_progress", or "completed"
                - priority: "low", "medium", or "high" (optional)

        Returns:
            Dictionary with updated TODO list and embedded instructions
            (following Claude Code pattern of instructions in tool results)
        """
        # Validate TODO items
        validated_todos = []
        for item in todos:
            if not isinstance(item, dict):
                continue
            if "id" not in item or "content" not in item:
                continue
            if "status" not in item:
                item["status"] = "pending"
            if item["status"] not in ["pending", "in_progress", "completed"]:
                item["status"] = "pending"
            validated_todos.append(item)

        self.todo_list = validated_todos
        logger.debug(f"Updated TODO list: {len(self.todo_list)} items")

        # Persist TODO list to scratchpad file if enabled (Manus pattern)
        if self.enable_scratchpad:
            self._save_todo_to_scratchpad()

        # Record metrics for observability
        if self._metrics is not None:
            completed = sum(1 for item in self.todo_list if item.get("status") == "completed")
            self._metrics["todo_updates"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "todo_count": len(self.todo_list),
                "completed": completed,
            })
            # Auto-save metrics periodically
            if len(self._metrics["todo_updates"]) % 10 == 0:
                self._save_metrics()

            # Automated health check and optimization
            optimization_result = self._check_health_and_auto_optimize()
            if optimization_result:
                logger.info(f"Auto-optimization performed: {optimization_result}")

        # Return result with embedded instructions (Claude Code pattern)
        # This ensures instructions are reinforced every time TODO list is updated
        completed = sum(1 for item in self.todo_list if item.get("status") == "completed")
        total = len(self.todo_list)
        in_progress = [item for item in self.todo_list if item.get("status") == "in_progress"]
        pending = [item for item in self.todo_list if item.get("status") == "pending"]

        instructions = (
            f"TODO list updated successfully. Progress: {completed}/{total} completed.\n"
            f"Keep using the TODO list to track your work and follow the next task on the list.\n"
        )

        if in_progress:
            instructions += f"Current task in progress: {in_progress[0].get('content', 'Unknown')}. Focus on completing it.\n"
        elif pending:
            instructions += f"Next task: {pending[0].get('content', 'Unknown')}. Consider starting it.\n"

        instructions += "Update the TODO list status as you complete tasks."

        # Track instruction effectiveness (for feedback loop)
        instruction_version = "v1"  # Can be A/B tested
        if self._metrics is not None:
            # Track which instruction format is used
            try:
                # Calculate completion rate safely (handle division by zero)
                completion_rate = completed / total if total > 0 else 0.0

                # Ensure completion_rate is in valid range
                if not isinstance(completion_rate, (int, float)):
                    completion_rate = 0.0
                elif completion_rate < 0.0:
                    completion_rate = 0.0
                elif completion_rate > 1.0:
                    completion_rate = 1.0

                self._metrics.setdefault("instruction_usage", []).append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "version": instruction_version,
                    "context": {
                        "has_in_progress": len(in_progress) > 0,
                        "has_pending": len(pending) > 0,
                        "completion_rate": completion_rate,
                        "total_todos": total,
                        "completed_todos": completed,
                    }
                })

                # Limit instruction_usage size to prevent unbounded growth
                if len(self._metrics["instruction_usage"]) > 1000:
                    self._metrics["instruction_usage"] = self._metrics["instruction_usage"][-1000:]
            except Exception as e:
                logger.debug(f"Failed to track instruction usage: {e}")

        return {
            "todos": [item.copy() for item in self.todo_list],
            "progress": {"completed": completed, "total": total},
            "instructions": instructions,
            "instruction_version": instruction_version,  # For A/B testing
        }

    def get_todo_list(self) -> List[Dict[str, Any]]:
        """
        Get current TODO list.

        Returns:
            Copy of current TODO list
        """
        return [item.copy() for item in self.todo_list]

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get observability metrics for self-reflection and improvement.

        Returns:
            Dictionary with metrics summary, or None if observability disabled
        """
        if self._metrics is None:
            return None

        # Calculate summary statistics
        summary = {
            "compaction": {
                "total_events": len(self._metrics["compaction_events"]),
                "successful": sum(1 for e in self._metrics["compaction_events"] if e.get("success")),
                "failed": sum(1 for e in self._metrics["compaction_events"] if not e.get("success")),
            },
            "todo_updates": {
                "total": len(self._metrics["todo_updates"]),
            },
            "reminders": {
                "total_generations": len(self._metrics["reminder_generations"]),
            },
            "errors": {
                "total": len(self._metrics["errors"]),
                "by_type": {},
            },
        }

        # Calculate average compression ratio
        successful_compactions = [e for e in self._metrics["compaction_events"] if e.get("success")]
        if successful_compactions:
            summary["compaction"]["avg_compression_ratio"] = sum(
                e.get("compression_ratio", 0) for e in successful_compactions
            ) / len(successful_compactions)

        # Count errors by type
        for error in self._metrics["errors"]:
            error_type = error.get("type", "unknown")
            summary["errors"]["by_type"][error_type] = summary["errors"]["by_type"].get(error_type, 0) + 1

        return {
            "summary": summary,
            "detailed": self._metrics.copy(),  # Full metrics for deep analysis
        }

    def self_reflect(self) -> Dict[str, Any]:
        """
        Self-reflection: analyze own behavior and suggest improvements.

        Returns:
            Dictionary with self-analysis and improvement suggestions
        """
        metrics = self.get_metrics()
        if metrics is None:
            return {"status": "observability_disabled"}

        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "observations": [],
            "suggestions": [],
            "health_score": 1.0,
        }

        summary = metrics["summary"]

        # Analyze compaction behavior
        if summary["compaction"]["total_events"] > 0:
            success_rate = summary["compaction"]["successful"] / summary["compaction"]["total_events"]
            analysis["observations"].append(
                f"Compaction success rate: {success_rate:.1%} "
                f"({summary['compaction']['successful']}/{summary['compaction']['total_events']})"
            )

            if success_rate < 0.9:
                analysis["suggestions"].append(
                    "Compaction failure rate is high. Consider reviewing error logs or "
                    "switching to heuristic-based compaction if LLM compaction is failing."
                )
                analysis["health_score"] *= 0.8

            if summary["compaction"].get("avg_compression_ratio", 0) > 0:
                compression = summary["compaction"]["avg_compression_ratio"]
                analysis["observations"].append(
                    f"Average compression ratio: {compression:.1%} "
                    f"(lower is better - {compression:.1%} means {compression:.1%} of original size)"
                )

        # Analyze error patterns
        if summary["errors"]["total"] > 0:
            analysis["observations"].append(
                f"Total errors observed: {summary['errors']['total']}"
            )

            # Check for error patterns
            error_types = summary["errors"]["by_type"]
            if "compaction_failure" in error_types and error_types["compaction_failure"] > 2:
                analysis["suggestions"].append(
                    "Multiple compaction failures detected. Consider increasing "
                    "BOP_MAX_CONVERSATION_HISTORY or investigating root cause."
                )
                analysis["health_score"] *= 0.7

        # Analyze TODO list usage
        if summary["todo_updates"]["total"] > 0:
            analysis["observations"].append(
                f"TODO list updated {summary['todo_updates']['total']} times"
            )

        # Analyze reminder generation
        if summary["reminders"]["total_generations"] > 0:
            analysis["observations"].append(
                f"System reminders generated {summary['reminders']['total_generations']} times"
            )

        # Overall health assessment
        if analysis["health_score"] < 0.7:
            analysis["suggestions"].append(
                "System health score is below optimal. Review error logs and consider adjustments."
            )

        analysis["health_score"] = max(0.0, min(1.0, analysis["health_score"]))

        return analysis

    def _check_health_and_auto_optimize(self) -> Optional[Dict[str, Any]]:
        """
        Automated health check and self-optimization.

        Periodically checks system health and automatically adjusts settings
        if health score drops below threshold.

        Returns:
            Dictionary with optimization actions taken, or None if no action needed
        """
        if not self.enable_observability or self._metrics is None:
            return None

        # Only check periodically (every 20 operations to avoid overhead)
        # Handle edge case: empty metrics
        compaction_count = len(self._metrics.get("compaction_events", []))
        todo_count = len(self._metrics.get("todo_updates", []))
        reminder_count = len(self._metrics.get("reminder_generations", []))

        total_ops = compaction_count + todo_count + reminder_count

        # Skip if no operations yet (need at least some data)
        if total_ops == 0:
            return None

        # Only check periodically (every 20 operations)
        if total_ops % 20 != 0:
            return None

        # Perform self-reflection
        try:
            analysis = self.self_reflect()
            health_score = analysis.get("health_score", 1.0)

            # Validate health score is in valid range
            if not isinstance(health_score, (int, float)):
                logger.warning(f"Invalid health score type: {type(health_score)}, defaulting to 1.0")
                health_score = 1.0
            elif health_score < 0.0 or health_score > 1.0:
                logger.warning(f"Health score out of range: {health_score}, clamping to [0.0, 1.0]")
                health_score = max(0.0, min(1.0, health_score))
        except Exception as e:
            logger.error(f"Self-reflection failed during health check: {e}", exc_info=True)
            return None

        actions_taken = []

        # Auto-optimize if health score is low
        if health_score < 0.7:
            # Action 1: If compaction failures are high, suggest switching to heuristic
            if self.use_llm_compaction:
                compaction_events = self._metrics.get("compaction_events", [])
                if compaction_events:
                    # Get last 10 events (or all if fewer than 10)
                    recent_events = compaction_events[-10:] if len(compaction_events) >= 10 else compaction_events
                    recent_failures = [
                        e for e in recent_events
                        if isinstance(e, dict) and not e.get("success", True)
                    ]
                    if len(recent_failures) >= 3:
                        failure_rate = len(recent_failures) / len(recent_events) if recent_events else 0.0
                        logger.warning(
                            f"High compaction failure rate detected: {len(recent_failures)}/{len(recent_events)} "
                            f"({failure_rate:.1%}). Consider disabling LLM compaction."
                        )
                        # Don't auto-disable, just warn (user should decide)
                        actions_taken.append({
                            "action": "warn_llm_compaction",
                            "reason": f"High failure rate ({failure_rate:.1%})",
                            "suggestion": "Set BOP_USE_LLM_COMPACTION=false",
                            "failure_count": len(recent_failures),
                            "total_recent": len(recent_events),
                        })

            # Action 2: If errors are accumulating, increase history limit
            error_count = len(self._metrics.get("errors", []))
            if error_count > 10 and error_count % 5 == 0:
                current_max = self.max_conversation_history
                # Validate current_max is reasonable
                if not isinstance(current_max, int) or current_max < 1:
                    logger.warning(f"Invalid max_conversation_history: {current_max}, skipping auto-adjustment")
                else:
                    suggested_max = min(current_max + 10, 100)  # Cap at 100
                    if suggested_max > current_max:
                        logger.info(
                            f"Auto-adjusting max_conversation_history: {current_max} → {suggested_max} "
                            f"(error count: {error_count})"
                        )
                        self.max_conversation_history = suggested_max
                        actions_taken.append({
                            "action": "increase_history_limit",
                            "old_value": current_max,
                            "new_value": suggested_max,
                            "reason": f"High error rate ({error_count} errors)",
                        })

        if actions_taken:
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "health_score": health_score,
                "actions": actions_taken,
            }

        return None

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses tiktoken if available for accuracy, otherwise uses character-based estimation.

        Handles edge cases:
        - None or empty strings
        - Very long strings (no overflow)
        - Non-ASCII characters (handled by tiktoken or character count)

        Args:
            text: Text to estimate tokens for (can be None or empty)

        Returns:
            Estimated token count (always >= 0)
        """
        if not text:
            return 0

        # Ensure text is a string
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception:
                logger.warning(f"Could not convert text to string for token estimation: {type(text)}")
                return 0

        # Handle empty string after conversion
        if not text:
            return 0

        if self._tokenizer is not None:
            try:
                # tiktoken handles encoding internally
                encoded = self._tokenizer.encode(text)
                return len(encoded)
            except (UnicodeEncodeError, ValueError) as e:
                logger.debug(f"tiktoken encoding failed (non-UTF8?): {e}, using estimation")
            except Exception as e:
                logger.debug(f"tiktoken encoding failed: {e}, using estimation")

        # Fallback: character-based estimation (1 token ≈ 4 characters)
        # This is a common approximation for English text
        # For non-ASCII, this may underestimate, but it's safe
        char_count = len(text)
        if char_count == 0:
            return 0

        # Use integer division to avoid float issues
        estimated = char_count // 4

        # Ensure at least 1 token for non-empty text (unless truly empty)
        # This handles very short strings
        return max(1, estimated) if char_count > 0 else 0

    def _get_conversation_token_count(self) -> int:
        """
        Get total estimated token count for conversation history.

        Includes:
        - Content tokens (from _estimate_tokens)
        - Message structure overhead (role, formatting, etc.)

        Handles edge cases:
        - Empty conversation history
        - Messages with missing content
        - Invalid message structure

        Returns:
            Total estimated tokens (always >= 0)
        """
        if not self.conversation_history:
            return 0

        total = 0
        for msg in self.conversation_history:
            if not isinstance(msg, dict):
                # Skip invalid messages
                continue

            content = msg.get("content", "")
            if content:
                total += self._estimate_tokens(content)

            # Add overhead for message structure (role, formatting, etc.)
            # Approximate: role name, JSON structure, etc.
            total += 10  # Approximate overhead per message

        return total

    def _save_metrics(self) -> None:
        """
        Save metrics to file for persistence.

        Uses atomic write pattern to prevent corruption:
        1. Write to temporary file
        2. Replace original file atomically
        3. Handles permission errors, disk full, and JSON serialization errors gracefully
        """
        if self._metrics is None or self.metrics_path is None:
            return

        try:
            # Ensure directory exists
            self.metrics_path.parent.mkdir(parents=True, exist_ok=True)

            # Validate metrics structure before saving
            if not isinstance(self._metrics, dict):
                logger.error("Metrics structure is invalid, cannot save")
                return

            # Save with atomic write
            temp_file = self.metrics_path.with_suffix('.json.tmp')
            data = {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "metrics": self._metrics.copy(),
            }

            # Serialize with error handling
            try:
                json_str = json.dumps(data, indent=2, default=str)  # default=str handles non-serializable types
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize metrics: {e}")
                return

            # Write to temp file
            try:
                temp_file.write_text(json_str, encoding='utf-8')
            except (OSError, IOError) as e:
                logger.error(f"Failed to write metrics file: {e}")
                return

            # Atomic replace
            try:
                temp_file.replace(self.metrics_path)
                logger.debug(f"Saved metrics to {self.metrics_path}")
            except (OSError, IOError) as e:
                logger.error(f"Failed to replace metrics file: {e}")
                # Clean up temp file
                try:
                    temp_file.unlink()
                except Exception:
                    pass
                return

        except Exception as e:
            logger.warning(f"Unexpected error saving metrics: {e}", exc_info=True)

    def _load_metrics(self) -> None:
        """
        Load historical metrics from file.

        Handles:
        - Missing file (graceful skip)
        - Corrupted JSON (logs error, continues)
        - Version mismatches (validates structure)
        - Invalid data types (validates before merging)
        - Missing keys (handles gracefully)
        """
        if self._metrics is None or self.metrics_path is None:
            return

        if not self.metrics_path.exists():
            logger.debug(f"Metrics file does not exist: {self.metrics_path}")
            return

        try:
            # Read file with encoding
            try:
                file_content = self.metrics_path.read_text(encoding='utf-8')
            except (OSError, IOError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to read metrics file: {e}")
                return

            if not file_content.strip():
                logger.warning(f"Metrics file is empty: {self.metrics_path}")
                return

            # Parse JSON with validation
            try:
                data = json.loads(file_content)
            except json.JSONDecodeError as e:
                logger.error(f"Corrupted metrics file (invalid JSON): {e}")
                # Could attempt recovery here, but for now just log
                return

            # Validate structure
            if not isinstance(data, dict):
                logger.error("Metrics file has invalid structure (not a dict)")
                return

            # Check version (for future compatibility)
            version = data.get("version", "unknown")
            if version != "1.0":
                logger.warning(f"Metrics file version mismatch: {version} (expected 1.0)")
                # Continue anyway, but log warning

            # Load metrics
            if "metrics" in data and isinstance(data["metrics"], dict):
                historical = data["metrics"]
                loaded_count = 0

                for key in self._metrics.keys():
                    if key in historical:
                        historical_data = historical[key]

                        # Validate historical data is a list
                        if not isinstance(historical_data, list):
                            logger.warning(f"Invalid metrics data type for '{key}': expected list, got {type(historical_data)}")
                            continue

                        # Validate items in list are dicts (for structured metrics)
                        if historical_data and not all(isinstance(item, dict) for item in historical_data):
                            logger.warning(f"Invalid metrics items for '{key}': expected list of dicts")
                            continue

                        # Merge: keep recent metrics, append historical (limit to last 1000 per type)
                        # Take last 500 from history to avoid unbounded growth
                        historical_slice = historical_data[-500:] if len(historical_data) > 500 else historical_data
                        self._metrics[key].extend(historical_slice)
                        loaded_count += len(historical_slice)

                        # Limit total size to prevent memory issues
                        if len(self._metrics[key]) > 1000:
                            self._metrics[key] = self._metrics[key][-1000:]
                            logger.debug(f"Trimmed metrics '{key}' to 1000 items")

                if loaded_count > 0:
                    logger.info(f"Loaded {loaded_count} historical metrics from {self.metrics_path}")
                else:
                    logger.debug("No valid historical metrics to load")
            else:
                logger.warning("Metrics file missing 'metrics' key or invalid structure")

        except Exception as e:
            logger.warning(f"Unexpected error loading metrics: {e}", exc_info=True)

    async def _compact_conversation_history(self) -> None:
        """
        Compact conversation history when it exceeds threshold (70% of max).

        Based on Claude Code compaction pattern with robust error handling:
        - Trigger at 70% capacity (not 100%) to prevent performance degradation
        - Keep recent messages (last N messages)
        - Summarize older messages into a summary
        - Preserve critical context (architectural decisions, unresolved issues)
        - Never lose conversation history if compaction fails (graceful degradation)

        Supports both heuristic-based (fast) and LLM-based (higher quality) summarization.

        This prevents context window overflow while maintaining coherence.
        """
        compaction_threshold = int(self.max_conversation_history * 0.7)
        if len(self.conversation_history) <= compaction_threshold:
            return

        # Validate we have enough messages to compact safely
        if len(self.conversation_history) < 10:
            logger.warning("Not enough messages to compact safely, skipping")
            return

        # Keep recent messages (last 20 messages = ~10 exchanges)
        keep_recent = 20
        recent_messages = self.conversation_history[-keep_recent:]
        old_messages = self.conversation_history[:-keep_recent]

        # Store original history for rollback if compaction fails
        original_history = self.conversation_history.copy()
        original_summary = self.conversation_summary
        before_count = len(original_history)  # Track for metrics

        try:
            # If we have a previous summary, include it in the old messages to summarize
            if self.conversation_summary:
                old_messages.insert(0, {
                    "role": "system",
                    "content": f"[Previous conversation summary]: {self.conversation_summary}"
                })

            # Use LLM-based compaction if enabled (better quality, adds latency/cost)
            new_summary = None
            if self.use_llm_compaction and self.llm_service:
                try:
                    # Format messages for LLM summarization
                    messages_text = "\n".join([
                        f"{msg.get('role', 'unknown')}: {msg.get('content', '')[:500]}"
                        for msg in old_messages[:30]  # Limit to avoid token overflow
                    ])

                    prompt = f"""Summarize this conversation history, preserving:
1. User requests and goals
2. Key architectural decisions and choices made
3. Unresolved issues, errors, or problems
4. Important context needed for continuation

Conversation history:
{messages_text}

Provide a concise summary that preserves critical information for continuing the conversation."""

                    summary_result = await self.llm_service.agent.run(prompt)
                    new_summary = summary_result.data[:1000]  # Limit summary length

                    # Validate summary quality (basic check)
                    if len(new_summary) < 20:
                        raise ValueError("LLM summary too short, likely failed")

                    self.conversation_summary = new_summary
                    logger.info("Used LLM-based compaction for higher quality summary")
                except Exception as e:
                    logger.warning(f"LLM compaction failed, falling back to heuristic: {e}")
                    new_summary = None  # Will use heuristic fallback

            # Heuristic-based summarization (fallback or default)
            # Improved with better NLP techniques (key term extraction)
            if new_summary is None:
                try:
                    from .token_importance import extract_key_terms

                    summary_parts = []
                    user_requests = []
                    key_decisions = []
                    all_key_terms = []

                    for msg in old_messages:
                        if not isinstance(msg, dict):
                            continue  # Skip invalid messages

                        role = msg.get("role", "")
                        content = msg.get("content", "")

                        # Skip empty content
                        if not content or not isinstance(content, str):
                            continue

                        # Normalize content (strip whitespace)
                        content = content.strip()
                        if not content:
                            continue

                        if role == "user":
                            # Truncate long requests to avoid summary bloat
                            truncated = content[:200] if len(content) > 200 else content
                            user_requests.append(truncated)
                            # Extract key terms from user requests
                            try:
                                terms = extract_key_terms(content, max_terms=5)
                                if terms:
                                    all_key_terms.extend(terms)
                            except Exception as e:
                                logger.debug(f"Key term extraction failed for user message: {e}")
                        elif role == "assistant":
                            # Look for key phrases indicating decisions or issues
                            content_lower = content.lower()
                            key_phrases = ["decided", "chose", "implemented", "error", "issue", "problem", "bug", "fix",
                                          "created", "added", "removed", "changed", "updated", "fixed", "resolved"]
                            if any(phrase in content_lower for phrase in key_phrases):
                                # Extract first sentence or key portion
                                sentences = content.split('.')
                                if sentences and sentences[0].strip():
                                    key_decisions.append(sentences[0].strip()[:300])
                                elif content.strip():
                                    key_decisions.append(content.strip()[:300])
                            # Extract key terms from assistant messages too
                            try:
                                terms = extract_key_terms(content, max_terms=3)
                                if terms:
                                    all_key_terms.extend(terms)
                            except Exception as e:
                                logger.debug(f"Key term extraction failed for assistant message: {e}")

                    # Build summary with improved structure
                    if user_requests:
                        summary_parts.append(f"User requests: {', '.join(user_requests[:5])}")
                    if key_decisions:
                        summary_parts.append(f"Key decisions/issues: {', '.join(key_decisions[:3])}")
                    if all_key_terms:
                        # Get most frequent key terms
                        term_counts = Counter(all_key_terms)
                        top_terms = [term for term, _ in term_counts.most_common(5)]
                        summary_parts.append(f"Key topics: {', '.join(top_terms)}")

                    if summary_parts:
                        self.conversation_summary = " | ".join(summary_parts)
                    else:
                        self.conversation_summary = f"Previous conversation with {len(old_messages)} messages"
                except Exception as e:
                    # Fallback to simple summarization if key term extraction fails
                    logger.warning(f"Key term extraction failed, using simple summarization: {e}")
                    summary_parts = []
                    user_requests = []
                    key_decisions = []

                    for msg in old_messages:
                        if msg.get("role") == "user":
                            user_requests.append(msg.get("content", "")[:200])
                        elif msg.get("role") == "assistant":
                            content = msg.get("content", "")
                            if any(phrase in content.lower() for phrase in ["decided", "chose", "implemented", "error", "issue", "problem", "bug", "fix"]):
                                key_decisions.append(content[:300])

                    if user_requests:
                        summary_parts.append(f"User requests: {', '.join(user_requests[:5])}")
                    if key_decisions:
                        summary_parts.append(f"Key points: {', '.join(key_decisions[:3])}")

                    if summary_parts:
                        self.conversation_summary = " | ".join(summary_parts)
                    else:
                        self.conversation_summary = f"Previous conversation with {len(old_messages)} messages"

            # Validate summary was created
            if not self.conversation_summary:
                raise ValueError("Failed to create conversation summary")

            # Replace old messages with summary message (atomic operation)
            self.conversation_history = [
                {"role": "system", "content": f"[Conversation summary]: {self.conversation_summary}"}
            ] + recent_messages

            # Verify compaction succeeded (basic sanity check)
            if len(self.conversation_history) > self.max_conversation_history:
                raise ValueError(f"Compaction failed: history still too long ({len(self.conversation_history)} > {self.max_conversation_history})")

            logger.info(f"Compacted conversation history: {len(old_messages)} messages → summary, kept {len(recent_messages)} recent messages")

            # Record metrics for observability
            if self._metrics is not None:
                after_count = len(self.conversation_history)
                self._metrics["compaction_events"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "before": before_count,
                    "after": after_count,
                    "method": "llm" if new_summary else "heuristic",
                    "success": True,
                    "compression_ratio": after_count / before_count if before_count > 0 else 0,
                })
                # Auto-save metrics periodically (every 10 events)
                if len(self._metrics["compaction_events"]) % 10 == 0:
                    self._save_metrics()

                # Automated health check and optimization
                optimization_result = self._check_health_and_auto_optimize()
                if optimization_result:
                    logger.info(f"Auto-optimization performed: {optimization_result}")

        except Exception as e:
            # CRITICAL: Never lose conversation history if compaction fails
            # Rollback to original state
            logger.error(f"Compaction failed, rolling back to original history: {e}", exc_info=True)
            self.conversation_history = original_history
            self.conversation_summary = original_summary

            # Log warning but continue - system can still function with longer history
            logger.warning(
                f"Conversation history compaction failed. "
                f"History length: {len(self.conversation_history)}/{self.max_conversation_history}. "
                f"System will continue but may experience performance degradation."
            )

            # Record failure metrics
            if self._metrics is not None:
                self._metrics["compaction_events"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "before": len(original_history),
                    "after": len(self.conversation_history),
                    "method": "unknown",
                    "success": False,
                    "error": str(e),
                })
                self._metrics["errors"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": "compaction_failure",
                    "message": str(e),
                    "context": {"history_length": len(self.conversation_history)},
                })

    def _save_todo_to_scratchpad(self) -> None:
        """
        Save TODO list to scratchpad file (todo.md) for persistent memory.

        Based on Manus pattern: file-based memory that persists across context resets.
        This allows the agent to continue work even after context compaction.
        """
        if not self.enable_scratchpad or not self.scratchpad_dir.exists():
            return

        try:
            todo_file = self.scratchpad_dir / "todo.md"
            lines = ["# TODO List\n", f"Last updated: {datetime.now(timezone.utc).isoformat()}\n\n"]

            for item in self.todo_list:
                status_icon = "✓" if item.get("status") == "completed" else "→" if item.get("status") == "in_progress" else "○"
                priority = item.get("priority", "medium")
                lines.append(
                    f"{status_icon} [{item.get('id', '?')}] {item.get('content', '')} "
                    f"(status: {item.get('status', 'pending')}, priority: {priority})\n"
                )

            completed = sum(1 for item in self.todo_list if item.get("status") == "completed")
            total = len(self.todo_list)
            lines.append(f"\nProgress: {completed}/{total} completed\n")

            todo_file.write_text("".join(lines))
            logger.debug(f"Saved TODO list to scratchpad: {todo_file}")
        except Exception as e:
            logger.warning(f"Failed to save TODO list to scratchpad: {e}")

    def _load_todo_from_scratchpad(self) -> None:
        """
        Load TODO list from scratchpad file if it exists.

        Allows agent to resume work after context reset or restart.
        """
        if not self.enable_scratchpad or not self.scratchpad_dir.exists():
            return

        todo_file = self.scratchpad_dir / "todo.md"
        if not todo_file.exists():
            return

        try:
            # Parse TODO list from markdown file
            # Simple parser: looks for lines with status icons and extracts TODO items
            content = todo_file.read_text()
            todos = []

            for line in content.split("\n"):
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("Progress:"):
                    continue

                # Parse format: "✓ [id] content (status: ..., priority: ...)"
                # Extract id, content, status, priority
                match = re.match(r'[✓→○]\s+\[([^\]]+)\]\s+(.+?)\s+\(status:\s+(\w+),\s+priority:\s+(\w+)\)', line)
                if match:
                    todos.append({
                        "id": match.group(1),
                        "content": match.group(2).strip(),
                        "status": match.group(3),
                        "priority": match.group(4),
                    })

            if todos:
                self.todo_list = todos
                logger.debug(f"Loaded {len(todos)} TODO items from scratchpad")
        except Exception as e:
            logger.warning(f"Failed to load TODO list from scratchpad: {e}")

    def _create_response_tiers(
        self,
        full_response: str,
        research: Dict[str, Any],
        query: str,
    ) -> Dict[str, str]:
        """
        Create progressive disclosure tiers for response.

        Gracefully handles errors and returns minimal tiers on failure.

        Returns:
            Dictionary with summary, structured, detailed, evidence tiers
        """
        # Ensure full_response is a string
        if not isinstance(full_response, str):
            full_response = str(full_response) if full_response else ""

        # Summary: 1-2 sentence direct answer
        try:
            summary = full_response.split('.')[0] if '.' in full_response else full_response[:150]
            if len(summary) > 150:
                summary = summary[:147] + "..."
        except Exception as e:
            logger.warning(f"Failed to create summary tier: {e}", exc_info=True)
            summary = full_response[:150] + "..." if len(full_response) > 150 else full_response

        # Structured: Organized breakdown (use research synthesis if available)
        try:
            structured = ""
            if research and isinstance(research, dict):
                final_synthesis = research.get("final_synthesis", "")
                if final_synthesis:
                    structured = final_synthesis
                else:
                    # Use subsolutions if available
                    subsolutions = research.get("subsolutions", [])
                    if subsolutions:
                        structured_parts = []
                        for sub in subsolutions[:3]:  # Top 3
                            try:
                                subproblem = sub.get("subproblem", "")
                                synthesis = sub.get("synthesis", "")
                                if synthesis:
                                    structured_parts.append(f"**{subproblem}**: {synthesis[:200]}")
                            except Exception as e:
                                logger.debug(f"Failed to process subsolution for structured tier: {e}")
                                continue
                        structured = "\n\n".join(structured_parts)

            if not structured:
                # Fallback: use first 3 paragraphs of response
                paragraphs = full_response.split('\n\n')[:3]
                structured = "\n\n".join(paragraphs)
        except Exception as e:
            logger.warning(f"Failed to create structured tier: {e}", exc_info=True)
            structured = full_response[:500] + "..." if len(full_response) > 500 else full_response

        # Detailed: Full response (always available)
        detailed = full_response

        # Evidence: Full research synthesis
        try:
            evidence = ""
            if research and isinstance(research, dict):
                evidence_parts = []
                if research.get("final_synthesis"):
                    evidence_parts.append(f"**Final Synthesis**:\n{research['final_synthesis']}")

                subsolutions = research.get("subsolutions", [])
                if subsolutions:
                    evidence_parts.append("\n**Detailed Breakdown**:")
                    for sub in subsolutions:
                        try:
                            subproblem = sub.get("subproblem", "")
                            synthesis = sub.get("synthesis", "")
                            tools = sub.get("tools_used", [])
                            if synthesis:
                                evidence_parts.append(
                                    f"\n**{subproblem}**\n"
                                    f"Tools: {', '.join(tools)}\n"
                                    f"{synthesis}"
                                )
                        except Exception as e:
                            logger.debug(f"Failed to process subsolution for evidence tier: {e}")
                            continue

                evidence = "\n\n".join(evidence_parts) if evidence_parts else full_response
            else:
                evidence = full_response
        except Exception as e:
            logger.warning(f"Failed to create evidence tier: {e}", exc_info=True)
            evidence = full_response

        return {
            "summary": summary,
            "structured": structured,
            "detailed": detailed,
            "evidence": evidence,
        }

    def _add_source_references(
        self,
        response_text: str,
        research: Dict[str, Any],
    ) -> str:
        """
        Add source references to response text.

        FIXED: Now matches sources to actual response text, not synthesis.
        Uses token-level provenance to show which query tokens matched which document tokens.
        """
        if not research or not isinstance(research, dict):
            return response_text

        # Build provenance map: matches claims in response text to sources
        provenance_map = build_provenance_map(response_text, research)

        if not provenance_map:
            return response_text

        # Add source references section
        response_text += "\n\n**Sources:**\n"

        # Add top claims with their sources and relevance scores
        # Sort by combined quality and relevance (better than just source count)
        def get_claim_priority(item):
            claim_text, prov_data = item
            quality = prov_data.get("quality_score", 0.5)
            relevance = prov_data.get("top_source_relevance", 0.0)
            num_sources = prov_data.get("num_sources", 0)
            # Combined priority
            return (relevance * quality, num_sources)

        sorted_claims = sorted(
            provenance_map.items(),
            key=get_claim_priority,
            reverse=True
        )[:5]  # Top 5 claims

        for claim_text, provenance_data in sorted_claims:
            claim_short = claim_text[:75] + "..." if len(claim_text) > 75 else claim_text
            sources = provenance_data.get("sources", [])

            if sources:
                # Get unique source names
                source_names = list(set(s["source"] for s in sources))
                sources_str = ", ".join(source_names[:3])
                if len(source_names) > 3:
                    sources_str += f" (+{len(source_names) - 3} more)"

                # Get relevance score if available
                top_source = sources[0]
                relevance_score = None
                if "relevance_breakdown" in top_source:
                    relevance_score = top_source["relevance_breakdown"].get("overall_score")
                elif "overlap_ratio" in top_source:
                    relevance_score = top_source["overlap_ratio"]

                # Add claim with source citation and relevance (with indicator)
                if relevance_score is not None:
                    # Add relevance indicator
                    if relevance_score > 0.7:
                        indicator = "🟢"
                    elif relevance_score > 0.5:
                        indicator = "🟡"
                    else:
                        indicator = "🔴"
                    response_text += f"- {claim_short} [Sources: {sources_str}] {indicator} Relevance: {relevance_score:.2f}\n"
                else:
                    response_text += f"- {claim_short} [Sources: {sources_str}]\n"

        return response_text

