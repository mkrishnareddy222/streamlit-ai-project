import json
from typing import List
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import Groq
from config import GROQ_API_KEY, MODEL_NAME
from api.chat_routes import router as chat_router
from api.llm_routes import router as llm_router
from api.user_routes import router as user_router

app = FastAPI(
    title="FastAPI SSE Streaming Backend",
    description="Streams Groq LLM responses to a Streamlit frontend using true SSE",
    version="2.0.0"
)
app.include_router(chat_router)
app.include_router(llm_router)
app.include_router(user_router)

client = Groq(api_key=GROQ_API_KEY)
class ChatMessage(BaseModel):
    role: str
    content: str
class ChatRequest(BaseModel):
    messages: List[ChatMessage]
@app.get("/")
def home():
    return {"message": "FastAPI SSE backend is running."}
@app.post("/stream")
def stream_response(request: ChatRequest):
    def generate():
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[m.dict() for m in request.messages],
            temperature=0.2,
            max_tokens=500,
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                payload = json.dumps({"content": content})
                yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no", 
        },
    )
@app.post("/generate")
def generate_response(request: ChatRequest):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[m.dict() for m in request.messages],
        temperature=0.2,
        max_tokens=500,
    )
    return {"response": response.choices[0].message.content}  
    
    
    
    
    
    
    
    
    