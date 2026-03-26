# from langchain.agents import create_agent
# from langchain.tools import tool
# from pydantic import BaseModel, Field
# from static import JOB_DESCRIPTION,RESUME
# from langgraph.graph import StateGraph, START, END
# from schemas import *
# from tools import *
# from langgraph.types import Command
# from langgraph.types import interrupt
# from langgraph.checkpoint.memory import MemorySaver
# import os
# import logging
# # # Create the agent
# # Static job description and resume
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

# JOB_PDF_PATH = os.getenv("JOB_PDF_PATH")
# RESUME_PDF_PATH = os.getenv("RESUME_PDF_PATH")

# if not JOB_PDF_PATH or not RESUME_PDF_PATH:
#     logger.error("Both JOB_PDF_PATH and RESUME_PDF_PATH environment variables must be set to uploaded PDF paths.")
#     logger.error("Received JOB_PDF_PATH=%s RESUME_PDF_PATH=%s", JOB_PDF_PATH, RESUME_PDF_PATH)

# # Extract text using pdf_to_text from tools.py
# try:
#     job_text = pdf_to_text(JOB_PDF_PATH)
# except NameError:
#     logger.exception("pdf_to_text is not defined in tools.py - ensure tools.py exports pdf_to_text.")
# except Exception:
#     logger.exception("Unexpected error running pdf_to_text on JOB_PDF_PATH=%s", JOB_PDF_PATH)

# try:
#     resume_text = pdf_to_text(RESUME_PDF_PATH)
# except NameError:
#     logger.exception("pdf_to_text is not defined in tools.py - ensure tools.py exports pdf_to_text.")
# except Exception:
#     logger.exception("Unexpected error running pdf_to_text on RESUME_PDF_PATH=%s", RESUME_PDF_PATH)

# # Fail if extraction produced no text
# if not job_text or not job_text.strip():
#     logger.error("Failed to extract any text from job PDF at: %s", JOB_PDF_PATH)

# if not resume_text or not resume_text.strip():
#     logger.error("Failed to extract any text from resume PDF at: %s", RESUME_PDF_PATH)

# doc_agent = create_agent(
#     model="gpt-4o",
#     tools=[analyze_document],
#     response_format=DocumentAnalysis,
#     system_prompt="""You are an AI Resume/Job Description Understanding Agent.
# You must extract structured interview relevant information from documents.
# Generate the data in the valid json only don't write anything outside the json"""
# )

# # Usage
#   result = doc_agent.invoke({
#     "messages": [{
#         "role": "user", 
#         "content": f"Analyze this job description and resume:\n\nJOB DESCRIPTION:\n{job_text}\n\nRESUME:\n{resume_text}"
#     }]
# })


# # Access structured output
# print(result["structured_response"])
# # Returns DocumentAnalysis object with parsed fields

# interview_planner_agent = create_agent(
#     model="gpt-4o",
#     tools=[plan_interview],
#     response_format=InterviewPlan,
#     system_prompt="""You are an expert Interview Planner Agent.

# Create comprehensive interview plans based on extracted document context.
# Focus on topics, difficulty level, question flow, and specific questions."""
# )

# plan_result = interview_planner_agent.invoke({
#     "messages": [{
#         "role": "user", 
#         "content": f"""Create an interview plan based on this context:
#     {result["structured_response"]}"""
#     }]
# })
# print(plan_result["structured_response"])
    

# def create_interview_agent():
#     workflow = StateGraph(InterviewState)
    
#     # Add nodes
#     workflow.add_node("generate_question", generate_question)
#     workflow.add_node("wait_for_answer", wait_for_answer)
#     workflow.add_node("decide_next_action", decide_next_action)
    
#     # Add edges
#     workflow.add_edge(START, "generate_question")
#     workflow.add_edge("generate_question", "wait_for_answer")
#     workflow.add_edge("wait_for_answer", "decide_next_action")
#     workflow.add_conditional_edges(
#         "decide_next_action",
#         should_continue,
#         {
#             "generate_question": "generate_question",
#             "end": END
#         }
#     )
    
#     # Compile with checkpointer (required for interrupts)
#     checkpointer = MemorySaver()
#     return workflow.compile(checkpointer=checkpointer)

# # Usage Example
# if __name__ == "__main__":
#     # Your interview plan output
#     interview_plan = plan_result["structured_response"].model_dump()
    
#     agent = create_interview_agent()
    
#     # Start interview
#     config = {"configurable": {"thread_id": "interview_1"}}
#     initial_state = {
#         "messages": [],
#         "interview_plan": interview_plan,
#         "current_topic_index": 0,
#         "questions_asked": 0,
#         "is_follow_up": False
#     }
    
#     # Run interview loop
#     state = initial_state
#     while True:
#         result = agent.invoke(state, config)
        
#         # Check if interrupted (waiting for user)
#         if result.get("__interrupt__"):
#             print(f"\nInterviewer: {result['messages'][-1].content}")
#             user_input = input("\nYou: ")
            
#             state = agent.invoke(Command(resume=user_input),config)
#             if state.get("questions_asked",0)>=12:
#                 print("\nInterview completed!!")
#                 break
#             # # Resume with user answer
#             # from langgraph.types import Command
#             # state = agent.invoke(
#             #     Command(resume=user_input),
#             #     config
#             # )
#             # # Check if interview should end after resuming
#             # current_idx = state.get("current_topic_index", 0)
#             # questions_asked = state.get("questions_asked", 0)
#             # total_topics = len(interview_plan["topics"])
            
#             # if current_idx >= total_topics or questions_asked >= 13:
#             #     print("Total topics:->",total_topics)
#             #     # print("\nInterview completed!")
#             #     print(f"Final stats - Topics: {current_idx}, Questions: {questions_asked}")
#             #     break
            
#         else:
#             # Interview ended naturally
#             print("\nInterview completed!")
#             break

from langchain.agents import create_agent
from langchain.tools import tool
from pydantic import BaseModel, Field
from static import JOB_DESCRIPTION, RESUME
from langgraph.graph import StateGraph, START, END
from schemas import *
from tools import *
from langgraph.types import Command
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver
import os
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# Define Agents (Stateless definitions can remain global)
doc_agent = create_agent(
    model="gpt-4o",
    tools=[analyze_document],
    response_format=DocumentAnalysis,
    system_prompt="""You are an AI Resume/Job Description Understanding Agent.
You must extract structured interview relevant information from documents.
**Generate the data in the valid json only don't write anything outside the json**"""
)
interview_planner_agent = create_agent(
    model="gpt-4o",
    tools=[plan_interview],
    response_format=InterviewPlan,
    system_prompt="""You are an expert Interview Planner Agent.
Create comprehensive interview plans based on extracted document context.
Focus on topics, difficulty level, question flow, and specific questions."""
)
def generate_interview_plan(job_pdf_path: str, resume_pdf_path: str):
    """
    Dynamically processes the given PDF paths and returns the interview plan.
    """
    logger.info(f"Generating plan for Job: {job_pdf_path}, Resume: {resume_pdf_path}")
    # Extract text using pdf_to_text from tools.py
    try:
        job_text = pdf_to_text(job_pdf_path)
    except Exception as e:
        logger.exception("Error reading Job PDF")
        job_text = ""
    try:
        resume_text = pdf_to_text(resume_pdf_path)
    except Exception as e:
        logger.exception("Error reading Resume PDF")
        resume_text = ""
    # Fail if extraction produced no text
    if not job_text.strip() or not resume_text.strip():
        logger.error("Failed to extract text from one or both PDFs.")
        raise ValueError("Could not extract text from uploaded PDFs.")
    # 1. Analyze Documents
    result = doc_agent.invoke({
        "messages": [{
            "role": "user", 
            "content": f"Analyze this job description and resume:\n\nJOB DESCRIPTION:\n{job_text}\n\nRESUME:\n{resume_text}"
        }]
    })
    # Access structured output
    analysis_data = result["structured_response"]
    print("Document Analysis:", analysis_data)
    # 2. Plan Interview
    plan_result = interview_planner_agent.invoke({
        "messages": [{
            "role": "user", 
            "content": f"""Create an interview plan based on this context:
        {analysis_data}"""
        }]
    })
    
    return {
        "analysis": analysis_data,
        "plan": plan_result["structured_response"]
    }
def create_interview_agent():
    workflow = StateGraph(InterviewState)
    
    # Add nodes
    workflow.add_node("generate_question", generate_question)
    workflow.add_node("wait_for_answer", wait_for_answer)
    workflow.add_node("decide_next_action", decide_next_action)
    workflow.add_node("wrap_up", wrap_up)
    
    # Add edges
    workflow.add_edge(START, "generate_question")
    workflow.add_edge("generate_question", "wait_for_answer")
    workflow.add_edge("wait_for_answer", "decide_next_action")
    workflow.add_conditional_edges(
        "decide_next_action",
        should_continue,
        {
            "generate_question": "generate_question",
            "end": "wrap_up"
        }
    )
    workflow.add_edge("wrap_up", END)
    
    # Compile with checkpointer (required for interrupts)
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)
# Usage Example for CLI testing
if __name__ == "__main__":
    # Example usage if running directly
    # You would need to provide valid paths here to test
    job_path = os.getenv("JOB_PDF_PATH", "path/to/job.pdf")
    resume_path = os.getenv("RESUME_PDF_PATH", "path/to/resume.pdf")
    
    try:
        plan = generate_interview_plan(job_path, resume_path)
        print("Generated Plan:", plan.model_dump())
    except Exception as e:
        print(f"Error: {e}")