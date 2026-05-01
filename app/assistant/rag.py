"""
app/assistant/rag.py

RAG (Retrieval-Augmented Generation) engine for the AI portfolio assistant.

Loads Xavier's knowledge base from Markdown files, indexes them in a
ChromaDB vector store using local sentence-transformer embeddings, and
answers questions by retrieving relevant context before calling Gemini.
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
    "xavier_projects": "Projects",
    "xavier_skills": "Skills",
    "xavier_about": "About",
}


class RAGEngine:
    """Manages the vector store, retriever, and LLM for the assistant."""

    def __init__(self) -> None:
        self._retriever: Any = None
        self._llm: Any = None
        self._initialized: bool = False

    def init_app(self, app: Flask) -> None:
        """
        Build or load the vector index and initialise the LLM.

        Skips silently if GOOGLE_API_KEY is not configured.
        Stores self on app.extensions['rag_engine'] so routes can access it.
        """
        api_key = app.config.get("GOOGLE_API_KEY")

        if not api_key:
            app.extensions["rag_engine"] = None
            return

        try:
            from langchain_community.document_loaders import DirectoryLoader, TextLoader
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_chroma import Chroma
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError as exc:
            app.logger.error("RAG dependencies not installed: %s", exc)
            app.extensions["rag_engine"] = None
            return

        knowledge_dir = Path(app.root_path) / "data" / "knowledge"
        chroma_dir = Path(app.root_path) / "data" / "chroma_db"

        if not knowledge_dir.exists():
            app.logger.warning("Knowledge base directory not found — skipping RAG init.")
            app.extensions["rag_engine"] = None
            return

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
                loader = DirectoryLoader(
                    str(knowledge_dir),
                    glob="**/*.md",
                    loader_cls=TextLoader,
                    loader_kwargs={"encoding": "utf-8"},
                )
                docs = loader.load()

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

            self._llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=api_key,
                temperature=0.3,
                max_output_tokens=512,
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
            Dict with 'answer' (str) and 'sources' (list of readable source names).
        """
        if not self._initialized:
            raise RuntimeError("RAG engine is not initialised.")

        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        docs = self._retriever.invoke(message)

        sources: list[str] = []
        seen: set[str] = set()
        for doc in docs:
            stem = Path(doc.metadata.get("source", "")).stem
            name = SOURCE_NAME_MAP.get(
                stem,
                stem.replace("xavier_", "").replace("_", " ").title(),
            )
            if name not in seen:
                seen.add(name)
                sources.append(name)

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
