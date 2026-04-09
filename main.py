from fastapi import FastAPI
from api.router import router

app = FastAPI(
    title="PDF Extractext",
    description="API para extraer texto de PDFs y generar resúmenes con IA",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "Bienvenido a PDF Extractext",
        "docs": "/docs",
        "version": "1.0.0",
    }
