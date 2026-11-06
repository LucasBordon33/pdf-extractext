from pydantic import BaseModel, field_validator


class PDF(BaseModel):
    """Entidad de dominio: PDF.
    Invariante: El checksum es obligatorio. Su ausencia falla en la 
    inicialización, garantizando un estado válido sin depender de validadores externos.
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
