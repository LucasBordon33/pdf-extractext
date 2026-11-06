class InvalidPDFError(Exception):
    """El archivo recibido no cumple las reglas de un PDF válido."""


class DuplicatePDFError(Exception):
    """Ya existe un PDF registrado con el mismo checksum."""


class PDFNotFoundError(Exception):
    """No existe un PDF con el identificador solicitado."""
