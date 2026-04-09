from typing import Dict, Any, Optional
from datetime import datetime


class DatabaseRepository:
    def __init__(self):
        self._documents = {}
        self._counter = 0

    async def save_document(self, document_data: Dict[str, Any]) -> str:
        self._counter += 1
        doc_id = f"doc_{self._counter}"

        document_data["_id"] = doc_id
        document_data["created_at"] = datetime.utcnow().isoformat()

        self._documents[doc_id] = document_data

        return doc_id

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self._documents.get(doc_id)

    async def get_all_documents(self) -> list:
        return list(self._documents.values())
