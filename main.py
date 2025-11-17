from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from agents import create_interview_agent, plan_result
from langgraph.types import Command
from elevenlabs import ElevenLabs
from schemas import UserMessage

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
eleven = ElevenLabs(api_key="sk_e01de8d3124d5dd55daedcccf8f475da2214bf9ece0410bc")

# -------------------------
# Interview agent load
# -------------------------
agent = create_interview_agent()

# Session states stored in-memory
THREAD_STATES = {}

# Pre-extracted interview plan from your agents.py
INTERVIEW_PLAN = plan_result["structured_response"].model_dump()


# -------------------------
# /ask endpoint
# -------------------------
@app.post("/ask")
def ask(user_msg: UserMessage):
    user_text = user_msg.text
    thread_id = user_msg.thread_id

    # Initialize state for new thread
    if thread_id not in THREAD_STATES:
        THREAD_STATES[thread_id] = {
            "messages": [],
            "interview_plan": INTERVIEW_PLAN,
            "current_topic_index": 0,
            "questions_asked": 0,
            "is_follow_up": False
        }

    state = THREAD_STATES[thread_id]

    # Case 1 — This is the FIRST USER MESSAGE (start interview)
    if state["messages"] == []:
        print("\n🎤 Starting interview...")
        result = agent.invoke(state, {"configurable": {"thread_id": thread_id}})
    else:
        # Case 2 — Continue existing conversation
        print("\n➡️ Resuming agent with user input...")
        result = agent.invoke(
            Command(resume=user_text),
            {"configurable": {"thread_id": thread_id}}
        )

    # AI generated message
    ai_text = result["messages"][-1].content
    print("AI message",ai_text)
    # Save state back
    THREAD_STATES[thread_id] = result

    # Generate TTS audio
    audio = eleven.text_to_speech.convert(
        text=ai_text,
        model_id="eleven_multilingual_v2",
        voice_id="EXAVITQu4vr4xnSDxMaL"
    )
    audio_bytes = b"".join(audio)
    # Return JSON + audio as base64
    return JSONResponse({
        "user_text": user_text,
        "ai_text": ai_text,
        "audio_base64": audio_bytes.decode("latin1")  # safe raw byte transfer
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


# from fastapi import FastAPI
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from agents import create_interview_agent, plan_result
# from langgraph.types import Command
# from schemas import UserMessage
# import os
# import base64

# # -------------------------
# # FastAPI Setup
# # -------------------------
# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_methods=["*"], 
#     allow_headers=["*"]
# )

# # -------------------------
# # Interview agent load
# # -------------------------
# agent = create_interview_agent()

# # Session states stored in-memory
# THREAD_STATES = {}

# # Pre-extracted interview plan from your agents.py
# INTERVIEW_PLAN = plan_result["structured_response"].model_dump()

# print("🚀 Interview System Ready!")
# print(f"📋 Topics: {len(INTERVIEW_PLAN['topics'])}")


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
#     print(f"🤖 AI message: {ai_text}")
    
#     # Save state back
#     THREAD_STATES[thread_id] = result

#     # Return response without TTS
#     return JSONResponse({
#         "user_text": user_text,
#         "ai_text": ai_text,
#         "questions_asked": result.get("questions_asked", 0),
#         "interview_complete": result.get("questions_asked", 0) >= 12
#     })


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)