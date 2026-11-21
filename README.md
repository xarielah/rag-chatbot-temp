<div align="center">

# 🤖 RAG Chatbot

**Ask questions. Get answers grounded in your own documents.**

![Python](https://img.shields.io/badge/python-3.14-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-compose-2496ed?logo=docker&logoColor=white)
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

## 🧰 Tech Stack

| Layer        | Technology                                              |
| ------------ | ------------------------------------------------------- |
| Backend      | Python 3.14, FastAPI, Uvicorn, pydantic-settings        |
| LLM          | Anthropic (`anthropic` SDK)                             |
| Embeddings   | Voyage AI (`voyageai`)                                  |
| Vector store | Qdrant (`qdrant-client`)                                |
| Frontend     | React 19, TypeScript, Vite, ESLint                      |
| Serving      | Nginx (serves the built UI and proxies `/api/` to backend) |
| Orchestration| Docker Compose                                          |

## 📁 Structure

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app (/api/health, docs at /api/docs)
│   │   └── config.py      # Settings loaded from environment / .env
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/               # React + TypeScript UI (App.tsx, main.tsx)
│   ├── public/            # Static assets
│   ├── nginx.conf         # Static serving + /api reverse proxy
│   ├── Dockerfile
│   └── vite.config.ts
├── docs/                  # Additional documentation
├── docker-compose.yml     # qdrant + backend + frontend
├── docker-compose.override.yml  # Dev: hot reload, exposed ports
└── .env.example
```

## 🚀 Quickstart (Docker)

```bash
git clone <repo-url> && cd rag-chatbot
cp .env.example .env        # add your API keys
docker compose up --build
```

| Service  | URL                                  | Notes                                  |
| -------- | ------------------------------------ | -------------------------------------- |
| Frontend | http://localhost:8080                | Nginx; proxies `/api/` to the backend  |
| Backend  | http://localhost:8000/api/docs       | Exposed by the dev override (hot reload) |
| Qdrant   | http://localhost:6333                | Exposed by the dev override            |

`docker-compose.override.yml` is applied automatically and mounts `./backend` with `--reload`. For a production-like run use `docker compose -f docker-compose.yml up --build`.

## 💻 Local Development (without Docker)

```bash
# Backend (requires a running Qdrant, e.g. `docker compose up qdrant`)
cd backend
python -m venv .venv && .venv\Scripts\activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
set QDRANT_URL=http://localhost:6333                # Linux/macOS: export QDRANT_URL=...
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Frontend scripts: `npm run dev`, `npm run build`, `npm run lint`, `npm run preview`.

## ⚙️ Configuration

Set in `.env` (see `.env.example`):

| Variable            | Description                                   | Default               |
| ------------------- | --------------------------------------------- | --------------------- |
| `ANTHROPIC_API_KEY` | Anthropic API key (LLM)                       | –                     |
| `VOYAGE_API_KEY`    | Voyage AI API key (embeddings)                | –                     |
| `QDRANT_URL`        | Qdrant endpoint                               | `http://qdrant:6333`  |

## 🔌 API

| Method | Path          | Description                                  |
| ------ | ------------- | -------------------------------------------- |
| GET    | `/api/health` | Returns `{status, qdrant}` (Qdrant reachability) |
| GET    | `/api/docs`   | Interactive OpenAPI docs                     |

## 🗺️ Roadmap

- [ ] Streaming responses
- [ ] Source citations in UI
- [ ] Conversation memory

## 🤝 Contributing

Fork, branch, add tests, and open a pull request.

## 📜 License

MIT © Your Name
