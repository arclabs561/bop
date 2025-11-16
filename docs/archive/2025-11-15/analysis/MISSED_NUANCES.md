# Missed Nuances Analysis

## Overview

This document identifies nuances from the "How to display knowledge well?" research document that we may have missed or could improve further.

## Critical Nuances We May Have Missed

### 1. **Agency Preservation in Adaptive Interfaces**

**What the Document Says**:
> "Adaptive interfaces shouldn't just reduce load, they must preserve worker agency and sense of control. Auto-simplifying during fatigue risks making workers feel infantilized rather than supported."

**What We Implemented**:
- Context-dependent adaptation adjusts response length automatically
- No explicit user choice/consent mechanism

**What's Missing**:
- **User consent for adaptation**: We should offer choice: "You seem to be exploring this topic—would you like more detail, or keep it concise?"
- **Override mechanism**: User should be able to say "always give me full details" or "always give me summaries"
- **Adaptation transparency**: We don't explain WHY we're adapting (e.g., "Detected similar queries, increasing detail level")

**Recommendation**: Add user preference settings and explicit adaptation prompts.

### 2. **Metacognitive Blindness Warnings**

**What the Document Says**:
> "People are metacognitively blind to noise arising when integrating multiple pieces of evidence—they trust their judgments about visualizations more than they should."

**What We Implemented**:
- Calibration error display with explanation
- Verification counts

**What's Missing**:
- **Explicit warnings**: "Your confidence in this information may be higher than warranted"
- **Overconfidence detection**: When multiple sources agree, warn about false confidence
- **Judgment quality indicators**: Help users recognize when they're over-trusting

**Recommendation**: Add explicit metacognitive warnings when confidence is high but evidence is limited.

### 3. **Task/Goal Detection**

**What the Document Says**:
> "People prioritize information that directly enables their current task, not comprehensive coverage."

**What We Implemented**:
- Context-dependent adaptation based on topic similarity
- Response length adaptation

**What's Missing**:
- **Explicit task detection**: We don't detect if user wants "quick lookup" vs "deep research"
- **Goal-oriented filtering**: We don't filter information by what enables the task
- **Task context tracking**: We don't track what task the user is trying to accomplish

**Recommendation**: Add task/goal detection from query patterns and user behavior.

### 4. **Exploration vs Extraction Mode Detection**

**What the Document Says**:
> "In exploratory research contexts, viewers want interactive layers... But in persuasive or explanatory contexts, audiences prefer streamlined presentations."

**What We Implemented**:
- Topic similarity-based adaptation (similar = exploration, different = extraction)
- This is a heuristic, not explicit mode detection

**What's Missing**:
- **Explicit mode detection**: User should be able to specify "explore" vs "extract"
- **Mode-specific UI**: Exploration mode should show interactive filters, extraction should show focused summaries
- **Behavioral mode detection**: Detect from interaction patterns (rapid queries = extraction, sustained engagement = exploration)

**Recommendation**: Add explicit mode selection and behavioral detection.

### 5. **Temporal Knowledge Evolution**

**What the Document Says**:
> "Tools showing how understanding of a topic has changed over time—which claims gained consensus, which became contested, what new evidence emerged."

**What We Implemented**:
- Session tracking exists
- No temporal knowledge evolution tracking

**What's Missing**:
- **Claim tracking over time**: Track how consensus on specific claims changes
- **Knowledge timeline**: Show "This claim had 0.8 consensus last week, now 0.6"
- **Evidence evolution**: Track when new evidence emerges that changes understanding

**Recommendation**: Add temporal tracking of claims and consensus across sessions.

### 6. **Context-Dependent Value Representation**

**What the Document Says**:
> "The same visualization will be interpreted differently depending on what else viewers have recently seen, what alternatives they're comparing, and whether they're in a high or low value context."

**What We Implemented**:
- Recent query tracking
- Topic similarity computation

**What's Missing**:
- **Comparison context**: We don't track what alternatives user is comparing
- **Value context**: We don't detect high vs low value contexts
- **Recent exposure tracking**: We track queries but not what information was shown

**Recommendation**: Track what information was displayed, not just what was queried.

### 7. **Source Diversity Emphasis**

**What the Document Says**:
> "Agreement across different source types" is important for consensus.

**What We Implemented**:
- Source diversity metric in cliques
- Verification counts

**What's Missing**:
- **Explicit diversity warnings**: "This consensus comes from 3 sources, but all are the same type (academic papers)"
- **Diversity scoring**: Separate score for source type diversity vs count
- **Diversity recommendations**: "Consider checking news sources for a different perspective"

**Recommendation**: Add explicit source diversity scoring and warnings.

### 8. **Belief-Evidence Consistency Display**

**What the Document Says**:
> "When evidence aligns with prior beliefs, uncertainty communication can reduce trust. When evidence contradicts prior beliefs, uncertainty communication can increase trust."

**What We Implemented**:
- Belief extraction and alignment computation
- Alignment stored in nodes

**What's Missing**:
- **Explicit alignment display**: We show beliefs but not how evidence aligns/contradicts
- **Trust adjustment explanation**: We don't explain how alignment affects trust interpretation
- **Contradiction warnings**: "This contradicts your earlier statement that X"

**Recommendation**: Add explicit alignment display and contradiction warnings.

### 9. **Calibration Error Interpretation**

**What the Document Says**:
> Calibration must align with actual accuracy. Over-confidence and under-confidence are problems.

**What We Implemented**:
- Calibration error computation and display
- Explanation of what it means

**What's Missing**:
- **Actionable guidance**: "Calibration error of 0.15 means trust scores are off by ~15%—be cautious"
- **Historical calibration**: Track calibration over time
- **Calibration improvement suggestions**: "To improve calibration, we need more feedback"

**Recommendation**: Add actionable calibration guidance and historical tracking.

### 10. **Co-Construction vs Validation Chains**

**What the Document Says**:
> "Human and AI co-construct understanding through iterative exchange" rather than "AI builds, human validates."

**What We Implemented**:
- Sequential: AI generates, user receives
- No iterative co-construction

**What's Missing**:
- **Iterative refinement**: User should be able to say "expand on X" or "I disagree with Y"
- **Constraint learning**: System should learn user constraints in real-time
- **Co-construction interface**: Interactive back-and-forth rather than one-shot responses

**Recommendation**: This is a larger architectural change—consider for future version.

### 11. **Emotional and Physical State Factors**

**What the Document Says**:
> "Cognitive performance with visualizations degrades under stress, fatigue, divided attention, or time pressure."

**What We Implemented**:
- No state detection
- No fatigue monitoring

**What's Missing**:
- **Fatigue detection**: Track interaction patterns (slow responses, repetitive queries)
- **State-adaptive presentation**: Simplify during detected fatigue
- **Break suggestions**: "You've been working for 30 minutes—consider a break"

**Recommendation**: Add behavioral monitoring for fatigue detection (future feature).

### 12. **Personalized Cognitive Style Adaptation**

**What the Document Says**:
> "Individual characteristics like prior knowledge, cognitive style, spatial ability, and domain familiarity fundamentally alter what viewers extract from identical visualizations."

**What We Implemented**:
- Generic adaptation
- No personalization

**What's Missing**:
- **User profile**: Track user's cognitive style, expertise level
- **Personalized presentation**: Adapt to user's preferred style
- **Learning from preferences**: Learn what presentation style works for each user

**Recommendation**: Add user profile and personalization (future feature).

### 13. **Visual Fallback for Text-Heavy Users**

**What the Document Says**:
> "Some users fundamentally distrust visual communication regardless of quality. Adaptive systems need text-heavy fallback options."

**What We Implemented**:
- CLI is text-based
- Web UI uses text with some formatting

**What's Missing**:
- **Visual preference detection**: Detect if user prefers text vs visual
- **Text-only mode**: Option to disable all visual elements
- **Accessibility**: Ensure text alternatives for all visual information

**Recommendation**: Add user preference for text-only mode.

### 14. **Interaction Pattern Analysis**

**What the Document Says**:
> "Track not just time-on-page but interaction patterns—are users exploring different views (high engagement) or repeatedly checking the same area (confusion)?"

**What We Implemented**:
- No interaction tracking
- No pattern analysis

**What's Missing**:
- **Interaction logging**: Track what users click, expand, ignore
- **Pattern detection**: Detect exploration vs confusion patterns
- **Adaptive help**: Offer help when confusion patterns detected

**Recommendation**: Add interaction tracking and pattern analysis (future feature).

### 15. **Belief Prior Distribution Tracking**

**What the Document Says**:
> "Track prior belief distributions per agent" for proper belief-evidence consistency.

**What We Implemented**:
- Simple belief extraction (text matching)
- No distribution tracking

**What's Missing**:
- **Belief strength**: Track how strongly user holds beliefs
- **Belief distribution**: Track probability distributions, not just point beliefs
- **Bayesian updating**: Proper Bayesian belief updating

**Recommendation**: Enhance belief tracking with strength and distributions (future enhancement).

## Summary of Priorities

### High Priority (Should Implement Soon)
1. Agency preservation with user consent
2. Explicit alignment display and contradiction warnings
3. Source diversity warnings
4. Task/goal detection
5. Calibration actionable guidance

### Medium Priority (Nice to Have)
6. Exploration vs extraction mode selection
7. Temporal knowledge evolution
8. Metacognitive warnings
9. Context-dependent value tracking

### Low Priority (Future Enhancements)
10. Co-construction interface
11. Emotional state detection
12. Personalized cognitive style
13. Interaction pattern analysis
14. Belief distribution tracking

