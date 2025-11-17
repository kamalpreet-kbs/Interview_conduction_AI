from langchain.tools import tool
from schemas import InterviewState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt
from typing import Literal
from langchain.chat_models import init_chat_model

from dotenv import load_dotenv
load_dotenv()

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
    """Generate next question based on context"""
    plan = state["interview_plan"]
    messages = state["messages"]
    questions_asked = state.get("questions_asked", 0)
    current_topic_idx = state.get("current_topic_index", 0)
    is_follow_up = state.get("is_follow_up", False)
    
    # Question 1: Introduction
    if questions_asked == 0:
        system_prompt = """You are conducting an interview.
        Ask an introductory question like 'Tell me about yourself'."""
        
        # Questions 2-11: Topic-based
    elif 1 <= questions_asked <= 10:
        # Check if we need a follow-up
        if is_follow_up and len(messages) >= 2:
            last_answer = messages[-1].content
            system_prompt = f"""The candidate's previous answer was unsatisfactory.
            Ask ONE follow-up question to clarify or get more details.
            Previous answer: {last_answer}"""
        else:
            # Move to next topic
            current_topic = plan['topics'][current_topic_idx] if current_topic_idx < len(plan['topics']) else plan['topics'][-1]
            system_prompt = f"""You are conducting a technical interview.
            
            Current Topic: {current_topic}
            All Topics:{plan['topics']}
            Recommended Questions: {plan['recommended_questions']}
            
            Ask a relevant question based on the current topic."""
    # Question 12: HR question
    else:
        system_prompt = """You are wrapping up the interview.
        Ask a final HR-style question (e.g., salary expectations, availability, questions for us).
        Be professional and friendly."""
    
    recent_context = messages[-4:] if len(messages) > 4 else messages
    response = model.invoke([
        SystemMessage(content=system_prompt),
        *recent_context,
        HumanMessage(content="Generate the next interview question.")
    ])
    
    return {"messages": [AIMessage(content=response.content)]}


# Node 2: Wait for User Answer
def wait_for_answer(state: InterviewState) -> dict:
    """Pause and wait for user input"""
    user_answer = interrupt("Please provide your answer:")
    is_follow_up = state.get("is_follow_up",False)
    
    new_count = state.get("questions_asked", 0) if is_follow_up else state.get("questions_asked", 0) + 1
     
    return {
        "messages": [HumanMessage(content=user_answer)],
        "questions_asked": new_count
    }

# Node 3: Decide Next Action
def decide_next_action(state: InterviewState) -> dict:
    """Analyze answer and decide: follow-up or next topic"""
    messages = state["messages"]
    plan = state["interview_plan"]
    current_idx = state.get("current_topic_index", 0)
    is_follow_up = state.get("is_follow_up", 0)
    question_asked = state.get("question_asked",0)
    
    # Skip decision for intro (Q1) and HR (Q12)
    questions_asked = state.get("questions_asked", 0)
    if questions_asked == 0 or questions_asked >= 11:
        return {"is_follow_up": False}
    
    # If already asked follow-up, move to next topic
    if is_follow_up:
        return {
            "current_topic_index": current_idx + 1,
            "is_follow_up": False
        }
    
    # Get last Q&A pair
    last_question = messages[-2].content if len(messages) >= 2 else ""
    last_answer = messages[-1].content
    
    decision_prompt = f"""Analyze this interview exchange:

Question: {last_question}
Answer: {last_answer}

Current topic: {plan['topics'][current_idx] if current_idx < len(plan['topics']) else 'Done'}

Is the answer satisfactory? Decide:
- "follow_up" if answer is incomplete,vague, or need clarification
- "next_topic" if answer is complete and satisfactory

Return ONLY: follow_up or next_topic
"""
    
    response = model.invoke([SystemMessage(content=decision_prompt)])
    decision = response.content.strip().lower()
    
    if "follow_up" in decision:
        return {
            "is_follow_up":True
        }
    else:
        # Move to next topic
        return {
            "current_topic_index": current_idx + 1,
            "is_follow_up": False
        }
# def decide_next_action(state: InterviewState) -> dict:
#     """Move to next question (no follow-ups)"""
#     return {}

def should_continue(state: InterviewState) -> Literal["generate_question", "end"]:
    """End after 12 questions"""
    questions_asked = state.get("questions_asked", 0)
    current_topic_index = state.get("current_topic_index",0)
    print("Topic index is :--->",current_topic_index)
    
    if questions_asked >= 12:
        print(f"Interview complete! Total questions: {questions_asked}")
        return "end"
    else:
        return "generate_question"

# def should_continue(state: InterviewState) -> Literal["generate_question", "end"]:
#     """Check if we should continue or end interview"""
#     current_idx = state.get("current_topic_index", 0)
#     questions_asked = state.get("questions_asked", 0)
#     total_topics = len(state["interview_plan"]["topics"])
#     print("your current_idx is: ----->", current_idx)
#     print("your questions_asked is: ----->", questions_asked)
#     print("your total_topics is: ----->", total_topics)
#     # End conditions - changed to > 10
#     if current_idx > 10 or questions_asked > 10 or current_idx >= total_topics:
#         return "end"
#     return "generate_question"