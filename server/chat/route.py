from fastapi import APIRouter,Depends,Body,HTTPException
from auth.route import authenticate
from chat.chat_query import answer_query, quiz_generation
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



@router.post("/quiz")
async def quiz(request:QuestionRequest, user=Depends(authenticate)):
    if user["role"] != "Student":
        raise HTTPException(
            status_code=403,
            detail="Only Students can create quizzes"
            )
    
    response = await quiz_generation(
        request.topic,
        user["role"],
        user["grade"],
        request.num_question
    )


    quiz_doc = {
        "user_id":user["user_id"],
        "timestamp":datetime.datetime.utcnow(),
        "topic":request.topic,
        "quiz_data":response["quiz"],
        "sources":response["sources"]
    }
    result = quizzes_collection.insert_one(quiz_doc)

    return {
        "quiz":response["quiz"],
        "sources":response["sources"],
        "quiz_id":str(result.inserted_id)
    }



@router.post("/quiz/check")
async def check_quiz_answers(request:QuizAnswerRequest, user=Depends(authenticate)):
    quiz_doc = quizzes_collection.find_one({"_id":ObjectId(request.quiz_id)})

    if not quiz_doc:
        raise HTTPException(
            404,
            "Quiz not found"
        )
    
    if quiz_doc["user_id"] != user["user_id"]:
        raise HTTPException(
            403,
            "You can only check your own quiz"
        )
    
    correct_answers = []
    for line in quiz_doc["quiz_data"].split("\n"):
        if line.startswith("Correct Answer"):
            correct_answers.append(line.split(":")[1].strip()[0])


    if len(request.answer) != len(correct_answers):
        raise HTTPException(
            400,
            "Answer count mismatch"
            )

    score = 0
    results = []

    for i,ans in enumerate(request.answer):
        is_correct = ans.strip().lower() == correct_answers[i]
        if is_correct:
            score += 1
            
        results.append({
            "question_number":i+1,
            "user_answer":ans,
            "correct_answer":correct_answers[i],
            "is_correct":is_correct
        })
    
    quiz_history.insert_one({
        "user_id":user["user_id"],
        "quiz_id":ObjectId(request.quiz_id),
        "timestamp":datetime.datetime.utcnow(),
        "topic":quiz_doc["topic"],
        "score":score,
        "total":len(correct_answers),
        "results":results,
        "quiz_content":quiz_doc["quiz_data"]
    })

     
    return {
        "message":f"Quiz complete, You scored {score}/{len(correct_answers)}",
        "score":score,
        "total":len(correct_answers),
        "results":results,
        "quiz_content":quiz_doc["quiz_data"]
    }



@router.get("/quiz/history")
async def get_quiz_history(user=Depends(authenticate)):
    if user["role"] != "Student":
        raise HTTPException(
            403,
            "Only Students can access quiz history"
        )
    
    cursor = quiz_history.find({"user_id": user["user_id"]}).sort("timestamp", -1)

    history = []
    for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        doc["quiz_id"] = str(doc["quiz_id"])
        doc.pop("user_id",None)
        history.append(doc)

    return {
        "message":f"Found {len(history)} quiz attempts",
        "history": history
        }