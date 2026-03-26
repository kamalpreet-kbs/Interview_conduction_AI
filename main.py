# from fastapi import FastAPI
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from agents import create_interview_agent, plan_result
# from langgraph.types import Command
# from elevenlabs import ElevenLabs
# from schemas import UserMessage
# import base64

# # -------------------------
# # FastAPI Setup
# # -------------------------
# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
# )

# # -------------------------
# # AI + TTS Clients  
# # -------------------------
# eleven = ElevenLabs(api_key="sk_e01de8d3124d5dd55daedcccf8f475da2214bf9ece0410bc")

# # -------------------------
# # Interview agent load
# # -------------------------
# agent = create_interview_agent()

# # Session states stored in-memory
# THREAD_STATES = {}

# # Pre-extracted interview plan from your agents.py
# INTERVIEW_PLAN = plan_result["structured_response"].model_dump()


# # -------------------------
# # /ask endpoint
# # -------------------------
# @app.post("/ask")
# def ask(user_msg: UserMessage):
#     user_text = user_msg.text
#     thread_id = user_msg.thread_id

#     # Initialize state for new thread
#     if thread_id not in THREAD_STATES:
#         THREAD_STATES[thread_id] = {
#             "messages": [],
#             "interview_plan": INTERVIEW_PLAN,
#             "current_topic_index": 0,
#             "questions_asked": 0,
#             "is_follow_up": False
#         }

#     state = THREAD_STATES[thread_id]

#     # Case 1 — This is the FIRST USER MESSAGE (start interview)
#     if state["messages"] == []:
#         print("\n🎤 Starting interview...")
#         result = agent.invoke(state, {"configurable": {"thread_id": thread_id}})
#     else:
#         # Case 2 — Continue existing conversation
#         print("\n➡️ Resuming agent with user input...")
#         result = agent.invoke(
#             Command(resume=user_text),
#             {"configurable": {"thread_id": thread_id}}
#         )

#     # AI generated message
#     ai_text = result["messages"][-1].content
#     print("AI message",ai_text)
#     # Save state back
#     THREAD_STATES[thread_id] = result

#     # Generate TTS audio
#     audio = eleven.text_to_speech.convert(
#         text=ai_text,
#         model_id="eleven_multilingual_v2",
#         voice_id="EXAVITQu4vr4xnSDxMaL"
#     )
#     audio_bytes = b"".join(audio)
#     audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
#     # Return JSON + audio as base64
#     return JSONResponse({
#         "user_text": user_text,
#         "ai_text": ai_text,
#         "audio_base64": audio_base64
#     })

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)


# # from fastapi import FastAPI
# # from fastapi.responses import JSONResponse
# # from fastapi.middleware.cors import CORSMiddleware
# # from agents import create_interview_agent, plan_result
# # from langgraph.types import Command
# # from schemas import UserMessage
# # import os
# # import base64

# # # -------------------------
# # # FastAPI Setup
# # # -------------------------
# # app = FastAPI()
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"], 
# #     allow_methods=["*"], 
# #     allow_headers=["*"]
# # )

# # # -------------------------
# # # Interview agent load
# # # -------------------------
# # agent = create_interview_agent()

# # # Session states stored in-memory
# # THREAD_STATES = {}

# # # Pre-extracted interview plan from your agents.py
# # INTERVIEW_PLAN = plan_result["structured_response"].model_dump()

# # print("🚀 Interview System Ready!")
# # print(f"📋 Topics: {len(INTERVIEW_PLAN['topics'])}")


# # # -------------------------
# # # /ask endpoint
# # # -------------------------
# # @app.post("/ask")
# # def ask(user_msg: UserMessage):
# #     user_text = user_msg.text
# #     thread_id = user_msg.thread_id

# #     # Initialize state for new thread
# #     if thread_id not in THREAD_STATES:
# #         THREAD_STATES[thread_id] = {
# #             "messages": [],
# #             "interview_plan": INTERVIEW_PLAN,
# #             "current_topic_index": 0,
# #             "questions_asked": 0,
# #             "is_follow_up": False
# #         }

# #     state = THREAD_STATES[thread_id]

# #     # Case 1 — This is the FIRST USER MESSAGE (start interview)
# #     if state["messages"] == []:
# #         print("\n🎤 Starting interview...")
# #         result = agent.invoke(state, {"configurable": {"thread_id": thread_id}})
# #     else:
# #         # Case 2 — Continue existing conversation
# #         print("\n➡️ Resuming agent with user input...")
# #         result = agent.invoke(
# #             Command(resume=user_text),
# #             {"configurable": {"thread_id": thread_id}}
# #         )

# #     # AI generated message
# #     ai_text = result["messages"][-1].content
# #     print(f"🤖 AI message: {ai_text}")
    
# #     # Save state back
# #     THREAD_STATES[thread_id] = result

# #     # Return response without TTS
# #     return JSONResponse({
# #         "user_text": user_text,
# #         "ai_text": ai_text,
# #         "questions_asked": result.get("questions_asked", 0),
# #         "interview_complete": result.get("questions_asked", 0) >= 12
# #     })


# # if __name__ == "__main__":
# #     import uvicorn
# #     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from agents import create_interview_agent, generate_interview_plan
from langgraph.types import Command
from elevenlabs import ElevenLabs
from schemas import UserMessage
import base64
import os
import shutil
import uuid
# -------------------------
# FastAPI Setup
# -------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
# -------------------------
# AI + TTS Clients  
# -------------------------
eleven = ElevenLabs(api_key="sk_cd9ef4033476688822593120ccfe36f6223a1c8da363c733")
# -------------------------
# Global State
# -------------------------
agent = create_interview_agent()
# Store session data: thread_id -> { "plan": ..., "state": ... }
# In a real app, use a database (Redis/Postgres)
SESSIONS = {} 
THREAD_STATES = {}
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
# -------------------------
# /init endpoint (Upload PDFs)
# -------------------------
@app.post("/init")
async def init_interview(
    resume: UploadFile = File(...),
    job_description: UploadFile = File(...)
):
    """
    Uploads PDFs, generates an interview plan, and starts a session.
    Returns: {"thread_id": "unique-id"}
    """
    thread_id = str(uuid.uuid4())
    
    # Save files locally
    resume_path = os.path.join(UPLOAD_DIR, f"{thread_id}_resume.pdf")
    job_path = os.path.join(UPLOAD_DIR, f"{thread_id}_job.pdf")
    
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)
        
    with open(job_path, "wb") as buffer:
        shutil.copyfileobj(job_description.file, buffer)
        
    # Generate Plan
    try: 
        data = generate_interview_plan(job_path, resume_path)
        analysis = data["analysis"]
        interview_plan = data["plan"].model_dump()
        
        # Store plan in session
        SESSIONS[thread_id] = interview_plan
        
        # Initialize empty state for this thread
        THREAD_STATES[thread_id] = {
            "messages": [],
            "interview_plan": interview_plan,
            "current_topic_index": 0,
            "questions_asked": 0,
            "is_follow_up": False
        }
        
        return {
            "thread_id": thread_id, 
            "message": "Interview initialized successfully.",
            "analysis": analysis.model_dump()
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
# -------------------------
# /ask endpoint
# -------------------------
@app.post("/ask")
def ask(user_msg: UserMessage):
    user_text = user_msg.text
    thread_id = user_msg.thread_id
    
    if thread_id not in THREAD_STATES:
         return JSONResponse(
             status_code=404, 
             content={"detail": "Session not found. Please upload PDFs first to /init."}
         )
    state = THREAD_STATES[thread_id]
    # Case 1 — This is the FIRST USER MESSAGE (potentially triggering start)
    # The frontend might send an empty "start" message or the first user hello.
    # If the user hasn't said anything yet, we might want the AI to start.
    
    print(f"\nProcessing message for thread {thread_id}")
    if not state["messages"]:
        # Start the interview (AI speaks first usually)
        print("Starting interview via agent...")
        result = agent.invoke(state, {"configurable": {"thread_id": thread_id}})
    else:
        # Continue existing conversation
        print("Resuming agent with user input...")
        result = agent.invoke(
            Command(resume=user_text),
            {"configurable": {"thread_id": thread_id}}
        )
    # 4. Extract AI Response
    # The result state contains the full history. The last message is the new AI question.
    if result.get("messages"):
        ai_text = result["messages"][-1].content
    else:
        ai_text = "ERROR: No response from agent."
    print("AI Message:", ai_text)
    # Save state back
    THREAD_STATES[thread_id] = result
    # 5. Generate TTS
    try:
        audio = eleven.text_to_speech.convert(
            text=ai_text,
            model_id="eleven_multilingual_v2",
            voice_id="EXAVITQu4vr4xnSDxMaL"
        )
        audio_bytes = b"".join(audio)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        print(f"TTS Error: {e}")
        audio_base64 = ""
    # 6. Serialize full history
    history = []
    for m in result.get("messages", []):
        # LangChain messages have a 'type' attribute (e.g., 'ai', 'human')
        role = "interviewer" if getattr(m, "type", "") == "ai" else "candidate"
        history.append({
            "role": role,
            "content": m.content
        })

    is_complete = result.get("questions_asked", 0) >= 12 and getattr(result.get("messages", [])[-1], "type", "") == "ai"
    
    evaluation = None
    if is_complete:
        print("Generating interview evaluation...")
        try:
            from tools import model
            from langchain_core.messages import SystemMessage, HumanMessage
            
            history_text = "\n".join([f"{h['role']}: {h['content']}" for h in history])
            eval_prompt = f"""You are an expert interview evaluator. 
            Analyze the following interview conversation and provide a structured feedback report.
            
            Conversation:
            {history_text}
            
            Provide the feedback in the following JSON format:
            {{
                "score": 0-100 (overall performance),
                "summary": "Brief executive summary",
                "strengths": ["list", "of", "strengths"],
                "weaknesses": ["list", "of", "areas", "for", "improvement"],
                "detailed_feedback": "Detailed paragraph of feedback"
            }}
            Return ONLY the raw JSON.
            """
            eval_response = model.invoke([
                SystemMessage(content="Return pure JSON evaluation of the interview."),
                HumanMessage(content=eval_prompt)
            ])
            import json
            # Clean possible markdown wrap
            raw_eval = eval_response.content.replace("```json", "").replace("```", "").strip()
            evaluation = json.loads(raw_eval)
        except Exception as e:
            print(f"Evaluation Error: {e}")
            evaluation = {
                "score": 0,
                "summary": "Feedback generation failed.",
                "strengths": [],
                "weaknesses": [],
                "detailed_feedback": "Could not generate feedback at this time."
            }

    return JSONResponse({
        "user_text": user_text,
        "ai_text": ai_text,
        "audio_base64": audio_base64,
        "history": history,
        "interview_complete": is_complete,
        "evaluation": evaluation
    })
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)