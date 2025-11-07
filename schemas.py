from pydantic import BaseModel, Field 
from typing import Optional
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain.chat_models import init_chat_model
import operator



# Define the structured output schema
class DocumentAnalysis(BaseModel):
    """Structured interview context extracted from documents."""
    summary: str = Field(description="Brief role or candidate summary")
    skills: list[str] = Field(description="List of skills mentioned")
    experience: list[str] = Field(description="Experience details")
    projects: list[str] = Field(description="Project information")
    keywords: list[str] = Field(description="Key terms and technologies")
    job_focus: str = Field(description="Role focus or candidate core strength")

class InterviewPlan(BaseModel):
    """Structured interview plan with topics, difficulty, and question flow."""
    topics: list[str] = Field(description="List of interview topics to cover")
    difficulty_level: str = Field(description="Overall difficulty: beginner, intermediate, advanced")
    question_flow: list[str] = Field(description="Ordered flow of question types")
    estimated_duration: str = Field(description="Estimated interview duration")
    recommended_questions: list[str] = Field(description="Specific interview questions")
    
class InterviewState(TypedDict):
    messages: Annotated[list, "conversation history"]
    interview_plan: dict  # Output from interview_planner_agent
    current_topic_index: int
    questions_asked: int
    follow_up_count: int  # Track follow-ups on current answer
