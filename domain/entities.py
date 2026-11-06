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
