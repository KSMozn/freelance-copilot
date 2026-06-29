from dataclasses import asdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.output import Citation, OutputKind
from app.domain.entities.output import Output as DomainOutput
from app.infrastructure.db.models.output import Output


def _to_domain(row: Output) -> DomainOutput:
    citations = [
        Citation(
            claim=str(c.get("claim", "")),
            evidence_type=c.get("evidence_type", "skill"),
            evidence_id=c.get("evidence_id"),
            evidence_label=str(c.get("evidence_label", "")),
            snippet=c.get("snippet"),
        )
        for c in (row.citations or [])
        if isinstance(c, dict)
    ]
    return DomainOutput(
        id=row.id,
        user_id=row.user_id,
        persona_id=row.persona_id,
        job_id=row.job_id,
        kind=row.kind,  # type: ignore[arg-type]
        title=row.title,
        content_markdown=row.content_markdown,
        content_html=row.content_html,
        citations=citations,
        metadata=dict(row.metadata_ or {}),
        tone=row.tone,
        ai_provider=row.ai_provider,
        ai_model=row.ai_model,
        created_at=row.created_at,
    )


class SQLAlchemyOutputRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, output: DomainOutput) -> DomainOutput:
        row = Output(
            id=output.id,
            user_id=output.user_id,
            persona_id=output.persona_id,
            job_id=output.job_id,
            kind=output.kind,
            title=output.title,
            content_markdown=output.content_markdown,
            content_html=output.content_html,
            citations=[asdict(c) for c in output.citations],
            metadata_=dict(output.metadata or {}),
            tone=output.tone,
            ai_provider=output.ai_provider,
            ai_model=output.ai_model,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        await self._session.commit()
        return _to_domain(row)

    async def get(self, *, user_id: UUID, output_id: UUID) -> DomainOutput | None:
        stmt = select(Output).where(
            Output.id == output_id, Output.user_id == user_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        job_id: UUID | None = None,
        kind: OutputKind | None = None,
        limit: int = 50,
    ) -> list[DomainOutput]:
        stmt = select(Output).where(Output.user_id == user_id)
        if job_id is not None:
            stmt = stmt.where(Output.job_id == job_id)
        if kind is not None:
            stmt = stmt.where(Output.kind == kind)
        stmt = stmt.order_by(Output.created_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]

    async def delete(self, *, user_id: UUID, output_id: UUID) -> bool:
        row = await self._session.get(Output, output_id)
        if row is None or row.user_id != user_id:
            return False
        await self._session.delete(row)
        await self._session.commit()
        return True
