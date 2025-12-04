from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_ALGORITHM = "HS256"

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Pydantic Models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    education_level: str  # school, college, undergraduate, postgraduate
    sub_level: Optional[str] = None  # For school: primary, middle, high_school, senior_secondary, competitive
    board: Optional[str] = None  # For school: cbse, icse, state, ncert

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    education_level: str
    sub_level: Optional[str] = None
    board: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TopicRequest(BaseModel):
    topic: str

class TechniqueRequest(BaseModel):
    topic: str
    technique: str  # passage, video, flowchart

class QuestionRequest(BaseModel):
    topic: str
    content: str
    technique: str
    difficulty: int = 1

class AnswerSubmission(BaseModel):
    session_id: str
    question_id: str
    answer: str
    time_taken: float

class LearningSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    topic: str
    technique: str
    content: Any
    questions: List[Dict]
    responses: List[Dict] = []
    score: int = 0
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Helper Functions
def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    user = await db.users.find_one({"id": payload.get("user_id")}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

# Initialize LLM
def get_llm_chat(session_id: str, system_message: str = "You are an educational AI assistant."):
    return LlmChat(
        api_key=os.environ.get('EMERGENT_LLM_KEY'),
        session_id=session_id,
        system_message=system_message
    ).with_model("openai", "gpt-4o-mini")

# Routes
@api_router.post("/auth/signup")
async def signup(request: SignupRequest):
    existing = await db.users.find_one({"email": request.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = request.model_dump()
    user_dict['password_hash'] = pwd_context.hash(user_dict.pop('password'))
    user = User(**{k: v for k, v in user_dict.items() if k != 'password_hash'})
    
    doc = user.model_dump()
    doc['password_hash'] = user_dict['password_hash']
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.users.insert_one(doc)
    token = create_token({"user_id": user.id, "email": user.email})
    
    return {"token": token, "user": user.model_dump()}

@api_router.post("/auth/login")
async def login(request: LoginRequest):
    user_doc = await db.users.find_one({"email": request.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not pwd_context.verify(request.password, user_doc['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})
    token = create_token({"user_id": user.id, "email": user.email})
    
    return {"token": token, "user": user.model_dump()}

@api_router.post("/learning/generate-content")
async def generate_content(request: TechniqueRequest, current_user: User = Depends(get_current_user)):
    session_id = f"{current_user.id}_{request.topic}_{datetime.now(timezone.utc).timestamp()}"
    
    if request.technique == "passage":
        chat = get_llm_chat(session_id, "You are an educational content creator. Create clear, engaging passages.")
        prompt = f"""Create an educational passage about '{request.topic}' suitable for {current_user.education_level} level.
Make it clear, engaging, and informative (300-400 words). Focus on key concepts and real-world applications."""
        response = await chat.send_message(UserMessage(text=prompt))
        return {"type": "passage", "content": response}
    
    elif request.technique == "video":
        chat = get_llm_chat(session_id, "You are a YouTube content curator.")
        prompt = f"""Find ONE high-quality educational YouTube video about '{request.topic}' suitable for {current_user.education_level} level.
Return ONLY a JSON object with this format: {{"title": "video title", "videoId": "YouTube video ID", "description": "brief description"}}
The video should be animated, clear, and in English."""
        response = await chat.send_message(UserMessage(text=prompt))
        try:
            # Extract JSON from response
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            video_data = json.loads(content)
            return {"type": "video", "content": video_data}
        except:
            # Fallback video
            return {
                "type": "video",
                "content": {
                    "title": f"Educational Video: {request.topic}",
                    "videoId": "dQw4w9WgXcQ",
                    "description": "Educational content about " + request.topic
                }
            }
    
    elif request.technique == "flowchart":
        chat = get_llm_chat(session_id, "You are a flowchart expert using Mermaid syntax.")
        prompt = f"""Create a colorful, easy-to-understand Mermaid flowchart about '{request.topic}' for {current_user.education_level} level.
Use Mermaid syntax. Make it visual and clear with proper flow. Start with 'graph TD' or 'graph LR'.
Return ONLY the Mermaid code, no explanations."""
        response = await chat.send_message(UserMessage(text=prompt))
        # Clean the response
        mermaid_code = response.strip()
        if "```mermaid" in mermaid_code:
            mermaid_code = mermaid_code.split("```mermaid")[1].split("```")[0].strip()
        elif "```" in mermaid_code:
            mermaid_code = mermaid_code.split("```")[1].split("```")[0].strip()
        return {"type": "flowchart", "content": mermaid_code}
    
    raise HTTPException(status_code=400, detail="Invalid technique")

@api_router.post("/learning/generate-questions")
async def generate_questions(request: QuestionRequest, current_user: User = Depends(get_current_user)):
    session_id = f"{current_user.id}_questions_{datetime.now(timezone.utc).timestamp()}"
    chat = get_llm_chat(session_id, "You are an educational assessment expert.")
    
    difficulty_level = ["basic", "moderate", "challenging"][min(request.difficulty - 1, 2)]
    
    prompt = f"""Based on this content about '{request.topic}':
{request.content[:1000]}

Generate 6 questions at {difficulty_level} difficulty:
- 3 Multiple Choice Questions (MCQ) with 4 options each
- 3 Short Answer Questions

Return ONLY a JSON array with this exact format:
[
  {{"id": "q1", "type": "mcq", "question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct": "A", "expected_time": 30}},
  {{"id": "q2", "type": "short", "question": "...", "expected_time": 60}}
]

Set expected_time based on complexity (MCQ: 20-40s, Short: 40-90s)."""
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    try:
        content = response.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        questions = json.loads(content)
        return {"questions": questions}
    except Exception as e:
        logger.error(f"Failed to parse questions: {e}")
        # Fallback questions
        return {
            "questions": [
                {"id": "q1", "type": "mcq", "question": f"What is the main concept of {request.topic}?", "options": ["A) Concept A", "B) Concept B", "C) Concept C", "D) Concept D"], "correct": "A", "expected_time": 30},
                {"id": "q2", "type": "short", "question": f"Explain {request.topic} briefly.", "expected_time": 60}
            ]
        }

@api_router.post("/learning/evaluate-answer")
async def evaluate_answer(submission: AnswerSubmission, current_user: User = Depends(get_current_user)):
    session = await db.learning_sessions.find_one({"id": submission.session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    question = next((q for q in session['questions'] if q['id'] == submission.question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    is_correct = False
    feedback = ""
    
    if question['type'] == 'mcq':
        is_correct = submission.answer.strip().upper().startswith(question['correct'].upper())
        feedback = "Correct!" if is_correct else f"Incorrect. The correct answer is {question['correct']}."
    else:
        # Use AI to evaluate short answer
        chat = get_llm_chat(f"eval_{submission.session_id}", "You are an educational evaluator.")
        prompt = f"""Question: {question['question']}
Student Answer: {submission.answer}

Evaluate if the answer is correct (even if not perfect). Return JSON: {{"is_correct": true/false, "feedback": "brief feedback"}}"""
        response = await chat.send_message(UserMessage(text=prompt))
        try:
            content = response.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            result = json.loads(content)
            is_correct = result.get('is_correct', False)
            feedback = result.get('feedback', 'Answer evaluated.')
        except:
            is_correct = len(submission.answer.strip()) > 10
            feedback = "Answer recorded."
    
    # Calculate speed score
    time_ratio = submission.time_taken / question['expected_time']
    speed_score = "fast" if time_ratio < 0.8 else "optimal" if time_ratio < 1.5 else "slow"
    
    response_data = {
        "question_id": submission.question_id,
        "answer": submission.answer,
        "is_correct": is_correct,
        "time_taken": submission.time_taken,
        "speed_score": speed_score,
        "feedback": feedback,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Update session
    await db.learning_sessions.update_one(
        {"id": submission.session_id},
        {
            "$push": {"responses": response_data},
            "$inc": {"score": 1 if is_correct else 0}
        }
    )
    
    return response_data

@api_router.post("/learning/create-session")
async def create_session(request: Dict, current_user: User = Depends(get_current_user)):
    session = LearningSession(
        user_id=current_user.id,
        topic=request['topic'],
        technique=request['technique'],
        content=request['content'],
        questions=request['questions']
    )
    
    doc = session.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.learning_sessions.insert_one(doc)
    
    return {"session_id": session.id}

@api_router.get("/learning/session/{session_id}")
async def get_session(session_id: str, current_user: User = Depends(get_current_user)):
    session = await db.learning_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@api_router.get("/progress")
async def get_progress(current_user: User = Depends(get_current_user)):
    sessions = await db.learning_sessions.find({"user_id": current_user.id}, {"_id": 0}).to_list(1000)
    
    total_sessions = len(sessions)
    completed = sum(1 for s in sessions if s.get('completed', False))
    total_questions = sum(len(s.get('responses', [])) for s in sessions)
    correct_answers = sum(sum(1 for r in s.get('responses', []) if r.get('is_correct', False)) for s in sessions)
    
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Speed analysis
    all_responses = [r for s in sessions for r in s.get('responses', [])]
    fast_count = sum(1 for r in all_responses if r.get('speed_score') == 'fast')
    optimal_count = sum(1 for r in all_responses if r.get('speed_score') == 'optimal')
    slow_count = sum(1 for r in all_responses if r.get('speed_score') == 'slow')
    
    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "accuracy": round(accuracy, 2),
        "speed_analysis": {
            "fast": fast_count,
            "optimal": optimal_count,
            "slow": slow_count
        },
        "recent_sessions": sorted(sessions, key=lambda x: x['created_at'], reverse=True)[:5]
    }

@api_router.get("/analytics/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    sessions = await db.learning_sessions.find({"user_id": current_user.id}, {"_id": 0}).to_list(1000)
    
    # Calculate metrics
    all_responses = [r for s in sessions for r in s.get('responses', [])]
    technique_performance = {}
    
    for session in sessions:
        tech = session['technique']
        if tech not in technique_performance:
            technique_performance[tech] = {'correct': 0, 'total': 0}
        for resp in session.get('responses', []):
            technique_performance[tech]['total'] += 1
            if resp.get('is_correct', False):
                technique_performance[tech]['correct'] += 1
    
    # Best and weak areas
    for tech in technique_performance:
        if technique_performance[tech]['total'] > 0:
            technique_performance[tech]['accuracy'] = round(
                technique_performance[tech]['correct'] / technique_performance[tech]['total'] * 100, 2
            )
        else:
            technique_performance[tech]['accuracy'] = 0
    
    return {
        "technique_performance": technique_performance,
        "total_learning_time": sum(r.get('time_taken', 0) for r in all_responses),
        "avg_time_per_question": sum(r.get('time_taken', 0) for r in all_responses) / len(all_responses) if all_responses else 0,
        "strengths": [t for t, p in technique_performance.items() if p.get('accuracy', 0) >= 75],
        "weaknesses": [t for t, p in technique_performance.items() if p.get('accuracy', 0) < 60]
    }

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()