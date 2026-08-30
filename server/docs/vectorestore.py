import os 
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from pinecone import Pinecone
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config.db import chunk_collection

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV","us-east-1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME","ai-teaching-assistant")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Use a local upload directory relative to this file
UPLOAD_DIR = Path(__file__).parent / "upload_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# pinecone global func upsert
pc=None
index=None

def get_pinecone_index():
    global pc,index 
    if index is None:
        pc=Pinecone(api_key=PINECONE_API_KEY)
        index=pc.Index(PINECONE_INDEX_NAME)
    return index

async def load_vectorestore(uploaded_files, role:str, doc_id:str, grade:int):
    # init embedding model
    embed_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    # get pinecone index
    pinecone_index = get_pinecone_index()
    # loop over uploaded files
    for file in uploaded_files:
        # save file to disk
        save_path = UPLOAD_DIR / file.filename
        with open(save_path,"wb") as f:
            f.write(await file.read())
        
        # load pdf file
        loader = PyPDFLoader(str(save_path))
        documents = loader.load()

        # chunk the text 
        splitter=RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50)
        chunks=splitter.split_documents(documents)

        # guard condition
        if not chunks:
            print(f"No text extracted from {file.filename}, skipping...")
            continue

        # --- store full text chunks in mongodb ---
        chunk_docs = [
            {
                "chunk_id": f"{doc_id}-{i}",
                "document_id": doc_id,
                "text": chunk.page_content,
                "page": int(chunk.metadata.get("page", 0)),
                "source": file.filename,
                "role": role,
                "grade": grade,
            }
            for i, chunk in enumerate(chunks)
        ]
        chunk_collection.insert_many(chunk_docs)

        # --- create embeddings and upsert to pinecone ---
        texts = [chunk.page_content for chunk in chunks]
        embeddings = await asyncio.to_thread(embed_model.embed_documents, texts)

        vectors = [
            {
                "id": f"{doc_id}-{i}",
                "values": embeddings[i],
                "metadata": {
                    "document_id": doc_id,
                    "page": int(chunks[i].metadata.get("page", 0)),
                    "source": file.filename,
                    "role": role,
                    "grade": grade,
                }
            }
            for i in range(len(embeddings))
        ]
        pinecone_index.upsert(vectors=vectors)

        print(f"Successfully Indexed {file.filename}")



        