from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .model import StudentUser, TeacherUser

from config.db import users_collection

from .hash_utils import hash_password, verify_password





router = APIRouter()
security = HTTPBasic()



def authenticate(credentials:HTTPBasicCredentials=Depends(security)):
    """authenticate user using a HTTPBasicCredentials"""

    # Search by either email or username since credentials.username could be either
    user_record = users_collection.find_one({
        "$or": [
            {"email": credentials.username},
            {"username": credentials.username}
        ]
    })
    if not user_record or not verify_password(credentials.password, user_record["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {
        "username": user_record["username"],
        "email": user_record["email"],
        "fullname": user_record["fullname"],
        "grade": user_record["grade"] if "grade" in user_record else None,
        "school": user_record["school"] if "school" in user_record else None,
        "role": user_record["role"]
    }


    



@router.post("/signup/student")
def signup_student(req: StudentUser):
    """ Student Signup"""
    

    # check if username and email is already exist
    if users_collection.find_one({"email": req.email, "username": req.username}):
        raise HTTPException(status_code=400, detail="Email or username already exists")

    # hash the password
    hashed_password = hash_password(req.password)
    users_collection.insert_one({
        "username": req.username,
        "email": req.email,
        "password": hashed_password,
        "fullname": req.fullname,
        "role": "student",
        "grade": req.grade,
        "school": req.school
    })
    return {"message": "Student created successfully"}



@router.post("/signup/teacher")
def signup_teacher(req: TeacherUser):
    """ Teacher Signup"""
    

    # check if username and email is already exist
    if users_collection.find_one({"email": req.email, "username": req.username}):
        raise HTTPException(status_code=400, detail="Email or username already exists")

    # hash the password
    hashed_password = hash_password(req.password)
    users_collection.insert_one({
        "username": req.username,
        "email": req.email,
        "password": hashed_password,
        "fullname": req.fullname,
        "role": "teacher",
        "school": req.school
    })

    return {"message": "Teacher created successfully"}



@router.get("/login")
def login(user=Depends(authenticate)):
    """Login user"""
    return {"message": "Login successful", "user": user}