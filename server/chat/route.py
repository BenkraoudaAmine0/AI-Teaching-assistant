from fastapi import APIRouter,Depends,Body,HTTPException
from auth.router import authenticate
from chat.chat_query import answer_query
from typing import List, Optional
from pydantic import BaseModel

import datetime
from config.db import (
    chat_history_collection
)
from bson.objectid import ObjectId

router = APIRouter()

@router.post("/chat")
async def chat(query:str = Body(...),user:Dict[str,Any]=Depends(authenticate)):
    """
    """
