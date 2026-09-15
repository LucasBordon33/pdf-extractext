"""
Capa de DOMINIO — Entidades.

La entidad `PDF` contiene SOLO conceptos del negocio (nombre, texto,
checksum). Ya NO incluye `id`: el identificador de persistencia
(`_id` de Mongo / PK de SQL) es un detalle de infraestructura y lo
gestionan los adaptadores al mapear (ver `MongoPDFRepository._serialize`,
que devuelve dicts con `id` como read-model, sin contaminar la entidad).
"""
from pydantic import BaseModel


class PDF(BaseModel):
    """Entidad de dominio: un PDF registrado en el sistema."""
    name: str
    text: str
    checksum: str | None = None
