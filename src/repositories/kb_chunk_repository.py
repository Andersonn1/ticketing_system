"""Repository for knowledge-base chunks."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.llm.embeddings import to_pgvector_str
from src.models import KBChunkModel
from src.schemas import RetrievedKBMatchSchema

from .contracts import KBChunkRepositoryContract


class KBChunkRepository(KBChunkRepositoryContract):
    """Async repository for KB chunks and vector retrieval."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_source_name(self, source_name: str) -> KBChunkModel | None:
        """Load a KB chunk by its stable source name."""
        result = await self._session.execute(select(KBChunkModel).where(KBChunkModel.source_name == source_name))
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        source_name: str,
        chunk_text: str,
        metadata: dict[str, Any],
        embedding: list[float],
    ) -> KBChunkModel:
        """Insert or update one KB chunk."""
        existing = await self.get_by_source_name(source_name)
        if existing is None:
            entity = KBChunkModel(
                source_name=source_name,
                chunk_text=chunk_text,
                meta_data=metadata,
                embedding=embedding,
            )
            self._session.add(entity)
            await self._session.flush()
            await self._session.refresh(entity)
            return entity

        existing.chunk_text = chunk_text
        existing.meta_data = metadata
        existing.embedding = embedding
        await self._session.flush()
        await self._session.refresh(existing)
        return existing

    async def search_similar(self, embedding: list[float], *, top_k: int) -> list[RetrievedKBMatchSchema]:
        """Return the most similar KB chunks for a query embedding."""
        vector = to_pgvector_str(embedding)
        result = await self._session.execute(
            text(
                """
                SELECT
                    id,
                    source_name,
                    chunk_text,
                    metadata,
                    1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM kb_chunk
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
                """
            ),
            {"embedding": vector, "top_k": top_k},
        )
        return [RetrievedKBMatchSchema.model_validate(dict(row)) for row in result.mappings().all()]
