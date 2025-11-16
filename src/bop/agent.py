"""Main agent for knowledge structure research and reasoning."""

import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from .research import ResearchAgent, load_content
from .schemas import get_schema, list_schemas, hydrate_schema
from .orchestrator import StructuredOrchestrator
from .llm import LLMService
from .quality_feedback import QualityFeedbackLoop
from .adaptive_quality import AdaptiveQualityManager
from .provenance import build_provenance_map, extract_claims_from_response, match_claim_to_sources
from .knowledge_tracking import KnowledgeTracker
from .query_refinement import refine_query_from_provenance
from .meta_learning import MetaLearner
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
        """
        self.research_agent = ResearchAgent()
        self.llm_service = llm_service
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
        
        # Save knowledge tracker state on agent cleanup (if persistence enabled)
        # Note: This is best-effort - proper cleanup would need __del__ or context manager

        # Add temporal information (timestamp tracking)
        from datetime import datetime, timezone
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
            from .validation import validate_response, IntrospectionLogger
            
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
        system_reminders: Optional[List[str]] = None,
    ) -> str:
        """
        Generate response based on message and context.
        
        Args:
            message: User message
            context: Context dictionary
            schema: Optional reasoning schema
            expected_length: Optional target response length (for adaptation)
            system_reminders: Optional system reminders to keep agent on track
        """
        if self.llm_service:
            try:
                # Pass target_length to LLM service for better control
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
        Search the local knowledge base.

        Args:
            query: Search query

        Returns:
            List of matching content snippets
        """
        results = []
        query_lower = query.lower()

        for doc_name, content in self.knowledge_base.items():
            if query_lower in content.lower():
                # Simple keyword matching - could be improved
                results.append({
                    "document": doc_name,
                    "matches": content.count(query_lower),
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
                            # Limit to last 10 beliefs
                            if len(self.prior_beliefs) > 10:
                                self.prior_beliefs = self.prior_beliefs[-10:]
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
        
        # Keep only last 10 queries
        if len(self.recent_queries) > 10:
            self.recent_queries = self.recent_queries[-10:]
    
    def _compute_topic_similarity(self, current_message: str, recent_topics: List[str]) -> float:
        """
        Compute similarity between current message and recent topics.
        
        Returns:
            0.0 to 1.0 similarity score
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
        for topic in recent_topics:
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
        
        if not similarities:
            return 0.0
        
        return float(sum(similarities) / len(similarities))
    
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

