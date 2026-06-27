from typing import Protocol


class EmbeddingProvider(Protocol):
    """Outbound port for any service that turns text into a unit vector.

    Implementations live in `infrastructure/ai/`. Both real and mock providers
    return L2-normalized vectors so cosine similarity is just a dot product.
    """

    name: str
    model: str
    dim: int

    @property
    def model_id(self) -> str:
        """A stable identifier used as the `model` column in the embeddings table.

        Must be unique per provider × model so two providers cannot trample
        each other's rows under the same nominal model name.
        """
        ...

    async def embed(self, text: str) -> list[float]: ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
