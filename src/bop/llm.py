"""LLM integration using pydantic-ai with multi-backend support."""

import os
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from pydantic_ai import Agent

from .schemas import ReasoningSchema
from .llm_capabilities import (
    LLMProviderCapabilities,
    BaseCapabilityAdapter,
    create_capability_adapter,
)

logger = logging.getLogger(__name__)

# Try to import all supported model backends
try:
    from pydantic_ai.models.openai import OpenAIChatModel
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from pydantic_ai.models.anthropic import AnthropicModel
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from pydantic_ai.models.google import GoogleModel
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    from pydantic_ai.providers.openai import OpenAIProvider
    from pydantic_ai.providers.anthropic import AnthropicProvider
    from pydantic_ai.providers.google import GoogleProvider
    PROVIDERS_AVAILABLE = True
except ImportError:
    PROVIDERS_AVAILABLE = False


class StructuredReasoning(BaseModel):
    """Structured reasoning output following a schema."""

    reasoning_steps: List[Dict[str, Any]]
    intermediate_results: List[str]
    final_result: str
    confidence: float


class DecompositionResult(BaseModel):
    """Result of query decomposition."""

    subproblems: List[str]
    rationale: str


class SynthesisResult(BaseModel):
    """Result of synthesizing multiple tool results."""

    synthesized_answer: str
    key_points: List[str]
    sources_used: List[str]


class LLMService:
    """Service for LLM interactions using pydantic-ai with multi-backend support."""

    def __init__(
        self,
        backend: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        Initialize LLM service with support for multiple backends.

        Args:
            backend: Backend to use ('openai', 'anthropic', 'google', 'groq', or None for auto-detect)
            model_name: Model name (defaults based on backend)

        Supported backends:
        - openai: OpenAI models (gpt-4o, gpt-4o-mini, etc.)
        - anthropic: Anthropic Claude models (claude-sonnet-4-5, claude-3-5-sonnet-latest, etc.)
        - google: Google Gemini models (gemini-2.5-pro, gemini-1.5-flash, etc.)
        - groq: Groq models (llama-3.3-70b-versatile, etc.)

        Environment variables:
        - OPENAI_API_KEY: For OpenAI backend
        - ANTHROPIC_API_KEY: For Anthropic backend
        - GEMINI_API_KEY or GOOGLE_API_KEY: For Google backend
        - GROQ_API_KEY: For Groq backend
        - LLM_BACKEND: Default backend to use (if not specified)
        - LLM_MODEL: Default model name (if not specified)
        """
        backend = backend or os.getenv("LLM_BACKEND")
        model_name = model_name or os.getenv("LLM_MODEL")

        # Auto-detect backend if not specified
        if not backend:
            backend = self._detect_backend()

        # Initialize model based on backend
        self.backend = backend
        self.model = self._create_model(backend, model_name)
        self.agent = Agent(self.model, result_type=str)
        
        # Initialize capability adapter
        self.capabilities: BaseCapabilityAdapter = create_capability_adapter(
            self.model, backend
        )

    def _detect_backend(self) -> str:
        """Auto-detect backend from available API keys."""
        # Check in order of preference
        # Note: Groq is fastest, so prioritize it if speed is important
        # For quality, prefer Anthropic > OpenAI > Google > Groq
        if os.getenv("GROQ_API_KEY") and OPENAI_AVAILABLE:
            # Groq is fastest - good for speed-critical operations
            logger.info("Auto-detected Groq backend (fast inference)")
            return "groq"
        elif os.getenv("ANTHROPIC_API_KEY") and ANTHROPIC_AVAILABLE:
            return "anthropic"
        elif os.getenv("OPENAI_API_KEY") and OPENAI_AVAILABLE:
            return "openai"
        elif (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) and GOOGLE_AVAILABLE:
            return "google"
        else:
            # Default to OpenAI if available
            if OPENAI_AVAILABLE:
                return "openai"
            raise ValueError(
                "No LLM backend available. Install pydantic-ai with appropriate extras:\n"
                "  - OpenAI: pip install 'pydantic-ai[openai]'\n"
                "  - Anthropic: pip install 'pydantic-ai[anthropic]'\n"
                "  - Google: pip install 'pydantic-ai[google]'\n"
                "And set the corresponding API key environment variable."
            )

    def _create_model(self, backend: str, model_name: Optional[str] = None):
        """Create model instance for the specified backend."""
        if backend == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI models not available. Install: pip install 'pydantic-ai[openai]'")
            model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            return OpenAIChatModel(model_name)

        elif backend == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic models not available. Install: pip install 'pydantic-ai[anthropic]'")
            model_name = model_name or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            return AnthropicModel(model_name)

        elif backend == "google":
            if not GOOGLE_AVAILABLE:
                raise ImportError("Google models not available. Install: pip install 'pydantic-ai[google]'")
            model_name = model_name or os.getenv("GEMINI_MODEL") or os.getenv("GOOGLE_MODEL", "gemini-2.5-pro")
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required")
            if PROVIDERS_AVAILABLE:
                provider = GoogleProvider(api_key=api_key)
                return GoogleModel(model_name, provider=provider)
            else:
                return GoogleModel(model_name)

        elif backend == "groq":
            if not OPENAI_AVAILABLE:
                raise ImportError("Groq requires OpenAI models. Install: pip install 'pydantic-ai[openai]'")
            model_name = model_name or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is required")
            # Groq uses OpenAI-compatible API via string notation
            # pydantic-ai supports groq: prefix automatically
            try:
                # Try using Agent string notation (simplest)
                agent = Agent(f"groq:{model_name}")
                return agent.model
            except Exception:
                # Fallback: use OpenAI provider with Groq base URL
                if PROVIDERS_AVAILABLE:
                    provider = OpenAIProvider(
                        base_url="https://api.groq.com/openai/v1",
                        api_key=api_key,
                    )
                    return OpenAIChatModel(model_name, provider=provider)
                else:
                    raise ImportError("Groq provider not available")

        else:
            raise ValueError(f"Unsupported backend: {backend}. Supported: openai, anthropic, google, groq")

    async def generate_response(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        schema: Optional[ReasoningSchema] = None,
        target_length: Optional[int] = None,
    ) -> str:
        """
        Generate a response to a message.

        Args:
            message: User message
            context: Optional context dictionary (research results, etc.)
            schema: Optional reasoning schema to guide response

        Returns:
            Generated response text
        """
        # Build prompt with context
        prompt_parts = [message]

        if context:
            if context.get("research"):
                prompt_parts.append("\n\nResearch context:")
                research = context["research"]
                if isinstance(research, dict):
                    if research.get("summary"):
                        prompt_parts.append(research["summary"])
                    if research.get("final_synthesis"):
                        prompt_parts.append(research["final_synthesis"])

            if context.get("knowledge_base_results"):
                prompt_parts.append("\n\nRelevant knowledge base content:")
                for result in context["knowledge_base_results"]:
                    prompt_parts.append(f"- {result}")

        if schema:
            prompt_parts.append(f"\n\nUse the {schema.name} reasoning approach:")
            prompt_parts.append(schema.description)
            if schema.schema_def:
                prompt_parts.append("\nSchema structure:")
                for key, desc in schema.schema_def.items():
                    if isinstance(desc, str):
                        prompt_parts.append(f"- {key}: {desc}")
        
        # Add length guidance if provided
        if target_length:
            if target_length < 200:
                prompt_parts.append(f"\n\nProvide a concise answer (approximately {target_length} characters).")
            elif target_length < 1000:
                prompt_parts.append(f"\n\nProvide a detailed answer (approximately {target_length} characters).")
            else:
                prompt_parts.append(f"\n\nProvide a comprehensive answer (approximately {target_length} characters).")
        
        # Add storytelling guidance for better narrative structure
        # Use connective phrases and problem-solution structure
        prompt_parts.append(
            "\n\nStructure your response as a clear narrative: "
            "1. Start with the problem or question context, "
            "2. Present supporting evidence or statistics, "
            "3. Explain the solution or answer, "
            "4. Use connective phrases like 'This led to...', 'To understand why...', "
            "'Building on this...', 'In contrast...' to guide the reader through the information flow."
        )

        prompt = "\n".join(prompt_parts)

        # Check cache first
        try:
            from .cache import get_cached_llm_response, cache_llm_response
            cache_key = f"{prompt}|{self.backend}|{self.model.model_name if hasattr(self.model, 'model_name') else 'default'}"
            cached = get_cached_llm_response(cache_key, self.backend)
            if cached is not None:
                logger.info(f"Cache hit for LLM response (backend: {self.backend})")
                return cached
        except Exception as e:
            logger.debug(f"Cache check failed: {e}")

        result = await self.agent.run(prompt)
        response_text = result.data
        
        # Cache successful response
        try:
            from .cache import cache_llm_response
            cache_key = f"{prompt}|{self.backend}|{self.model.model_name if hasattr(self.model, 'model_name') else 'default'}"
            cache_llm_response(cache_key, self.backend, response_text, ttl_hours=24 * 3)
        except Exception as e:
            logger.debug(f"Cache write failed: {e}")
        
        return response_text

    async def hydrate_schema(
        self,
        schema: ReasoningSchema,
        user_input: str,
    ) -> Dict[str, Any]:
        """
        Hydrate a schema with actual reasoning based on user input.

        Args:
            schema: Schema to hydrate
            user_input: User input to reason about

        Returns:
            Hydrated schema dictionary
        """
        schema_prompt = f"""
Given the following reasoning schema and user input, generate a structured reasoning response.

Schema: {schema.name}
Description: {schema.description}

Schema structure:
{self._format_schema_def(schema.schema_def)}

User input: {user_input}

Generate a response following the schema structure. Return a JSON object matching the schema.
"""

        # Use agent with structured output
        agent = Agent(self.model, result_type=Dict[str, Any])
        result = await agent.run(schema_prompt)

        return result.data if isinstance(result.data, dict) else {}

    async def decompose_query(
        self,
        query: str,
        schema: ReasoningSchema,
    ) -> List[str]:
        """
        Decompose a query into subproblems using LLM.

        Args:
            query: Query to decompose
            schema: Schema to guide decomposition

        Returns:
            List of subproblems
        """
        if schema.name == "decompose_and_synthesize":
            prompt = f"""
Decompose the following query into 3-5 focused subproblems that can be researched independently.

Query: {query}

Return a JSON array of subproblem strings, each focused on a specific aspect:
- Theoretical foundation
- Recent empirical results
- Alternative perspectives
- Practical applications
- Open questions

Return only the JSON array, no other text.
"""
        else:
            # For other schemas, use simpler decomposition
            prompt = f"""
Break down this query into 2-3 focused subproblems:

Query: {query}

Return a JSON array of subproblem strings.
"""

        agent = Agent(self.model, result_type=List[str])
        result = await agent.run(prompt)

        if isinstance(result.data, list):
            return result.data
        # Fallback to simple split
        return [query]

    async def synthesize_tool_results(
        self,
        tool_results: List[Dict[str, Any]],
        subproblem: str,
        use_ib_filtering: bool = True,
        ib_beta: float = 0.5,
    ) -> str:
        """
        Synthesize results from multiple tools into coherent answer.

        Args:
            tool_results: Results from multiple tools
            subproblem: The subproblem being addressed
            use_ib_filtering: Whether to apply Information Bottleneck filtering
            ib_beta: Beta parameter for IB filtering (higher = more compression)

        Returns:
            Synthesized answer
        """
        if not tool_results:
            return f"No results found for: {subproblem}"

        # Filter valid results
        valid_results = [r for r in tool_results if r and r.get("result")]

        if not valid_results:
            return f"No valid results found for: {subproblem}"

        # Apply IB filtering before synthesis if enabled and we have multiple results
        # 
        # Why IB Filtering: Research (arXiv 2406.01549) shows that most retrieved content
        # is noise. IB filtering removes irrelevant passages before synthesis, reducing
        # token usage by 20-30% while maintaining or improving quality. This addresses the
        # "waste" component of the degradation triple.
        # 
        # We only filter when we have multiple results (>2) to avoid over-filtering.
        # The min_mi=0.3 threshold filters out low-relevance results while preserving
        # high-relevance ones. The max_results=5 limit prevents token overflow while
        # keeping the most relevant information.
        ib_metadata = None
        if use_ib_filtering and len(valid_results) > 2:
            try:
                from .information_bottleneck import filter_with_information_bottleneck
                filtered_results, ib_metadata = filter_with_information_bottleneck(
                    valid_results,
                    query=subproblem,
                    beta=ib_beta,
                    min_mi=0.3,  # Filter out results with <30% mutual information
                    max_results=5,  # Limit to top 5 most relevant (prevents token overflow)
                )
                if filtered_results:
                    valid_results = filtered_results
                    logger.debug(
                        f"IB filtering: {ib_metadata['compression_ratio']:.2%} compression, "
                        f"removed {ib_metadata['removed_count']} results, "
                        f"avg MI: {ib_metadata['avg_mi']:.3f}"
                    )
            except Exception as e:
                # Fallback: If IB filtering fails, use all results (graceful degradation)
                logger.warning(f"IB filtering failed: {e}, using all results", exc_info=True)
                ib_metadata = None

        # Build synthesis prompt
        results_text = "\n\n".join(
            f"Tool: {r.get('tool', 'unknown')}\nResult: {r.get('result', '')[:500]}"
            for r in valid_results
        )

        prompt = f"""
Synthesize the following research results into a coherent answer to this subproblem:

Subproblem: {subproblem}

Research Results:
{results_text}

Provide a clear, synthesized answer that combines the key insights from all sources.
"""

        result = await self.agent.run(prompt)
        return result.data

    async def synthesize_subsolutions(
        self,
        subsolutions: List[Dict[str, Any]],
        schema: ReasoningSchema,
        original_query: str,
    ) -> str:
        """
        Synthesize all subsolutions into final answer using schema structure.

        Args:
            subsolutions: Results from all subproblems
            schema: Schema used for structuring
            original_query: Original research query

        Returns:
            Final synthesized answer
        """
        if not subsolutions:
            return f"No solutions found for: {original_query}"

        # Build synthesis prompt
        subsolution_text = "\n\n".join(
            f"Subproblem: {s.get('subproblem', 'unknown')}\n"
            f"Solution: {s.get('synthesis', 'No solution')}"
            for s in subsolutions
        )

        prompt = f"""
Synthesize the following subsolutions into a comprehensive final answer.

Original Query: {original_query}

Schema: {schema.name}
{schema.description}

Subsolutions:
{subsolution_text}

Provide a final synthesized answer that:
1. Addresses the original query comprehensively
2. Follows the {schema.name} structure
3. Integrates insights from all subsolutions
4. Maintains coherence and flow
"""

        result = await self.agent.run(prompt)
        return result.data

    def _format_schema_def(self, schema_def: Dict[str, Any]) -> str:
        """Format schema definition for prompt."""
        lines = []
        for key, value in schema_def.items():
            if isinstance(value, str):
                lines.append(f"- {key}: {value}")
            elif isinstance(value, list) and value:
                lines.append(f"- {key}:")
                for item in value:
                    if isinstance(item, dict):
                        for subkey, subval in item.items():
                            lines.append(f"  - {subkey}: {subval}")
                    else:
                        lines.append(f"  - {item}")
        return "\n".join(lines)

    # Capability methods (delegate to capability adapter)
    
    @property
    def supports_embeddings(self) -> bool:
        """Whether this LLM service supports embeddings."""
        return self.capabilities.supports_embeddings

    @property
    def supports_vision(self) -> bool:
        """Whether this LLM service supports vision/image inputs."""
        return self.capabilities.supports_vision

    @property
    def supports_logprobs(self) -> bool:
        """Whether this LLM service supports log probability returns."""
        return self.capabilities.supports_logprobs

    @property
    def supports_input_params(self) -> bool:
        """Whether this LLM service supports custom input parameters."""
        return self.capabilities.supports_input_params

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            NotImplementedError: If embeddings not supported
        """
        return await self.capabilities.generate_embedding(text)

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        return await self.capabilities.generate_embeddings(texts)

    async def compute_similarity(
        self, text1: str, text2: str, use_embedding: bool = True
    ) -> float:
        """Compute semantic similarity between two texts.
        
        This method is referenced by orchestrator.py for belief alignment.
        
        Args:
            text1: First text
            text2: Second text
            use_embedding: Whether to use embeddings (if available) or fallback method
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        return await self.capabilities.compute_similarity(text1, text2, use_embedding)

    def get_vision_input_types(self) -> List[str]:
        """Get supported vision input types.
        
        Returns:
            List of supported MIME types (e.g., ['image/jpeg', 'image/png'])
        """
        return self.capabilities.get_vision_input_types()

    def get_logprob_params(self) -> Dict[str, Any]:
        """Get parameters needed for logprob requests.
        
        Returns:
            Dictionary of parameter names and their types/requirements
        """
        return self.capabilities.get_logprob_params()

    def get_custom_input_params(self) -> Dict[str, Any]:
        """Get custom input parameters supported by the provider.
        
        Returns:
            Dictionary of parameter names and their types/requirements
        """
        return self.capabilities.get_custom_input_params()

    def get_capability_info(self) -> Dict[str, Any]:
        """Get comprehensive capability information for debugging/inspection.
        
        Returns:
            Dictionary with capability flags, backend info, and parameter details
        """
        return self.capabilities.get_capability_info()

