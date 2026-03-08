"""Build RAG document corpus from DB resources and barrier playbooks."""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.document_schema import RagDocument

logger = logging.getLogger(__name__)

_SCHEDULE_KEYWORDS = {
    "evening": "evening",
    "night": "evening",
    "day": "day",
    "morning": "day",
    "flexible": "flexible",
    "weekend": "flexible",
}


def _infer_schedule(subcategory: str | None, hours: str | None) -> str | None:
    combined = f"{subcategory or ''} {hours or ''}".lower()
    for kw, stype in _SCHEDULE_KEYWORDS.items():
        if kw in combined:
            return stype
    return None


def _extract_geography(address: str | None) -> str | None:
    if not address:
        return None
    parts = address.split(",")
    if len(parts) >= 2:
        return parts[-2].strip()
    return parts[0].strip()


_RESOURCE_QUERY = (
    "SELECT r.id, r.name, r.category, r.subcategory, r.address, "
    "r.services, r.notes, r.eligibility, r.hours, "
    "br.barrier_id, br.impact_strength "
    "FROM resources r "
    "JOIN barrier_resources br ON r.id = br.resource_id "
    "WHERE r.health_status IS NULL OR r.health_status != 'HIDDEN' "
    "ORDER BY r.id"
)


def _group_resource_rows(rows: list) -> dict[int, dict]:
    resource_map: dict[int, dict] = {}
    for row in rows:
        rid = row[0]
        if rid not in resource_map:
            resource_map[rid] = {
                "id": rid, "name": row[1], "category": row[2],
                "subcategory": row[3], "address": row[4], "services": row[5],
                "notes": row[6], "eligibility": row[7], "hours": row[8],
                "barrier_tags": [], "impact_strength": 0.0,
            }
        resource_map[rid]["barrier_tags"].append(row[9])
        resource_map[rid]["impact_strength"] = max(
            resource_map[rid]["impact_strength"], float(row[10])
        )
    return resource_map


def _resource_to_doc(r: dict) -> RagDocument:
    text_parts = [r["name"] or ""]
    if r["services"]:
        text_parts.append(str(r["services"]))
    if r["eligibility"]:
        text_parts.append(str(r["eligibility"]))
    if r["notes"]:
        text_parts.append(str(r["notes"]))
    return RagDocument(
        id=f"resource_{r['id']}",
        doc_type="resource",
        title=r["name"] or "",
        text=" ".join(text_parts),
        barrier_tags=list(set(r["barrier_tags"])),
        geography=_extract_geography(r["address"]),
        schedule_type=_infer_schedule(r["subcategory"], r["hours"]),
        transit_accessible=False,
        impact_strength=r["impact_strength"],
    )


async def _load_resource_docs(db: AsyncSession) -> list[RagDocument]:
    """Load resources linked to barriers as RagDocuments."""
    result = await db.execute(text(_RESOURCE_QUERY))
    resource_map = _group_resource_rows(result.fetchall())
    return [_resource_to_doc(r) for r in resource_map.values()]


async def _load_playbook_docs(db: AsyncSession) -> list[RagDocument]:
    """Load barrier playbooks as RagDocuments."""
    result = await db.execute(
        text(
            "SELECT b.id, b.name, b.category, b.description, b.playbook "
            "FROM barriers b "
            "WHERE b.playbook IS NOT NULL AND b.playbook != '' "
            "ORDER BY b.id"
        )
    )
    rows = result.fetchall()

    docs = []
    for row in rows:
        barrier_id, name, category, description, playbook = row
        text_body = f"{name}. {description or ''}. {playbook}".strip()
        docs.append(
            RagDocument(
                id=f"playbook_{barrier_id}",
                doc_type="playbook",
                title=f"Playbook: {name}",
                text=text_body,
                barrier_tags=[barrier_id],
                impact_strength=1.0,
            )
        )
    return docs


async def build_corpus(db: AsyncSession) -> list[RagDocument]:
    """Build full RAG corpus from resources and barrier playbooks."""
    resource_docs = await _load_resource_docs(db)
    playbook_docs = await _load_playbook_docs(db)
    docs = resource_docs + playbook_docs
    logger.info(
        "Corpus built: %d resource docs, %d playbook docs",
        len(resource_docs),
        len(playbook_docs),
    )
    return docs
