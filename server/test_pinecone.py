import os, asyncio
from pinecone import Pinecone
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv('PINECONE_INDEX_NAME', 'ai-teaching-assistant'))
embed = GoogleGenerativeAIEmbeddings(model='models/gemini-embedding-001')

query_emb = embed.embed_query('summarize me the uploaded document!')
print('Emb len:', len(query_emb))
res = index.query(vector=query_emb, top_k=5, include_metadata=True, filter={'role': {'$in': ['Public', 'Teacher']}})
print('Matches:', res.get('matches'))
