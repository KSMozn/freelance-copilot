from typing import Protocol
from uuid import UUID

from app.domain.entities.output import Output, OutputKind


class OutputRepository(Protocol):
    async def create(self, output: Output) -> Output: ...

    async def get(self, *, user_id: UUID, output_id: UUID) -> Output | None: ...

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        job_id: UUID | None = None,
        kind: OutputKind | None = None,
        limit: int = 50,
    ) -> list[Output]: ...

    async def delete(self, *, user_id: UUID, output_id: UUID) -> bool: ...
