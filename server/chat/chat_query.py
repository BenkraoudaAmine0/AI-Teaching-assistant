from pinecone.models.vectors import vector
from anyio import TemporaryDirectory
import os
import asyncio
from dotenv import load_dotenv

from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from config.db import chunk_collection

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


# init pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
# get pinecone index
index = pc.Index(PINECONE_INDEX_NAME)
#define embedding model
embed_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001") 
# define llm model
llm = ChatGroq(
    temperature=0.3,
    model_name="openai/gpt-oss-120b",
    groq_api_key=GROQ_API_KEY
)

# define chat prompt template
query_promot = PromptTemplate.from_template(
    """
    You are a helpful educational assistant.
    Answer the question using ONLY the context below.
    If the answer is not in the context, say "I don't know".
    
    Question: 
    {question}

    Context: 
    {context}
    
    If relevant, mention the document source.
    """
)

quiz_prompt = PromptTemplate.from_template(
    """
    You are a test-generation assistant.
    
    Using the context below, generate {num_questions}
    multiple-choice questions.

    Format STRICTLY as:
    Question 1: ...
    a) ...
    b) ...
    c) ...
    Correct Answer: a

    Context: 
    {context}
    
    """
)



# Design the RAG chain
rag_chain = (query_promot | llm)
quiz_chain = (quiz_prompt | llm)

async def answer_query(query:str,user_role:str,user_grade:int)->dict:
    # embedding generation
    embedding = await asyncio.to_thread(embed_model.embed_query,query)
    # Build the filter dynamically to handle missing roles/grades
    role_list = ["Public"]
    if user_role is not None:
        role_list.append(user_role)
        
    query_filter = {
        "role": {"$in": role_list}
    }
    if user_grade is not None:
        query_filter["grade"] = user_grade

    print("DEBUG: query_filter =", query_filter)
    
    # retrieve relevent enbedding from vectordb
    results = await asyncio.to_thread(
        index.query,
        vector=embedding,
        top_k=5,
        include_metadata=True,
        filter=query_filter
    )
    
    matches = results.get('matches', [])
    print(f"DEBUG: Pinecone returned {len(matches)} matches")

    # validation check
    if not matches:
        return {"answer":"No relevant documents found", "sources": []}

    # get chunk id and source from metadata
    # get chunk id
    chunk_ids = [match['id'] for match in matches]

    # get doc/text
    docs=list(chunk_collection.find({"chunk_id": {"$in": chunk_ids}}))
    # Validate check
    if not docs:
        return {"answer":"No relevant documents found", "sources": []}
        # preserve context order
        #1
    doc_map={ d["chunk_id"]: d for d in docs}
    ordered_map = [ doc_map[cid] for cid in chunk_ids if cid in doc_map]
        #2
    context = "\n\n".join(d["text"] for d in ordered_map)
    sources=list({d["source"] for d in ordered_map})
    # gather response
    response = await asyncio.to_thread(
        rag_chain.invoke,
        {"question": query, "context": context}
    )
    
    # get proper answer
    answer_text = (
        response.content
        if hasattr(response,"content")
        else str(response)
    )

    return {
        "answer":answer_text,
        "sources":sources
    }



async def quiz_generation(topic:str,user_role:str,user_grade:int,num_questions:int=3)->dict:
    # embedding generation
    embedding = await asyncio.to_thread(embed_model.embed_query,topic)
    # Build the filter dynamically to handle missing roles/grades
    role_list = ["Public"]
    if user_role is not None:
        role_list.append(user_role)
        
    query_filter = {
        "role": {"$in": role_list}
    }
    if user_grade is not None:
        query_filter["grade"] = user_grade

    print("DEBUG: query_filter =", query_filter)
    
    # retrieve relevent enbedding from vectordb
    results = await asyncio.to_thread(
        index.query,
        vector=embedding,
        top_k=5,
        include_metadata=True,
        filter=query_filter
    )
    
    matches = results.get('matches', [])
    print(f"DEBUG: Pinecone returned {len(matches)} matches")

    # validation check
    if not matches:
        return {"quiz":"No relevant information found for generating quiz", "sources": []}

    # get chunk id and source from metadata
    # get chunk id
    chunk_ids = [match['id'] for match in matches]

    # get doc/text
    docs=list(chunk_collection.find({"chunk_id": {"$in": chunk_ids}}))
    # Validate check
    if not docs:
        return {"quiz":"context unavailable for generating quiz", "sources": []}
        # preserve context order
        #1
    doc_map={ d["chunk_id"]: d for d in docs}
    ordered_map = [ doc_map[cid] for cid in chunk_ids if cid in doc_map]
        #2
    context = "\n\n".join(d["text"] for d in ordered_map)
    sources=list({d["source"] for d in ordered_map})
    # gather response
    response = await asyncio.to_thread(
        quiz_chain.invoke,
        {"num_questions": num_questions, "context": context}
    )
    
    # get proper answer
    quiz_text = (
        response.content
        if hasattr(response,"content")
        else str(response)
    )

    return {
        "quiz":quiz_text,
        "sources":sources
    }
