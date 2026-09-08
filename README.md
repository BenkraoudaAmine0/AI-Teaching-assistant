# 🎓 TutorRAG — AI Teaching Assistant

An AI-powered educational platform that lets **teachers upload study materials** and **students learn interactively** through document-grounded Q\&A and auto-generated quizzes. Built with **RAG (Retrieval-Augmented Generation)** using LangChain, Pinecone, and Groq.

---

## ✨ Features

### 👩‍🏫 For Teachers

- **Upload PDF documents** — course materials are automatically chunked, embedded, and indexed
- **Grade-scoped access control** — documents are tagged by grade level so students only see relevant content

### 🎒 For Students

- **AI Chat (Q\&A)** — ask questions about uploaded materials and get grounded, context-aware answers with source citations
- **Quiz Generator** — auto-generate multiple-choice quizzes on any topic from the uploaded documents
- **Quiz Checker** — submit answers and get instant grading with correct/incorrect feedback
- **Quiz History** — review all past quiz attempts, scores, and detailed results

### 🔐 Authentication

- Role-based signup (Student / Teacher) with HTTP Basic Auth
- Passwords hashed with **bcrypt**
- Grade and role-based document filtering

---

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────────┐
│   Streamlit UI  │◄───────►│   FastAPI Backend     │
│   (client/)     │  HTTP   │   (server/)           │
└─────────────────┘         └──────┬───────┬────────┘
                                   │       │
                          ┌────────▼──┐ ┌──▼─────────┐
                          │  MongoDB  │ │  Pinecone   │
                          │ (chunks,  │ │ (vector     │
                          │  users,   │ │  embeddings)│
                          │  quizzes) │ └─────────────┘
                          └───────────┘
                                ▲
                    ┌───────────┴───────────┐
                    │  Google Gemini        │
                    │  (Embedding Model)    │
                    ├──────────────────────-┤
                    │  Groq LLM            │
                    │  (Chat & Quiz Gen)   │
                    └───────────────────────┘
```

---

## 📁 Project Structure

```
AI-Teaching-assistant/
├── client/                      # Streamlit frontend
│   ├── main.py                  # Full UI (landing, login, signup, dashboards)
│   ├── assets/                  # Images for UI pages
│   └── .env                     # BACKEND_URL
│
├── server/                      # FastAPI backend
│   ├── main.py                  # App entry point & router registration
│   ├── config/
│   │   └── db.py                # MongoDB connection & collections
│   ├── auth/
│   │   ├── model.py             # Pydantic models (StudentUser, TeacherUser)
│   │   ├── route.py             # Signup, login, authenticate endpoints
│   │   └── hash_utils.py        # bcrypt password hashing
│   ├── docs/
│   │   ├── route.py             # PDF upload endpoint
│   │   └── vectorestore.py      # PDF parsing, chunking, embedding & indexing
│   ├── chat/
│   │   ├── route.py             # Chat, quiz, quiz-check, quiz-history endpoints
│   │   └── chat_query.py        # RAG chain: embedding → Pinecone → LLM
│   └── .env.example             # Environment variable template
│
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **MongoDB Atlas** account (or local MongoDB)
- **Pinecone** account (free tier works)
- **Google AI API Key** (for Gemini Embedding model)
- **Groq API Key** (for LLM inference)

### 1. Clone the Repository

```bash
git clone https://github.com/BenkraoudaAmine0/AI-LAW-assistant.git
cd AI-Teaching-assistant
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

#### Server (`server/.env`)

Copy the example and fill in your keys:

```bash
cp server/.env.example server/.env
```

```env
MONGO_URL="mongodb+srv://<username>:<password>@cluster0.mongodb.net/?appName=Cluster0"
DB_NAME="ai_teaching_assistant"

GOOGLE_API_KEY="your-google-api-key"

PINECONE_API_KEY="your-pinecone-api-key"
PINECONE_ENV="us-east-1"
PINECONE_INDEX_NAME="ai-teaching-assistant"

GROQ_API_KEY="your-groq-api-key"
```

> **Note:** Create a Pinecone index with **3072 dimensions** and **cosine** metric before running.

#### Client (`client/.env`)

```env
BACKEND_URL="http://127.0.0.1:8000"
```

### 5. Run the Backend

```bash
cd server
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 6. Run the Frontend

In a separate terminal:

```bash
cd client
streamlit run main.py
```

The UI will open at `http://localhost:8501`.

---

## 📡 API Endpoints

| Method   | Endpoint            | Description                     | Auth                    |
| -------- | ------------------- | ------------------------------- | ----------------------- |
| `POST` | `/signup/student` | Register a new student          | ❌                      |
| `POST` | `/signup/teacher` | Register a new teacher          | ❌                      |
| `GET`  | `/login`          | Login (returns user info)       | ✅ Basic                |
| `POST` | `/upload_docs`    | Upload & index a PDF            | ✅ Basic                |
| `POST` | `/chat`           | Ask a question (RAG)            | ✅ Basic (Student only) |
| `POST` | `/quiz`           | Generate a quiz                 | ✅ Basic (Student only) |
| `POST` | `/quiz/check`     | Submit quiz answers for grading | ✅ Basic                |
| `GET`  | `/quiz/history`   | Get past quiz attempts          | ✅ Basic (Student only) |

---

## 🧠 How RAG Works in This Project

1. **Upload** — Teacher uploads a PDF → text is extracted with PyPDF, chunked with LangChain's `RecursiveCharacterTextSplitter`
2. **Index** — Each chunk is embedded using **Google Gemini Embedding** and upserted to **Pinecone**; full text is stored in **MongoDB**
3. **Query** — Student asks a question → question is embedded → Pinecone finds the top-5 most similar chunks (filtered by role & grade)
4. **Answer** — Retrieved chunks are injected as context into a prompt → **Groq LLM** generates a grounded answer
5. **Quiz** — Same retrieval pipeline, but the prompt instructs the LLM to generate multiple-choice questions instead

---

## 🛠️ Tech Stack

| Layer                  | Technology                                         |
| ---------------------- | -------------------------------------------------- |
| **Frontend**     | Streamlit                                          |
| **Backend**      | FastAPI + Uvicorn                                  |
| **Database**     | MongoDB Atlas                                      |
| **Vector Store** | Pinecone                                           |
| **Embeddings**   | Google Gemini Embedding (`gemini-embedding-001`) |
| **LLM**          | Groq (via LangChain)                               |
| **PDF Parsing**  | PyPDF + LangChain                                  |
| **Auth**         | HTTP Basic Auth + bcrypt                           |

---

## 🗄️ MongoDB Collections

| Collection       | Purpose                                 |
| ---------------- | --------------------------------------- |
| `users`        | User accounts (students & teachers)     |
| `text`         | Full-text document chunks with metadata |
| `chat_history` | Student Q\&A conversation logs          |
| `quizzes`      | Generated quiz data                     |
| `quiz_history` | Student quiz attempt results & scores   |

---

## 👤 Author

**Benkraouda Amine**
📧 benkraouda.moh@gmail.com
🔗 [GitHub](https://github.com/BenkraoudaAmine0)

---

## 📄 License

This project is for educational purposes.
