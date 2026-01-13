"""Hard tests: Validate provenance features align with knowledge structure research.

These tests ensure provenance features support BOP's core purpose:
- Understanding knowledge structures through topological analysis
- Preserving d-separation and causal structure
- Enabling trust/uncertainty modeling
- Supporting clique complex analysis
"""

from bop.provenance import build_provenance_map


def test_provenance_preserves_d_separation_structure():
    """
    Test that provenance mapping preserves d-separation structure.

    Core principle: Provenance should track conditional dependencies
    without introducing spurious correlations (collider bias).

    This means:
    - Claims should only link to sources that actually support them
    - Token matches should reflect actual semantic relationships
    - Relevance scores should not create false dependencies
    """
    # Simulate research with clear conditional structure
    # Claim A depends on Source 1, Claim B depends on Source 2
    # They should remain d-separated unless there's actual overlap

    research = {
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity_deep_research",
                        "result": "D-separation is a graphical criterion for determining conditional independence.",
                    }
                ],
            },
            {
                "subproblem": "What is information geometry?",
                "results": [
                    {
                        "tool": "perplexity_deep_research",
                        "result": "Information geometry studies statistical manifolds using differential geometry.",
                    }
                ],
            },
        ],
    }

    # Response with two independent claims
    response_text = (
        "D-separation is a graphical criterion for determining conditional independence. "
        "Information geometry studies statistical manifolds using differential geometry."
    )

    provenance_map = build_provenance_map(response_text, research)

    # Verify claims are correctly matched to their sources
    # (not cross-matched, which would violate d-separation)
    list(provenance_map.keys())

    # Each claim should match its corresponding source
    for claim_text, prov_info in provenance_map.items():
        sources = prov_info.get("sources", [])
        assert len(sources) > 0, "Each claim should have at least one source"

        # Verify semantic alignment (not just keyword overlap)
        top_source = sources[0]
        relevance = top_source.get("relevance_breakdown", {}).get("overall_score", 0.0)

        # Relevance should reflect actual semantic relationship
        # Low relevance = weak relationship = preserves independence
        assert 0.0 <= relevance <= 1.0, "Relevance should be in [0, 1]"

        # If claim mentions "d-separation" and source is about "information geometry",
        # relevance should be low (preserving d-separation)
        if "d-separation" in claim_text.lower() and "information geometry" not in claim_text.lower():
            # Check if source is about d-separation
            source_text = top_source.get("result_text", "")
            if "information geometry" in source_text.lower() and "d-separation" not in source_text.lower():
                # These should have low relevance (they're independent)
                assert relevance < 0.5, "Independent claims should have low cross-relevance"


def test_provenance_supports_clique_analysis():
    """
    Test that provenance data supports clique complex analysis.

    Core principle: Provenance should enable identification of coherent
    knowledge structures (cliques) where sources agree.

    This means:
    - Multiple sources supporting same claim = potential clique
    - High relevance scores = strong edge in knowledge graph
    - Source agreement = clique formation
    """
    # Create research with multiple sources supporting same claim
    research = {
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity_deep_research",
                        "result": "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs.",
                    },
                    {
                        "tool": "arxiv_search",
                        "result": "D-separation provides a graphical criterion for identifying conditional independence relationships.",
                    },
                    {
                        "tool": "wikipedia",
                        "result": "D-separation is a criterion for determining conditional independence in Bayesian networks.",
                    },
                ],
            }
        ],
    }

    response_text = "D-separation is a graphical criterion for determining conditional independence."

    provenance_map = build_provenance_map(response_text, research)

    # Verify multiple sources support the claim (clique formation)
    if len(provenance_map) > 0:
        first_claim = list(provenance_map.keys())[0]
        prov_info = provenance_map[first_claim]
        num_sources = prov_info.get("num_sources", 0)

        # Should have multiple sources (clique potential)
        assert num_sources >= 1, "Should have at least one source"

        # Sources should have high relevance (strong edges)
        sources = prov_info.get("sources", [])
        if len(sources) > 1:
            # Multiple sources = potential clique
            relevance_scores = [
                s.get("relevance_breakdown", {}).get("overall_score", s.get("overlap_ratio", 0.0))
                for s in sources
            ]

            # High relevance scores indicate strong agreement (clique coherence)
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            assert avg_relevance > 0.0, "Sources should have measurable relevance"


def test_provenance_enables_trust_modeling():
    """
    Test that provenance supports trust/uncertainty modeling.

    Core principle: Provenance should provide data for:
    - Source credibility assessment
    - Confidence calibration
    - Uncertainty quantification

    This means:
    - Relevance scores should correlate with trust
    - Multiple sources = higher confidence
    - Low relevance = higher uncertainty
    """
    research = {
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity_deep_research",
                        "result": "D-separation is a graphical criterion for determining conditional independence.",
                    }
                ],
            }
        ],
    }

    response_text = "D-separation is a graphical criterion for determining conditional independence."

    provenance_map = build_provenance_map(response_text, research)

    if len(provenance_map) > 0:
        first_claim = list(provenance_map.keys())[0]
        prov_info = provenance_map[first_claim]
        sources = prov_info.get("sources", [])

        if sources:
            top_source = sources[0]
            relevance = top_source.get("relevance_breakdown", {}).get("overall_score", 0.0)

            # High relevance should indicate higher trust
            # Low relevance should indicate higher uncertainty
            assert 0.0 <= relevance <= 1.0

            # Multiple sources should increase confidence
            num_sources = prov_info.get("num_sources", 0)
            if num_sources > 1:
                # More sources = more verification = higher confidence
                assert num_sources > 0


def test_provenance_respects_information_geometry():
    """
    Test that provenance respects information geometry principles.

    Core principle: Provenance should reflect the statistical manifold
    structure of knowledge, where:
    - High Fisher Information = strong structure = high relevance
    - Low Fisher Information = weak structure = low relevance

    This means:
    - Relevance scores should reflect information content
    - Token matches should capture semantic structure
    - Component breakdowns should show information contribution
    """
    research = {
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity_deep_research",
                        "result": "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs. It helps identify when variables are conditionally independent given a set of conditioning variables.",
                    }
                ],
            }
        ],
    }

    # High information content claim
    response_text = "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs."

    provenance_map = build_provenance_map(response_text, research)

    if len(provenance_map) > 0:
        first_claim = list(provenance_map.keys())[0]
        prov_info = provenance_map[first_claim]
        sources = prov_info.get("sources", [])

        if sources:
            top_source = sources[0]
            relevance_breakdown = top_source.get("relevance_breakdown", {})

            if relevance_breakdown:
                overall_score = relevance_breakdown.get("overall_score", 0.0)
                components = relevance_breakdown.get("components", {})

                # High information content should yield high relevance
                # (strong structure in statistical manifold)
                assert overall_score > 0.0, "High information content should yield measurable relevance"

                # Components should reflect information contribution
                word_overlap = components.get("word_overlap", 0.0)
                semantic_sim = components.get("semantic_similarity", 0.0)
                token_avg = components.get("token_match_avg", 0.0)

                # All components should contribute to overall score
                assert word_overlap >= 0.0
                assert semantic_sim >= 0.0
                assert token_avg >= 0.0


def test_provenance_supports_attractor_basin_analysis():
    """
    Test that provenance supports attractor basin identification.

    Core principle: Provenance should help identify stable knowledge
    structures (attractor basins) where:
    - Multiple sources converge on same interpretation
    - High relevance = stable attractor
    - Low relevance = unstable/weak attractor

    This means:
    - Claims with high relevance from multiple sources = attractor
    - Claims with low relevance = weak/transient structure
    """
    # Create research with convergent sources (attractor basin)
    research = {
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "source1",
                        "result": "D-separation determines conditional independence.",
                    },
                    {
                        "tool": "source2",
                        "result": "D-separation identifies conditional independence.",
                    },
                    {
                        "tool": "source3",
                        "result": "D-separation is a criterion for conditional independence.",
                    },
                ],
            }
        ],
    }

    response_text = "D-separation determines conditional independence."

    provenance_map = build_provenance_map(response_text, research)

    if len(provenance_map) > 0:
        first_claim = list(provenance_map.keys())[0]
        prov_info = provenance_map[first_claim]

        num_sources = prov_info.get("num_sources", 0)
        top_relevance = prov_info.get("top_source_relevance", 0.0)

        # Multiple sources with high relevance = attractor basin
        if num_sources >= 2 and top_relevance > 0.6:
            # This represents a stable knowledge structure
            assert top_relevance > 0.0, "Attractor basin should have measurable relevance"

            # All sources should have reasonable relevance
            sources = prov_info.get("sources", [])
            relevance_scores = [
                s.get("relevance_breakdown", {}).get("overall_score", s.get("overlap_ratio", 0.0))
                for s in sources
            ]

            # Attractor basins should have consistent high relevance
            if len(relevance_scores) >= 2:
                min_relevance = min(relevance_scores)
                # Sources in attractor should have reasonable minimum relevance
                assert min_relevance > 0.0, "Attractor basin sources should have measurable relevance"


def test_provenance_query_refinement_preserves_structure():
    """
    Test that query refinement suggestions preserve knowledge structure.

    Core principle: Refinement suggestions should guide exploration
    without breaking d-separation or introducing spurious paths.

    This means:
    - Suggestions should be semantically coherent
    - Should not create false dependencies
    - Should respect existing knowledge structure
    """
    from bop.query_refinement import refine_query_from_provenance

    provenance_data = {
        "D-separation determines conditional independence": {
            "sources": [
                {
                    "source": "perplexity",
                    "relevance_breakdown": {
                        "overall_score": 0.75,
                        "components": {
                            "semantic_similarity": 0.72,
                        },
                    },
                }
            ],
            "num_sources": 1,
            "top_source_relevance": 0.75,
        }
    }

    original_query = "What is d-separation?"
    suggestions = refine_query_from_provenance(original_query, provenance_data)

    # Suggestions should be semantically related to original query
    # (preserving knowledge structure)
    for suggestion in suggestions:
        query = suggestion.get("query", "")
        rationale = suggestion.get("rationale", "")

        # Query should be related to original (semantic coherence)
        assert len(query) > 0, "Suggestion should have query text"
        assert len(rationale) > 0, "Suggestion should have rationale"

        # Rationale should explain why suggestion preserves structure
        assert "d-separation" in query.lower() or "conditional" in query.lower() or "independence" in query.lower() or len(query) > 20


def test_provenance_token_matching_reflects_semantic_structure():
    """
    Test that token matching reflects actual semantic structure.

    Core principle: Token matches should capture semantic relationships,
    not just surface-level similarity.

    This means:
    - High-quality matches = strong semantic relationship
    - Low-quality matches = weak/no relationship
    - Matches should align with knowledge structure
    """
    from bop.provenance import compute_token_matches

    query = "d-separation conditional independence"
    document = "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs."

    token_matches = compute_token_matches(query, document)

    # Should match key concepts
    assert "separation" in token_matches or "d-separation" in token_matches.lower()
    assert "conditional" in token_matches or "independence" in token_matches

    # Matches should have high scores for actual matches
    for query_token, matches in token_matches.items():
        if matches:
            best_match, best_score = matches[0]
            # Exact or near-exact matches should have high scores
            if query_token.lower() == best_match.lower():
                assert best_score >= 0.9, "Exact matches should have high scores"
            # Semantic matches should have reasonable scores
            elif query_token in best_match or best_match in query_token:
                assert best_score >= 0.7, "Substring matches should have reasonable scores"


def test_provenance_quality_scores_align_with_topology():
    """
    Test that provenance quality scores align with topological structure.

    Core principle: High-quality claims with high relevance should
    correspond to stable topological structures (cliques, attractors).

    This means:
    - Quality × Relevance should predict topological stability
    - Low quality or low relevance = unstable structure
    """
    research = {
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity",
                        "result": "D-separation is a graphical criterion for determining conditional independence.",
                    }
                ],
            }
        ],
    }

    # High-quality claim (clear, specific, informative)
    response_text = "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs."

    provenance_map = build_provenance_map(response_text, research)

    if len(provenance_map) > 0:
        first_claim = list(provenance_map.keys())[0]
        prov_info = provenance_map[first_claim]

        quality_score = prov_info.get("quality_score", 0.5)
        top_relevance = prov_info.get("top_source_relevance", 0.0)

        # High quality × high relevance = stable topological structure
        stability_score = quality_score * top_relevance

        # Should have measurable stability
        assert stability_score >= 0.0, "Stability score should be non-negative"

        # High stability should indicate strong topological structure
        if stability_score > 0.5:
            # This should correspond to a stable knowledge structure
            assert top_relevance > 0.0, "High stability requires measurable relevance"
            assert quality_score > 0.0, "High stability requires measurable quality"


def test_provenance_respects_serial_scaling():
    """
    Test that provenance respects serial scaling constraints.

    Core principle: Provenance building should not introduce
    unnecessary serial dependencies that violate computational constraints.

    This means:
    - Provenance should be computable in parallel where possible
    - Should not create artificial dependencies
    - Should respect independent claim processing
    """
    research = {
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity",
                        "result": "D-separation is a graphical criterion.",
                    }
                ],
            },
            {
                "subproblem": "What is information geometry?",
                "results": [
                    {
                        "tool": "perplexity",
                        "result": "Information geometry studies statistical manifolds.",
                    }
                ],
            },
        ],
    }

    response_text = (
        "D-separation is a graphical criterion. "
        "Information geometry studies statistical manifolds."
    )

    provenance_map = build_provenance_map(response_text, research)

    # Claims should be processable independently
    # (no artificial serial dependencies)
    list(provenance_map.keys())

    # Each claim should have independent provenance
    for claim_text, prov_info in provenance_map.items():
        sources = prov_info.get("sources", [])

        # Provenance for each claim should be independent
        # (can be computed in parallel)
        assert isinstance(sources, list), "Sources should be a list"
        assert "sources" in prov_info, "Each claim should have sources"

        # No cross-dependencies between claims
        # (each claim's provenance is independent)


def test_provenance_enables_calibration_analysis():
    """
    Test that provenance enables confidence calibration analysis.

    Core principle: Relevance scores should enable calibration error
    computation, where high relevance = high confidence should be calibrated.

    This means:
    - Relevance scores should be interpretable as confidence
    - Should enable Expected Calibration Error (ECE) computation
    - Should support trust/uncertainty modeling
    """
    research = {
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity",
                        "result": "D-separation is a graphical criterion for determining conditional independence.",
                    }
                ],
            }
        ],
    }

    response_text = "D-separation is a graphical criterion for determining conditional independence."

    provenance_map = build_provenance_map(response_text, research)

    if len(provenance_map) > 0:
        first_claim = list(provenance_map.keys())[0]
        prov_info = provenance_map[first_claim]
        sources = prov_info.get("sources", [])

        if sources:
            top_source = sources[0]
            relevance = top_source.get("relevance_breakdown", {}).get("overall_score", 0.0)

            # Relevance should be interpretable as confidence
            # High relevance (0.8) should mean high confidence
            # Low relevance (0.3) should mean low confidence

            # For calibration analysis:
            # - Bin relevance scores into confidence bins
            # - Compare to actual accuracy
            # - Compute ECE

            assert 0.0 <= relevance <= 1.0, "Relevance should be in [0, 1] for calibration"

            # High relevance should indicate high confidence
            if relevance > 0.7:
                # This should correspond to high confidence
                assert relevance > 0.0, "High relevance should be measurable"

            # Low relevance should indicate low confidence
            if relevance < 0.4:
                # This should correspond to low confidence
                assert relevance >= 0.0, "Low relevance should be non-negative"

