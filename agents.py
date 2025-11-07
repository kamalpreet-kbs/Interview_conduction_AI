from langchain.agents import create_agent
from langchain.tools import tool
from pydantic import BaseModel, Field
from static import JOB_DESCRIPTION,RESUME
from schemas import *
from tools import *
import os

from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
client = OpenAI()

# # Create the agent
# Static job description and resume


doc_agent = create_agent(
    model="gpt-4o",
    tools=[analyze_document],
    response_format=DocumentAnalysis,
    system_prompt="""You are an AI Resume/Job Description Understanding Agent.
You must extract structured interview relevant information from documents."""
)

# Usage
result = doc_agent.invoke({
    "messages": [{
        "role": "user", 
        "content": f"Analyze this job description and resume:\n\nJOB DESCRIPTION:\n{JOB_DESCRIPTION}\n\nRESUME:\n{RESUME}"
    }]
})


# Access structured output
print(result["structured_response"])
# Returns DocumentAnalysis object with parsed fields

interview_planner_agent = create_agent(
    model="gpt-4o",
    tools=[plan_interview],
    response_format=InterviewPlan,
    system_prompt="""You are an expert Interview Planner Agent.

Create comprehensive interview plans based on extracted document context.
Focus on topics, difficulty level, question flow, and specific questions."""
)

plan_result = interview_planner_agent.invoke({
    "messages": [{
        "role": "user", 
        "content": f"""Create an interview plan based on this context:
        {result["structured_response"]}"""
    }]
})
print(plan_result["structured_response"])


def create_interview_agent():
    workflow = StateGraph(InterviewState)
    
    # Add nodes
    workflow.add_node("generate_question", generate_question)
    workflow.add_node("wait_for_answer", wait_for_answer)
    workflow.add_node("decide_next_action", decide_next_action)
    
    # Add edges
    workflow.add_edge(START, "generate_question")
    workflow.add_edge("generate_question", "wait_for_answer")
    workflow.add_edge("wait_for_answer", "decide_next_action")
    workflow.add_conditional_edges(
        "decide_next_action",
        should_continue,
        {
            "generate_question": "generate_question",
            "end": END
        }
    )
    
    # Compile with checkpointer (required for interrupts)
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

# Usage Example
if __name__ == "__main__":
    # Your interview plan output
    interview_plan = {
        'topics': ['Advanced Python programming', 'Django and Flask web frameworks'],
        'difficulty_level': 'Advanced',
        'question_flow': ['Introductory experience questions', 'Deep-dive technical questions'],
        'recommended_questions': ["Can you describe a complex backend system you've built?"]
    }
    
    agent = create_interview_agent()
    
    # Start interview
    config = {"configurable": {"thread_id": "interview_1"}}
    initial_state = {
        "messages": [],
        "interview_plan": interview_plan,
        "current_topic_index": 0,
        "questions_asked": 0,
        "follow_up_count": 0
    }
    
    # Run interview loop
    state = initial_state
    while True:
        result = agent.invoke(state, config)
        
        # Check if interrupted (waiting for user)
        if result.get("__interrupt__"):
            print(f"\nInterviewer: {result['messages'][-1].content}")
            user_input = input("\nYou: ")
            
            # Resume with user answer
            from langgraph.types import Command
            state = agent.invoke(
                Command(resume=user_input),
                config
            )
        else:
            # Interview ended
            print("\nInterview completed!")
            break








# from langchain.agents import create_agent
# from langchain.tools import tool
# from pydantic import BaseModel, Field
# from static import JOB_DESCRIPTION, RESUME
# import os

# # Set API key
# if "OPENAI_API_KEY" not in os.environ:
#     os.environ["OPENAI_API_KEY"] = "your-key-here"  # Use environment variable instead

# Combined schema with both document analysis AND interview plan
# class DocumentAnalysisAndInterviewPlan(BaseModel):
#     """Complete document analysis and interview plan."""
#     # Document analysis fields
#     summary: str = Field(description="Brief role or candidate summary")
#     skills: list[str] = Field(description="List of skills mentioned")
#     experience: list[str] = Field(description="Experience details")
#     projects: list[str] = Field(description="Project information")
#     keywords: list[str] = Field(description="Key terms and technologies")
#     job_focus: str = Field(description="Role focus or candidate core strength")
    
#     # Interview plan fields
#     topics: list[str] = Field(description="List of interview topics to cover")
#     difficulty_level: str = Field(description="Overall difficulty: beginner, intermediate, advanced")
#     question_flow: list[str] = Field(description="Ordered flow of question types")
#     estimated_duration: str = Field(description="Estimated interview duration")
#     recommended_questions: list[str] = Field(description="Specific interview questions")

# # Single tool for the agent
# @tool
# def analyze_and_plan(document_text: str) -> str:
#     """Analyze documents and create interview plan."""
#     return f"Analyzing: {document_text}"

# # Create ONE agent that does everything
# agent = create_agent(
#     model="gpt-4o-mini",
#     tools=[analyze_and_plan],
#     response_format=DocumentAnalysisAndInterviewPlan,
#     system_prompt="""You are an AI Interview Planning Agent.

# First, extract structured information from the job description and resume.
# Then, create a comprehensive interview plan with topics, difficulty, question flow, and specific questions."""
# )

# # Single invoke - agent does both tasks
# result = agent.invoke({
#     "messages": [{
#         "role": "user", 
#         "content": f"""Analyze this job description and resume, then create an interview plan:

# JOB DESCRIPTION:
# {JOB_DESCRIPTION}

# RESUME:
# {RESUME}"""
#     }]
# })

# # Access all results in one structured response
# print(result["structured_response"])