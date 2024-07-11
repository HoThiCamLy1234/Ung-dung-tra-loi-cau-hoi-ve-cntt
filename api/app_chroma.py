import os
from fastapi import FastAPI
from dotenv import load_dotenv
import uuid
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sample import GPTSampler

app = FastAPI()
# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

def InitModel():
    return GPTSampler()

sessions = {}
class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.get("/init")
async def initialize_bot(): 
    
    model = InitModel()
    session_id = str(uuid.uuid4())
    sessions[session_id] = model
    return {"session_id": session_id, "response": "Hi, Can I help you?."}

@app.post("/process")
async def process_chat_message(chat_request: ChatRequest):

    if chat_request.session_id not in sessions:
        chat_request.session_id = str(uuid.uuid4())
        sessions[chat_request.session_id] = InitModel()
    
    chain = sessions[chat_request.session_id]

    response = chain.generate_samples(chat_request.message)
    return {"session_id": chat_request.session_id, "response": response}

@app.delete("/removesession/{session_id}")
async def remove_session(session_id):
    if(session_id not in sessions):
        return{"response: Not Found"}
    sessions.pop(session_id, None)
    return {"response: OK"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)