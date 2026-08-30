from fastapi import APIRouter, UploadFile, File,Form,HTTPException
from .vectorestore import load_vectorestore
import uuid

router = APIRouter()

@router.post("/upload_docs")
async def upload_docs(file:UploadFile=File(...),grade:int=Form(...),):
    """
    Upload pdf files and then index into:
        mongodb (full text chunks)
        pinecone (embedding only)

    access set to 'public' by default
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400,detail="File must be PDF")

    doc_id = str(uuid.uuid4())
    ACCESS_ROLE = "Public"

    # call vectorestore func
    try:
        await load_vectorestore([file],ACCESS_ROLE,doc_id=doc_id,grade=grade)
    
    except Exception as e:
        print("Error processing file:",e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process and index the document"
        )

    return {
        "message":f"file {file.filename} processed successfully",
        "doc_id":doc_id,
        "grade":grade,
        "access_role":ACCESS_ROLE
    }
    