"""
Capa de DOMINIO — Entidades.

La entidad `PDF` contiene SOLO conceptos del negocio (nombre, texto,
checksum) y ya NO es anémica: garantiza su propio invariante en la
construcción — todo PDF válido existe con un checksum obligatorio y no
vacío (es lo que identifica de forma única su contenido y sustenta la
regla de no duplicados de la capa de aplicación).

Sigue sin incluir `id`: el identificador de persistencia (`_id` de
Mongo / PK de SQL) es un detalle de infraestructura y lo gestionan los
adaptadores al mapear (ver `MongoPDFRepository._serialize`, que devuelve
dicts con `id` como read-model, sin contaminar la entidad).
"""
from pydantic import BaseModel, field_validator


class PDF(BaseModel):
    """Entidad de dominio: un PDF registrado en el sistema.

    Invariante: un PDF no puede existir sin checksum (obligatorio y no
    vacío). Quien intente construir uno inválido recibe `ValueError`
    (envuelto en `ValidationError` por pydantic) en la propia
    inicialización, sin depender de validaciones externas.
    """

    name: str
    text: str
    checksum: str

    @field_validator("checksum")
    @classmethod
    def _checksum_is_required(cls, value: str) -> str:
        """Invariante de dominio: el checksum es estrictamente requerido."""
        if not value or not value.strip():
            raise ValueError(
                "Invariante violado: todo PDF debe tener un checksum (no vacío)."
            )
        return value
