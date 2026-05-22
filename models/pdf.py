from pydantic import BaseModel


class PDF(BaseModel):
    id: str | None = None
    name: str
    text: str
    checksum: str | None = None
