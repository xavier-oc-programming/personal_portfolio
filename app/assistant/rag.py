"""
app/assistant/rag.py

RAG (Retrieval-Augmented Generation) engine for the AI portfolio assistant.

Loads Xavier's knowledge base from:
  - Markdown files: CV, skills, personal narrative (app/data/knowledge/)
  - Database:       Project records (live data from the portfolio DB)

Indexes everything in a ChromaDB vector store using local sentence-transformer
embeddings, and answers questions by retrieving relevant context before calling
the Groq LLM.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from flask import Flask

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Xavier's AI portfolio assistant on his developer portfolio "
    "website at xavieroc.dev. You answer questions about Xavier Ocón "
    "Capdeville — his skills, projects, experience, education, and "
    "background — based only on the provided context documents. "
    "Be professional, warm, and concise. If a recruiter asks whether "
    "Xavier is suitable for a role, be honest and constructive. "
    "If you don't know something from the context, say so clearly — "
    "never invent information. Keep answers under 150 words unless "
    "a longer answer is genuinely necessary. Always respond in the "
    "same language the question was asked in — if asked in Spanish, "
    "answer in Spanish."
)

SOURCE_NAME_MAP: dict[str, str] = {
    "xavier_cv": "CV",
    "xavier_skills": "Skills",
    "xavier_about": "About",
}

SOURCE_URL_MAP: dict[str, str] = {
    "xavier_cv": "/about",
    "xavier_skills": "/about",
    "xavier_about": "/about",
}

STATIC_KNOWLEDGE_FILES = ["xavier_cv.md", "xavier_skills.md", "xavier_about.md"]


def _project_to_text(project: Any) -> str:
    """Convert a Project DB record to a rich text document for indexing."""
    parts = [f"## {project.title}"]
    if project.short_description:
        parts.append(project.short_description)
    if project.full_description:
        parts.append(project.full_description)
    if project.problem:
        parts.append(f"Problem: {project.problem}")
    if project.solution:
        parts.append(f"Solution: {project.solution}")
    if project.challenges:
        parts.append(f"Challenges: {project.challenges}")
    if project.results:
        parts.append(f"Results: {project.results}")
    if project.tech_stack:
        stack = project.tech_stack if isinstance(project.tech_stack, list) else []
        if stack:
            parts.append(f"Tech stack: {', '.join(stack)}")
    if project.tags:
        tags = project.tags if isinstance(project.tags, list) else []
        if tags:
            parts.append(f"Tags: {', '.join(tags)}")
    if project.live_url:
        parts.append(f"Live: {project.live_url}")
    if project.repo_url:
        parts.append(f"Repository: {project.repo_url}")
    return "\n\n".join(parts)


class RAGEngine:
    """Manages the vector store, retriever, and LLM for the assistant."""

    def __init__(self) -> None:
        self._retriever: Any = None
        self._llm: Any = None
        self._initialized: bool = False

    def init_app(self, app: Flask) -> None:
        """
        Build or load the vector index and initialise the LLM.

        Skips silently if GROQ_API_KEY is not configured.
        Stores self on app.extensions['rag_engine'] so routes can access it.

        Knowledge sources:
          - xavier_cv.md, xavier_skills.md, xavier_about.md (static markdown)
          - All Project records from the portfolio database
        """
        api_key = app.config.get("GROQ_API_KEY")

        if not api_key:
            app.extensions["rag_engine"] = None
            return

        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_chroma import Chroma
            from langchain_core.documents import Document
            from langchain_groq import ChatGroq
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError as exc:
            app.logger.error("RAG dependencies not installed: %s", exc)
            app.extensions["rag_engine"] = None
            return

        knowledge_dir = Path(app.root_path) / "data" / "knowledge"
        chroma_dir = Path(app.root_path) / "data" / "chroma_db"

        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
            )

            chroma_dir.mkdir(parents=True, exist_ok=True)
            chroma_sqlite = chroma_dir / "chroma.sqlite3"

            if chroma_sqlite.exists():
                vector_store = Chroma(
                    persist_directory=str(chroma_dir),
                    embedding_function=embeddings,
                )
            else:
                docs: list[Document] = []

                # Load static knowledge files (CV, skills, about)
                for filename in STATIC_KNOWLEDGE_FILES:
                    filepath = knowledge_dir / filename
                    if filepath.exists():
                        text = filepath.read_text(encoding="utf-8")
                        stem = Path(filename).stem
                        docs.append(Document(
                            page_content=text,
                            metadata={"source": stem},
                        ))

                # Load project documents from the database
                with app.app_context():
                    try:
                        from app.models.models import Project
                        projects = Project.query.all()
                        for project in projects:
                            docs.append(Document(
                                page_content=_project_to_text(project),
                                metadata={
                                    "source": "db_project",
                                    "project_title": project.title,
                                    "project_slug": project.slug,
                                },
                            ))
                        app.logger.info(
                            "Loaded %d project documents from database.", len(projects)
                        )
                    except Exception:
                        app.logger.exception(
                            "Failed to load project documents from DB — "
                            "falling back to xavier_projects.md if present."
                        )
                        # Fallback: load xavier_projects.md if available
                        fallback = knowledge_dir / "xavier_projects.md"
                        if fallback.exists():
                            text = fallback.read_text(encoding="utf-8")
                            docs.append(Document(
                                page_content=text,
                                metadata={"source": "xavier_projects"},
                            ))

                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50,
                )
                chunks = splitter.split_documents(docs)

                vector_store = Chroma.from_documents(
                    documents=chunks,
                    embedding=embeddings,
                    persist_directory=str(chroma_dir),
                )

            self._retriever = vector_store.as_retriever(search_kwargs={"k": 4})

            self._llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=api_key,
                temperature=0.3,
                max_tokens=512,
            )

            self._initialized = True
            app.extensions["rag_engine"] = self
            app.logger.info("RAG engine initialised successfully.")

        except Exception:
            app.logger.exception("Failed to initialise RAG engine.")
            app.extensions["rag_engine"] = None

    def chat(self, message: str, history: list[dict[str, str]]) -> dict[str, Any]:
        """
        Retrieve relevant context and generate a grounded answer.

        Args:
            message: The user's current question.
            history: List of prior turns, each a dict with 'role' and 'content'.
                     Only the last 4 exchanges (8 messages) are used.

        Returns:
            Dict with 'answer' (str) and 'sources' (list of {name, url} dicts).
        """
        if not self._initialized:
            raise RuntimeError("RAG engine is not initialised.")

        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        docs = self._retriever.invoke(message)

        sources: list[dict[str, str]] = []
        seen: set[str] = set()

        for doc in docs:
            project_slug: str | None = doc.metadata.get("project_slug")
            project_title: str | None = doc.metadata.get("project_title")

            if project_slug and project_title:
                if project_title in seen:
                    continue
                seen.add(project_title)
                sources.append({"name": project_title, "url": f"/projects/{project_slug}"})
            else:
                stem = Path(doc.metadata.get("source", "")).stem
                name = SOURCE_NAME_MAP.get(
                    stem,
                    stem.replace("xavier_", "").replace("_", " ").title(),
                )
                if name in seen:
                    continue
                seen.add(name)
                sources.append({"name": name, "url": SOURCE_URL_MAP.get(stem, "/")})

        context = "\n\n".join(
            f"[{i + 1}] {doc.page_content}" for i, doc in enumerate(docs)
        )

        messages: list[Any] = [SystemMessage(content=SYSTEM_PROMPT)]

        for turn in history[-8:]:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        user_message = f"Context:\n{context}\n\nQuestion: {message}"
        messages.append(HumanMessage(content=user_message))

        response = self._llm.invoke(messages)
        return {"answer": response.content, "sources": sources}
