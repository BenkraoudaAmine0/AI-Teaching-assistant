from fastapi import APIRouter,Depends,Body,HTTPException
from auth.route import authenticate
from chat.chat_query import answer_query
from typing import List, Optional
from pydantic import BaseModel

import datetime
from config.db import (
    chat_history_collection,
    quizzes_collection,
    quiz_history
)
from bson.objectid import ObjectId

router = APIRouter()

class QuestionRequest(BaseModel):
    topic: str
    num_question: Optional[int] = 3

class QuizAnswerRequest(BaseModel):
    quiz_id:str
    answer:List[str]
    

@router.post("/chat")
async def chat(user=Depends(authenticate),query:str = Body(..., embed=True)):
    """
    """
    if user["role"] != "Student":
        raise HTTPException(
            status_code=403,
            detail="Only students can ask questions"
            )
    
    response = await answer_query(
        query,user["role"],user["grade"]
    )
    chat_history_collection.insert_one({
        "user_id":user["user_id"],
        "timestamp":datetime.datetime.utcnow(),
        "query":query,
        "response":response["answer"],
        "sources":response["sources"]
    })

    return response



@router.post(/quiz)
async def quiz(request:QuestionRequest, user=Depends(authenticate)):
    if user["role"] != "Student":
        raise HTTPException(
            status_code=403,
            detail="Only Students can create quizzes"
            )