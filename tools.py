from langchain.tools import tool
from schemas import InterviewState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt
from typing import Literal, Optional
from langchain.chat_models import init_chat_model
from pathlib import Path
import logging
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
load_dotenv()
import logging
try:
    from PIL import Image
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
logger = logging.getLogger(__name__)

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
    
    new_count = state.get("questions_asked", 0) 
     
    return {
        "messages": [HumanMessage(content=user_answer)],
        "questions_asked": new_count + 1
    }

# Node 3: Decide Next Action
def decide_next_action(state: InterviewState) -> dict:
    """Analyze answer and decide: follow-up or next topic"""
    messages = state["messages"]
    plan = state["interview_plan"]
    current_idx = state.get("current_topic_index", 0)
    is_follow_up = state.get("is_follow_up", 0)
    
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

def pdf_to_text(pdf_path: str) -> str:
    """
    Extracts text from a PDF file. 
    First attempts standard extraction using PyPDFLoader.
    If that yields empty or very little text, attempts OCR using pytesseract.
    
    Args:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        str: Extracted text from the PDF.
    """
    path = Path(pdf_path)
    if not path.exists() or not path.is_file():
        logger.error(f"pdf_to_text: File not found at {pdf_path}")
        return ""

    text = ""
    
    # 1. Try standard text extraction first (fast)
    try:
        logger.info(f"Attempting standard text extraction for {pdf_path}")
        loader = PyPDFLoader(str(path))
        docs = loader.load()
        text = "\n\n".join(d.page_content for d in docs if d.page_content)
    except Exception as e:
        logger.warning(f"Standard extraction failed: {e}")

    # 2. Check if we need OCR
    # If text is empty or very short (likely scanned image), try OCR
    if not text or len(text.strip()) < 50:
        if OCR_AVAILABLE:
            logger.info("Text content low/empty. Attempting OCR...")
            try:
                # Convert PDF pages to images
                # poppler_path must be in PATH or specified
                images = convert_from_path(str(path))
                
                ocr_text_list = []
                for i, image in enumerate(images):
                    page_text = pytesseract.image_to_string(image)
                    ocr_text_list.append(f"--- Page {i+1} ---\n{page_text}")
                
                text = "\n\n".join(ocr_text_list)
                logger.info("OCR successfully extracted text.")
                
            except Exception as e:
                logger.error(f"OCR Failed: {e}. Ensure poppler and tesseract are installed.")
                if not text: # If we had no text and OCR failed, return error message or empty
                    return ""
        else:
            logger.warning("OCR libraries (pdf2image, pytesseract, Pillow) not installed. Skipping OCR.")
            
    return text

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