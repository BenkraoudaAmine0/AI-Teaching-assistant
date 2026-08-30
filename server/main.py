from fastapi import FastAPI
from auth.route import router as auth_router
from docs.route import router as docs_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(docs_router)


@app.get("/")
def home():
    return {"message": "Welcome to the AI Teaching Assistant"}