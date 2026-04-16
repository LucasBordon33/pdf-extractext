from fastapi import FastAPI
from api.router import router
from services import interfaz

# Informacion para documentacion automatica con FastAPI
app = FastAPI(
    title="PDF Extractext",
    description="API para extraer texto de PDFs y generar resúmenes con IA",
    version="1.0.0",
)

# Agrega las rutas de la API a router
app.include_router(router)

# Mensaje bienvenida 
@app.get("/")
async def root():
    return {
        "message": "Bienvenido a PDF Extractext",
        "docs": "/docs",
        "version": "1.0.0",
    }


interfaz.main()
