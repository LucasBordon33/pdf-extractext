from fastapi import FastAPI
from routers.pdf_router import PDFRouter

# Crear aplicación FastAPI
app = FastAPI(title="PDF Extractext API", version="1.0.0")

# Instanciar y registrar routers
pdf_router = PDFRouter()
app.include_router(pdf_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
