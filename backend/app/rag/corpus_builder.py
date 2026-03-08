"""Build RAG corpus from database resources and barrier playbooks."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.document_schema import RagDocument


async def build_corpus(session: AsyncSession) -> list[RagDocument]:
    """Load resources and barrier playbooks into RagDocument list."""
    docs: list[RagDocument] = []
    docs.extend(await _build_resource_docs(session))
    docs.extend(await _build_playbook_docs(session))
    return docs


async def _build_resource_docs(session: AsyncSession) -> list[RagDocument]:
    """Create RagDocuments from resources table joined with barrier_resources."""
    result = await session.execute(
        text(
            "SELECT r.id, r.name, r.category, r.subcategory, r.address, "
            "r.phone, r.url, r.eligibility, r.services, r.hours, r.notes, "
            "r.lat, r.lng, r.health_status "
            "FROM resources r "
            "WHERE r.health_status != 'hidden'"
        )
    )
    resources = [dict(row._mapping) for row in result]

    docs = []
    for res in resources:
        barrier_tags, max_impact = await _get_barrier_tags_for_resource(
            session, res["id"]
        )
        if not barrier_tags:
            continue

        doc_text = _format_resource_text(res)
        docs.append(
            RagDocument(
                id=f"resource_{res['id']}",
                doc_type="resource",
                title=res["name"],
                text=doc_text,
                barrier_tags=barrier_tags,
                geography=_extract_city(res.get("address")),
                transit_accessible=res.get("lat") is not None,
                impact_strength=max_impact,
            )
        )
    return docs


async def _get_barrier_tags_for_resource(
    session: AsyncSession, resource_id: int
) -> tuple[list[str], float]:
    """Return (barrier_ids, max_impact_strength) for a resource."""
    result = await session.execute(
        text(
            "SELECT barrier_id, impact_strength "
            "FROM barrier_resources WHERE resource_id = :rid"
        ),
        {"rid": resource_id},
    )
    rows = result.fetchall()
    if not rows:
        return [], 0.0
    tags = [row[0] for row in rows]
    max_impact = max(row[1] for row in rows)
    return tags, max_impact


async def _build_playbook_docs(session: AsyncSession) -> list[RagDocument]:
    """Create RagDocuments from barrier playbooks."""
    result = await session.execute(
        text("SELECT id, name, category, playbook FROM barriers WHERE playbook != ''")
    )
    docs = []
    for row in result:
        r = dict(row._mapping)
        docs.append(
            RagDocument(
                id=f"playbook_{r['id']}",
                doc_type="playbook",
                title=f"Action Plan: {r['name']}",
                text=r["playbook"],
                barrier_tags=[r["id"]],
                impact_strength=1.0,
            )
        )
    return docs


def _format_resource_text(res: dict) -> str:
    """Format resource fields into embeddable text."""
    parts = [res["name"]]
    if res.get("category"):
        parts.append(f"Category: {res['category']}")
    if res.get("subcategory"):
        parts.append(f"Type: {res['subcategory']}")
    if res.get("services"):
        parts.append(f"Services: {res['services']}")
    if res.get("eligibility"):
        parts.append(f"Eligibility: {res['eligibility']}")
    if res.get("address"):
        parts.append(f"Address: {res['address']}")
    if res.get("phone"):
        parts.append(f"Phone: {res['phone']}")
    if res.get("hours"):
        parts.append(f"Hours: {res['hours']}")
    if res.get("notes"):
        parts.append(res["notes"])
    return ". ".join(parts)


def _extract_city(address: str | None) -> str | None:
    """Extract city from address string."""
    if not address:
        return None
    parts = address.split(",")
    if len(parts) >= 2:
        return parts[-2].strip()
    return None
