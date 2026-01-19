use bop_agent_core::llm::{LlmClient, LlmProvider, Message};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct QualityScore {
    pub groundedness: f32, // 0-1: Are claims supported by context?
    pub utility: f32,      // 0-1: Does it answer the user's question?
    pub coherence: f32,    // 0-1: Is the reasoning logical?
    pub feedback: String,
}

pub struct EvaluationJudge {
    client: LlmClient,
}

impl EvaluationJudge {
    pub fn new(client: LlmClient) -> Self {
        Self { client }
    }

    pub async fn evaluate_response(
        &self,
        query: &str,
        context: &str,
        response: &str,
    ) -> anyhow::Result<QualityScore> {
        let system_prompt = r#"You are an expert judge of AI RAG (Retrieval-Augmented Generation) quality.
Evaluate the AI's response based on the provided query and context.
Output your evaluation ONLY as a JSON object with the following fields:
- groundedness: float (0.0 to 1.0)
- utility: float (0.0 to 1.0)
- coherence: float (0.0 to 1.0)
- feedback: string (brief explanation of scores)

Evaluation Criteria:
1. Groundedness: Are the facts in the response directly supported by the context?
2. Utility: Does the response fully address the user's query?
3. Coherence: Is the response easy to read and logically sound?
"#;

        let user_msg = format!(
            "Query: {}\n\nContext: {}\n\nResponse: {}",
            query, context, response
        );

        let messages = vec![
            Message::system(system_prompt),
            Message::user(user_msg),
        ];

        let result = self.client.complete(&messages).await?;
        
        // Find JSON block if LLM adds markdown formatting
        let json_str = if let Some(start) = result.find('{') {
            if let Some(end) = result.rfind('}') {
                &result[start..=end]
            } else {
                &result
            }
        } else {
            &result
        };

        let score: QualityScore = serde_json::from_str(json_str)?;
        Ok(score)
    }
}

#[tokio::test]
async fn test_rag_quality_invariant() -> anyhow::Result<()> {
    // Only run if API keys are present
    let provider = match LlmProvider::auto(None) {
        Ok(p) => p,
        Err(_) => {
            println!("Skipping LLM-as-Judge test (no API keys)");
            return Ok(());
        }
    };
    
    let client = LlmClient::new(provider);
    let judge = EvaluationJudge::new(client);

    // Test Case: High Quality
    let query = "What is the capital of France?";
    let context = "Paris is the capital and most populous city of France.";
    let response = "The capital of France is Paris.";

    let score = judge.evaluate_response(query, context, response).await?;
    println!("Evaluation Score (Good): {:?}", score);
    
    assert!(score.groundedness > 0.8);
    assert!(score.utility > 0.8);

    // Test Case: Hallucination (Low Groundedness)
    let query = "What is the population of Paris?";
    let context = "Paris is the capital of France.";
    let response = "Paris has a population of 10 million people."; // Not in context

    let score = judge.evaluate_response(query, context, response).await?;
    println!("Evaluation Score (Hallucination): {:?}", score);
    
    assert!(score.groundedness < 0.5, "Hallucination should have low groundedness");

    Ok(())
}
