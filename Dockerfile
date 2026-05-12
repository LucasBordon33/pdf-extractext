# Descarga una imagen oficial que ya tiene instalada la herramienta uv
# Le pone el apodo "builder" para la primera etapa.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Crea una carpeta llamada /app dentro del sistema de archivos del contenedor y 
# se "mete" en ella. Todos los comandos que sigan ocurrirán dentro de esta carpeta.
WORKDIR /app

# Copiamos los archivos del proyecto.
# .dockerignore evita que copiemos cosas innecesarias o privadas
COPY . .

# Ejecuta la instalación de las librerías de Python.
# Frozen le dice que respete estrictamente el archivo uv.lock para que no instale versiones sorpresa.
# --no--dev evita instalar herramientas de desarrollo (como librerías de testing) para ahorrar espacio.
RUN uv sync --frozen --no-dev

# Arranca de cero una segunda etapa "runner" con un mini-Linux que solo tiene Python.
FROM python:3.12-slim-bookworm AS runner

# Vuelve a crear y posicionarse en la carpeta /app.
WORKDIR /app

# 1. Traemos el entorno virtual ya hecho desde el builder
COPY --from=builder /app/.venv /app/.venv

# 2. Copiamos el código fuente de nuestra PC al runner
# (Nuevamente, el .dockerignore evita que se copie basura)
COPY . .

# "Activa" el entorno virtual de forma automática. Le dice al Linux interno que busque primero en .venv cuando ejecute python
ENV PATH="/app/.venv/bin:${PATH}"

# Le prohíbe a Python generar esos archivos ocultos .pyc que en un contenedor son inútiles y solo ocupan espacio.
ENV PYTHONDONTWRITEBYTECODE=1

# Fuerza a que todos los mensajes de la consola (como los print() o los errores) 
# Se muestren instantáneamente en tu pantalla sin quedarse atascados en la memoria intermedia de Linux.
ENV PYTHONUNBUFFERED=1

# Le avisa a quien lea el archivo que esta aplicación tiene la intención de comunicarse por el puerto 8000 (Solo informativo)
EXPOSE 8000

# Comando por defecto que se ejecuta cuando el contenedor "despierta". Enciende el servidor FastAPI, exponiéndolo a cualquier IP (0.0.0.0) en el puerto 8000.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
