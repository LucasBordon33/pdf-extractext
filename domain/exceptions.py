"""
Capa de DOMINIO — Excepciones de negocio.

Errores que expresan reglas del dominio (no detalles de infraestructura
ni de transporte HTTP). Constituyen el "idioma" único de fallo entre las
capas:

- InvalidPDFError: el archivo recibido no cumple las reglas de un PDF.
- DuplicatePDFError: ya existe un PDF registrado con el mismo checksum.
- PDFNotFoundError: no existe un PDF con el identificador solicitado.

La capa de aplicación las lanza cuando una regla se viola; los
adaptadores de entrada (p. ej. el controller HTTP) se limitan a
traducirlas a códigos de estado (400 / 409 / 404). Ninguna regla de
negocio vuelve a evaluarse fuera de su capa.
"""


class InvalidPDFError(Exception):
    """El archivo recibido no cumple las reglas de un PDF válido."""


class DuplicatePDFError(Exception):
    """Ya existe un PDF registrado con el mismo checksum."""


class PDFNotFoundError(Exception):
    """No existe un PDF con el identificador solicitado."""
