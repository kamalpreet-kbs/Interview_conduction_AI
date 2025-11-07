from langchain.tools import tool
from schemas import InterviewState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt
from typing import TypedDict, Annotated, Literal
from langchain.chat_models import init_chat_model

from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
client = OpenAI()

model = init_chat_model("gpt-4o")

# Define the document analysis tool
@tool
def analyze_document(document_text: str) -> str:
    """Extract interview context from resume or job description."""
    return f"Analyzing document: {document_text}"

@tool
def plan_interview(context: str) -> str:
    """Create interview plan based on extracted context and write at most 7 topics and 7 recomended questions."""
    return f"Planning interview based on: {context}"


# Node 1: Question Generator
def generate_question(state: InterviewState) -> dict:
    """you can ask total 2 questions including new and follow up questions"""
    """Generate next question based on context"""
    plan = state["interview_plan"]
    messages = state["messages"]
    current_idx = state.get("current_topic_index", 0)
    follow_up_count = state.get("follow_up_count", 0)
    
    # Build context for question generation
    system_prompt = f"""You are conducting a technical interview.
    
Interview Plan:
- Topics: {plan['topics']}
- Difficulty: {plan['difficulty_level']}
- Question Flow: {plan['question_flow']}
- Recommended Questions: {plan['recommended_questions']}

Current Topic: {plan['topics'][current_idx] if current_idx < 2 else 'Wrap up'}
Follow-up count on current answer: {follow_up_count}

Rules:
1. You can ask total 2 questions including new and follow up questions
1. If follow_up_count < 1 and last answer needs clarification, ask a follow-up question
2. Otherwise, move to next topic from the plan
3. Keep questions relevant to candidate's experience level
4. Be conversational and professional
"""
    
    # Get last few messages for context
    recent_context = messages[-4:] if len(messages) > 4 else messages
    
    response = model.invoke([
        SystemMessage(content=system_prompt),
        *recent_context,
        HumanMessage(content="Generate the next interview question.")
    ])
    
    return {
        "messages": [AIMessage(content=response.content)]
    }

# Node 2: Wait for User Answer
def wait_for_answer(state: InterviewState) -> dict:
    """Pause and wait for user input"""
    user_answer = interrupt("Please provide your answer:")
    
    return {
        "messages": [HumanMessage(content=user_answer)],
        "questions_asked": state.get("questions_asked", 0) + 1
    }

# Node 3: Decide Next Action
def decide_next_action(state: InterviewState) -> dict:
    """Analyze answer and decide: follow-up or next topic"""
    messages = state["messages"]
    plan = state["interview_plan"]
    follow_up_count = state.get("follow_up_count", 0)
    current_idx = state.get("current_topic_index", 0)
    
    # Get last Q&A pair
    last_question = messages[-2].content if len(messages) >= 2 else ""
    last_answer = messages[-1].content
    
    decision_prompt = f"""Analyze this interview exchange:

Question: {last_question}
Answer: {last_answer}

Current topic: {plan['topics'][current_idx] if current_idx < len(plan['topics']) else 'Done'}
Follow-ups asked: {follow_up_count}

Decide:
- "follow_up" if answer needs clarification and follow_up_count < 1
- "next_topic" if answer is complete or follow_up_count >= 1

Return ONLY: follow_up or next_topic
"""
    
    response = model.invoke([SystemMessage(content=decision_prompt)])
    decision = response.content.strip().lower()
    
    if "follow_up" in decision and follow_up_count < 1:
        return {
            "follow_up_count": follow_up_count + 1
        }
    else:
        # Move to next topic
        return {
            "current_topic_index": current_idx + 1,
            "follow_up_count": 0
        }

# Conditional Edge: Check if interview should continue
def should_continue(state: InterviewState) -> Literal["generate_question", "end"]:
    """Check if we should continue or end interview"""
    current_idx = state.get("current_topic_index", 0)
    questions_asked = state.get("questions_asked", 0)
    total_topics = len(state["interview_plan"]["topics"])
    
    # End conditions
    if current_idx >= total_topics or questions_asked >= 10:
        return "end"
    return "generate_question"