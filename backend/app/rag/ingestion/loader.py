"""Transactional policy ingestion with Redis coordination and content idempotency."""
import hashlib
import uuid
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from redis import Redis

from app.core.config import settings
from app.models.policy_document import PolicyDocument
from app.models.policy_chunk import PolicyChunk
from app.rag.embeddings.embedding_provider import embed_texts
from app.rag.ingestion.chunker import chunk_markdown
from app.rag.ingestion.metadata import load_policy


class IngestionBusy(Exception):
    """Another worker owns this policy's ingestion lock."""


def ingest_policy(path: Path, session: Session, redis: Redis) -> dict[str, object]:
    """Index one policy atomically; return unchanged for identical source content."""
    metadata, body, raw = load_policy(path)
    content_hash = hashlib.sha256(raw).hexdigest()
    lock_key = f"policyflow:ingest:{metadata.policy_code}:{metadata.version}"
    lock_token = uuid.uuid4().hex
    if not redis.set(lock_key, lock_token, nx=True, ex=600):
        raise IngestionBusy(lock_key)
    try:
        existing = session.scalar(select(PolicyDocument).where(
            PolicyDocument.policy_code == metadata.policy_code,
            PolicyDocument.version == metadata.version,
        ))
        if (existing and existing.content_hash == content_hash
                and existing.status == metadata.status
                and existing.embedding_model == settings.embedding_model
                and (existing.metadata_ or {}).get("ingestion_revision") == 2):
            return {"policy_code": metadata.policy_code, "version": metadata.version, "status": "unchanged", "chunks": len(existing.chunks)}
        chunks = chunk_markdown(body)
        if not chunks:
            raise ValueError("policy contains no nonempty sections")
        vectors = embed_texts([chunk.content for chunk in chunks])
        with session.begin_nested():
            if existing:
                session.delete(existing)
                session.flush()
            document = PolicyDocument(
                policy_code=metadata.policy_code, title=metadata.title,
                domain=metadata.domain, version=metadata.version, region=metadata.region,
                travel_type=metadata.travel_type, status="INDEXING",
                effective_date=metadata.effective_date, expiry_date=metadata.expiry_date,
                source_uri=path.resolve().as_uri(), content_hash=content_hash,
                embedding_model=settings.embedding_model,
                metadata_={**metadata.model_dump(mode="json"), "ingestion_revision": 2},
            )
            session.add(document)
            session.flush()
            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
                section_label = chunk.section_title.lower()
                section_travel_type = (
                    "DOMESTIC" if "domestic" in section_label
                    else "INTERNATIONAL" if "international" in section_label else "ALL"
                )
                session.add(PolicyChunk(
                    document_id=document.id, chunk_index=index, section_id=chunk.section_id,
                    section_title=chunk.section_title, content=chunk.content,
                    token_count=chunk.token_count, embedding=vector,
                    metadata_={"policy_code": metadata.policy_code, "version": metadata.version,
                               "section_id": chunk.section_id, "travel_type": section_travel_type},
                ))
            session.flush()
            document.status = metadata.status
        session.commit()
        return {"policy_code": metadata.policy_code, "version": metadata.version, "status": "indexed", "chunks": len(chunks)}
    except Exception:
        session.rollback()
        raise
    finally:
        redis.eval("if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end", 1, lock_key, lock_token)


def ingest_directory(directory: Path, session_factory, redis: Redis) -> list[dict[str, object]]:
    """Ingest all Markdown files in deterministic order."""
    results = []
    for path in sorted(directory.glob("*.md")):
        with session_factory() as session:
            results.append(ingest_policy(path, session, redis))
    return results
