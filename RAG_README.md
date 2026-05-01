# AI Portfolio Assistant — RAG Implementation

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)
![LangChain](https://img.shields.io/badge/LangChain-0.3-green)
![Llama 3.3](https://img.shields.io/badge/Llama-3.3%2070B-orange)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-purple)
![sentence-transformers](https://img.shields.io/badge/sentence--transformers-3.3-yellow)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey)

A conversational AI assistant embedded in xavieroc.dev. Answers recruiter and visitor questions about Xavier in real time using Retrieval-Augmented Generation — retrieving relevant context from structured knowledge documents before generating a grounded, cited response.

**Live → [xavieroc.dev/assistant](https://www.xavieroc.dev/assistant)**
&nbsp;&nbsp;·&nbsp;&nbsp;
**Model → Llama 3.3 70B via Groq (free tier)**
&nbsp;&nbsp;·&nbsp;&nbsp;
**Embeddings → sentence-transformers/all-MiniLM-L6-v2 (local, free)**

Standard chatbots hallucinate. This assistant only answers from verified source documents — Xavier's CV, project descriptions, skills inventory, and personal narrative. Every response cites which documents it drew from.

---

## Table of Contents

0. [Prerequisites](#0-prerequisites)
1. [Quick start](#1-quick-start)
2. [How RAG works](#2-how-rag-works)
3. [Architecture](#3-architecture)
4. [Knowledge base](#4-knowledge-base)
5. [Retrieval pipeline](#5-retrieval-pipeline)
6. [Rate limiting and free tier](#6-rate-limiting-and-free-tier)
7. [Module reference](#7-module-reference)
8. [Environment variables](#8-environment-variables)
9. [Adding or updating knowledge](#9-adding-or-updating-knowledge)
10. [Design decisions](#10-design-decisions)
11. [Dependencies](#11-dependencies)

---

## 0. Prerequisites

- Python 3.11+
- A free Groq API key — get one at https://console.groq.com (no credit card required)
- The portfolio app already running (see main README.md for full setup)

---

## 1. Quick start

```bash
# 1. Add your Groq API key to .env
echo "GROQ_API_KEY=your-key-here" >> .env

# 2. Install all dependencies (including RAG packages)
pip install -r requirements.txt

# 3. Start the app — the vector index builds automatically on first run
python -m app.app

# 4. Open the assistant in your browser
open http://127.0.0.1:5000/assistant
```

The first startup takes longer than usual because `sentence-transformers/all-MiniLM-L6-v2` downloads (~80 MB) and the ChromaDB index is built from scratch. Subsequent restarts load the persisted index instantly.

If `GROQ_API_KEY` is not set, the assistant page shows a "coming soon" placeholder and the app runs normally — no errors.

---

## 2. How RAG works

RAG solves a fundamental problem with language models: they don't know anything about Xavier specifically, and they can't look it up. Without retrieval, a model would either refuse to answer or fabricate plausible-sounding but wrong details.

RAG works in three steps:

**Step 1 — Index**
At startup, Xavier's knowledge base (four Markdown files) is split into 500-character chunks, embedded into dense vectors using a local sentence-transformer model, and stored in ChromaDB. This happens once and is persisted to disk.

**Step 2 — Retrieve**
When a user asks a question, the question is embedded using the same model. ChromaDB performs a semantic similarity search and returns the four most relevant chunks — regardless of exact keyword matches.

**Step 3 — Generate**
The retrieved chunks, the conversation history (last 4 exchanges), and the system prompt are assembled into a single prompt. Llama 3.3 70B generates a concise, grounded answer. The response is returned alongside the names of the source documents it drew from.

```
User question
     │
     ▼
Embed question → vector search → top 4 chunks
                                      │
                                      ▼
                              Build prompt with context
                                      │
                                      ▼
                              Llama 3.3 70B (Groq)
                                      │
                                      ▼
                         Answer + source citations
```

---

## 3. Architecture

The assistant is a Flask blueprint registered in `app/app.py` alongside the existing `admin` and `api` blueprints.

```
app/
├── app.py                   ← registers blueprint, inits RAG, adds 429 handler
├── assistant/
│   ├── __init__.py          ← blueprint + flask-limiter instance
│   ├── routes.py            ← GET /assistant, POST /assistant/chat
│   └── rag.py               ← RAGEngine class (indexing + chat)
├── data/
│   ├── chroma_db/           ← persisted vector store (gitignored)
│   └── knowledge/
│       ├── xavier_cv.md
│       ├── xavier_projects.md
│       ├── xavier_skills.md
│       └── xavier_about.md
└── templates/
    └── assistant/
        └── assistant.html   ← Bootstrap 5 chat UI
```

**Request flow:**

1. Browser sends `POST /assistant/chat` with `{"message": "...", "history": [...]}`
2. `routes.py` validates the message, checks the API key, and calls `rag_engine.chat()`
3. `rag_engine.chat()` embeds the question, retrieves top-4 chunks, builds a prompt with context + history, and calls Llama 3.3 70B via Groq
4. The route returns `{"answer": "...", "sources": [...]}` as JSON
5. The frontend appends the message bubble and source tags without a page reload

The `RAGEngine` instance is stored on `app.extensions["rag_engine"]` at startup so the index is never rebuilt per-request.

---

## 4. Knowledge base

Source documents live in `app/data/knowledge/` and are loaded at app startup. Each file is a Markdown document covering one aspect of Xavier's profile.

| File | Contents | Purpose |
|------|----------|---------|
| `xavier_cv.md` | Personal info, work experience, education, certifications, availability | Answers recruiter questions about background and status |
| `xavier_projects.md` | Detailed descriptions of all major projects with tech stacks | Answers questions about what Xavier has built |
| `xavier_skills.md` | Full skills breakdown by category (languages, frameworks, data, AI, tools) | Answers questions about specific technologies |
| `xavier_about.md` | Personal narrative, career transition story, motivation | Answers questions about who Xavier is and why he chose tech |

All four files are indexed together. Each is split into 500-character chunks with 50-character overlap so context is never cut off mid-sentence.

---

## 5. Retrieval pipeline

What happens on each chat request:

1. **Message arrives** at `POST /assistant/chat` with optional conversation history
2. **Validation** — message is non-empty, ≤ 500 characters; API key is present; rate limit is not exceeded
3. **Embed** — the user's question is converted to a 384-dimensional vector using `all-MiniLM-L6-v2` running locally
4. **Search** — ChromaDB performs cosine similarity search and returns the 4 most semantically relevant chunks from the knowledge base
5. **Build prompt** — system prompt + last 4 conversation exchanges + numbered context chunks + current question are assembled into a LangChain message list
6. **Generate** — `ChatGroq` sends the message list to Llama 3.3 70B (temperature 0.3, max 512 output tokens)
7. **Return** — the route returns `{"answer": response_text, "sources": [readable_source_names]}` as JSON

---

## 6. Rate limiting and free tier

The Groq free tier limits are enforced at the route level using `flask-limiter`.

| Limit | Value | Enforced by |
|-------|-------|-------------|
| Requests per minute | 15 RPM | `@limiter.limit("15 per minute")` per IP |
| Requests per day | 1,500 RPD | `@limiter.limit("1500 per day")` per IP |

Rate limit state is stored in memory (single-instance deployment on Railway). When the limit is hit, flask-limiter triggers a 429 response. The frontend displays context-aware messages:

- Per-minute limit: *"Sorry — too many requests. Please wait a minute and try again."*
- Daily limit (flask-limiter or Groq quota): *"Sorry — the assistant has hit its daily request limit. Please try again tomorrow."*

**Embeddings are free.** The `sentence-transformers/all-MiniLM-L6-v2` model runs entirely locally — it does not make any API calls and does not count toward any quota.

---

## 7. Module reference

### `app/assistant/rag.py`

| Name | Signature | Description |
|------|-----------|-------------|
| `RAGEngine` | class | Manages vector store, retriever, and LLM lifecycle |
| `RAGEngine.init_app` | `(app: Flask) -> None` | Builds or loads the ChromaDB index and initialises the LLM. Stores self on `app.extensions["rag_engine"]`. No-ops silently if API key is missing. |
| `RAGEngine.chat` | `(message: str, history: list[dict]) -> dict` | Retrieves top-4 chunks, builds a prompted message list, calls Llama 3.3, returns `{"answer": str, "sources": list}` |
| `SYSTEM_PROMPT` | `str` | The system instruction sent to the LLM on every request |
| `SOURCE_NAME_MAP` | `dict[str, str]` | Maps knowledge base filenames to human-readable source labels |

### `app/assistant/routes.py`

| Name | Signature | Description |
|------|-----------|-------------|
| `assistant_page` | `GET /assistant` | Renders the chat template or coming-soon page based on API key presence |
| `chat` | `POST /assistant/chat` | Validates input, calls `rag_engine.chat()`, returns JSON response |

---

## 8. Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes (for assistant) | Free Groq API key from console.groq.com. If absent, the assistant shows a placeholder page and the rest of the site is unaffected. |

No paid API key is ever required. All embedding computation runs locally using `sentence-transformers`.

---

## 9. Adding or updating knowledge

To update what the assistant knows:

1. **Edit** the relevant `.md` file in `app/data/knowledge/`, or add a new `.md` file
2. **Delete** `app/data/chroma_db/` to force a full index rebuild:
   ```bash
   rm -rf app/data/chroma_db/
   ```
3. **Restart** the app — the index rebuilds automatically at startup from the updated files
4. **Test** with a question that would hit the new content to verify retrieval is working

The first restart after deleting the index will take a few seconds longer as the vector store is rebuilt.

---

## 10. Design decisions

### Why RAG instead of fine-tuning?

Fine-tuning a language model on Xavier's information would cost money, require GPU compute, and produce a model that is frozen in time — updating it means re-training. RAG separates the knowledge from the model entirely. Updating the knowledge base is just editing a Markdown file and restarting the app. It is also far cheaper (free in this case) and produces more factually reliable outputs because the model is explicitly shown the source text rather than asked to recall from weights.

### Why Groq + Llama 3.3 instead of a paid model?

The Groq free tier (15 RPM, 1,500 RPD) is more than sufficient for a personal portfolio assistant — the realistic request volume from recruiters and visitors is well within these limits. GPT-4o or Claude would cost money with no quality benefit for this specific use case. Llama 3.3 70B is a capable open-weights model that performs well on structured Q&A tasks. Keeping the assistant entirely free removes any operational cost from the portfolio site.

### Why local sentence-transformers instead of API-based embeddings?

The embedding step happens on every chat request and at index-build time. Using an API for embeddings would add latency, require another API key, and incur per-token costs. The `all-MiniLM-L6-v2` model is 80 MB, runs entirely in CPU memory on the Railway instance, produces 384-dimensional embeddings in milliseconds, and requires no external call. For a four-document knowledge base with ~50 chunks, the quality difference between local and API embeddings is negligible.

### Why Markdown files instead of a database for the knowledge base?

The knowledge base contains structured prose — CVs, project descriptions, narratives — not tabular records. Storing this in a database would add query complexity, a schema, and a migration layer for content that changes infrequently. Markdown files are readable and editable in any text editor, version-controlled naturally in git, and trivially loaded by LangChain's `DirectoryLoader`. Adding new knowledge is as simple as creating a new `.md` file in `app/data/knowledge/`.

---

## 11. Dependencies

The following packages were added specifically for the assistant feature. All other dependencies belong to the existing portfolio app.

| Package | Used in | Purpose |
|---------|---------|---------|
| `langchain` | `rag.py` | Core LangChain framework — message types, chain building |
| `langchain-community` | `rag.py` | `HuggingFaceEmbeddings`, `DirectoryLoader`, `TextLoader` |
| `langchain-chroma` | `rag.py` | LangChain integration for ChromaDB vector store |
| `langchain-groq` | `rag.py` | LangChain integration for Groq (`ChatGroq`) |
| `langchain-text-splitters` | `rag.py` | `RecursiveCharacterTextSplitter` for document chunking |
| `chromadb` | `rag.py` | Local persistent vector store |
| `sentence-transformers` | `rag.py` | Local embedding model (`all-MiniLM-L6-v2`) |
| `flask-limiter` | `__init__.py`, `routes.py` | Per-IP rate limiting (15 RPM, 1,500 RPD) on the chat endpoint |
