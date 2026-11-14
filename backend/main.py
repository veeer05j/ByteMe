from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# For development. Later restrict this to your app/domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    text: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/run")
def run(request: RunRequest):
    # Move the non-Streamlit logic from your app.py here.
    # Do NOT import streamlit in this backend.
    result = request.text.upper()
    return {"result": result}