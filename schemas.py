from pydantic import BaseModel, Field
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


# Models
class UserMessage(BaseModel):
    text: str
    thread_id: str
    

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
    messages: Annotated[list, add_messages]
    interview_plan: dict  # Output from interview_planner_agent
    current_topic_index: int
    questions_asked: int
    is_follow_up:bool  # Track follow-ups on current answer
