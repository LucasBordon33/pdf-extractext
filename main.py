from fastapi import FastAPI

from interfaces.routers.pdf_router import router as pdf_router

# Crear aplicación FastAPI
app = FastAPI(title="PDF Extractext API", version="1.0.0")

# Registrar el router del stack nuevo. Nada se instancia al importar:
# el composition root (interfaces/dependencies.py) compone los casos de
# uso con sus adaptadores por request, vía Depends(get_pdf_controller),
# y la conexión a Mongo es diferida (config.settings.get_db()).
app.include_router(pdf_router)

@app.get("/")
def leer_raiz():
    return {"mensaje": "¡El servidor de extracción de PDFs está funcionando!"}

