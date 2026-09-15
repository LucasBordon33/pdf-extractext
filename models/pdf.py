from pydantic import BaseModel

"""

Modelo base de PyDantic para archivos PDF

"""


class PDF(BaseModel):
    id: str | None = None
    name: str
    text: str
    checksum: str | None = None
