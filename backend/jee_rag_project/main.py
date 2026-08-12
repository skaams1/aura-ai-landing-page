# main.py
from pydoc import text
import random
from tracemalloc import start
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from .vector_db import get_vector_db, VectorDBService
from .llm_service import get_llm_service
from .data_processor import NCERTDataProcessor
from .config import Config
from fastapi import Query
import json
import re

app = FastAPI(
    title="JEE Chemistry RAG API",
    description="RAG-powered JEE Chemistry mentor using NCERT content",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QuestionRequest(BaseModel):
    question: str
    use_context: bool = True
    top_k: int = 5

class ContextItem(BaseModel):
    text: str
    source: str
    score: float

class AnswerResponse(BaseModel):
    question: str
    answer: str
    context_used: List[ContextItem]
    success: bool

class SetupResponse(BaseModel):
    success: bool
    message: str
    chunks_processed: int


@app.get("/")
def root():
    return {
        "message": "JEE Chemistry RAG API",
        "endpoints": {
            "/ask": "POST - Ask a chemistry question",
            "/setup": "POST - Initialize vector database with NCERT data",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "JEE Chemistry RAG"}


@app.post("/setup", response_model=SetupResponse)
def setup_database():
    """Initialize the vector database with NCERT Chemistry data"""
    try:
        # Process data
        processor = NCERTDataProcessor()

        # Try Kaggle download first, fall back to sample data
        if processor.download_kaggle_dataset():
            chunks = processor.process_chemistry_data()
        else:
            chunks = processor.create_sample_chemistry_data()

        if not chunks:
            return SetupResponse(
                success=False,
                message="No chemistry content found to process",
                chunks_processed=0
            )

        # Store in vector database
        vector_db = get_vector_db()
        vector_db.store_chunks(chunks)

        return SetupResponse(
            success=True,
            message="Vector database initialized successfully with JEE Chemistry content",
            chunks_processed=len(chunks)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    """Ask a JEE Chemistry question and get a RAG-powered response"""
    try:
        vector_db = get_vector_db()
        llm_service = get_llm_service()

        # Retrieve relevant context
        context_items = []
        formatted_context = ""

        if request.use_context:
            relevant_chunks = vector_db.query(request.question, top_k=request.top_k)
            context_items = [
                ContextItem(
                    text=chunk["text"],
                    source=chunk["source"],
                    score=chunk["score"]
                )
                for chunk in relevant_chunks
            ]
            formatted_context = vector_db.format_context(relevant_chunks)

        # Generate response
        result = llm_service.generate_response(request.question, formatted_context)

        if result["success"]:
            return AnswerResponse(
                question=request.question,
                answer=result["response"],
                context_used=context_items,
                success=True
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate-question")
def generate_question(
    difficulty: int = Query(1)
):
    try:
        vector_db = get_vector_db()
        llm_service = get_llm_service()

        topics = {
            1: "atomic structure",
            2: "chemical bonding",
            3: "equilibrium",
            4: "organic chemistry",
            5: "amines"
        }
        topic_pool = {
    1: ["atomic structure", "periodic table", "chemical bonding"],
    2: ["chemical bonding", "states of matter", "thermodynamics"],
    3: ["equilibrium", "electrochemistry", "kinetics"],
    4: ["organic chemistry", "hydrocarbons", "amines"],
    5: ["coordination compounds", "electrochemistry", "organic chemistry"]
}

        topic = topics.get(difficulty, "chemical bonding")
        

        relevant_chunks = vector_db.query(topic, top_k=3)
        print(type(relevant_chunks))
        print(relevant_chunks)
        context = relevant_chunks[0]["text"]

        prompt = f"""
Generate ONE JEE Chemistry MCQ.

Topic: {topic}
Difficulty: {difficulty}

Return ONLY valid JSON.

Format:
{{
    "question":"",
    "options":["","","",""],
    "answer":0
}}

Rules:
- Exactly 4 options
- answer must be 0,1,2 or 3
- No explanations
- No markdown
- No hints.
- All options must be plausible.
- Only one correct answer.
"""

        result = llm_service.generate_response(prompt, context)

        if not result["success"]:
            print("GROQ ERROR:", result)
            return {
                "question": "Generation failed",
                "options": ["A","B","C","D"],
                "answer": 0
            }

        text = result["response"]

        print("\n====================")
        print("RAW GROQ RESPONSE:")
        print(text)
        print("====================\n")

        text = re.sub(r"```json|```", "", text).strip()
        start = text.find("{")
        end = text.rfind("}") + 1

        json_text = text[start:end]
        data = json.loads(json_text)

        data["topic"] = topic

        return data

    except Exception as e:
      
        traceback.print_exc()
        
@app.post("/ask/simple")
def ask_simple(question: str):
    """Simple endpoint for quick questions"""
    request = QuestionRequest(question=question)
    return ask_question(request)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
