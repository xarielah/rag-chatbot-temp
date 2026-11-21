<div align="center">

# 🤖 RAG Chatbot

**Ask questions. Get answers grounded in your own documents.**

![Python](https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-in%20development-orange)

</div>

---

## ✨ Features

- 📄 **Document ingestion**: load PDFs, text, and markdown
- 🔎 **Semantic search**: vector-based retrieval of relevant context
- 💬 **Grounded answers**: LLM responses backed by cited sources
- 🧩 **Modular**: swap the LLM, embeddings, or vector store

## 🏗️ How It Works

```
Documents ──► Chunk & Embed ──► Vector Store
                                    │
User question ──► Embed ──► Retrieve top-k ──► LLM + context ──► Answer
```

## 📁 Structure

```
rag-chatbot/
├── backend/    # API, ingestion, retrieval pipeline
├── frontend/   # Chat UI
└── docs/       # Additional documentation
```

## 🚀 Quickstart

```bash
# 1. Clone
git clone <repo-url> && cd rag-chatbot

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                # add your keys
python main.py

# 3. Frontend (new terminal)
cd frontend
npm install && npm run dev
```

## ⚙️ Configuration

Set in `backend/.env`:

| Variable         | Description                    |
| ---------------- | ------------------------------ |
| `LLM_API_KEY`    | API key for the LLM provider   |
| `EMBEDDING_MODEL`| Embedding model name           |
| `VECTOR_DB_PATH` | Location of the vector store   |

## 🧪 Tests

```bash
cd backend && pytest
```

## 🗺️ Roadmap

- [ ] Streaming responses
- [ ] Source citations in UI
- [ ] Conversation memory

## 🤝 Contributing

Fork, branch, add tests, and open a pull request.

## 📜 License

MIT © Your Name
