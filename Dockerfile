# 1. Imagen base: Python 3.11 sobre Debian Bullseye (Estabilidad garantizada)
FROM python:3.11-slim-bullseye

# 2. Variables de entorno para optimizar Python en Docker
# Evita que Python genere archivos .pyc (mantiene el contenedor limpio)
ENV PYTHONDONTWRITEBYTECODE=1
# Asegura que los logs se vean en tiempo real sin almacenamiento en búfer
ENV PYTHONUNBUFFERED=1

# 3. Directorio de trabajo siguiendo estándares de servicios en Linux (/srv)
WORKDIR /srv/emr-rendering-engine

# 4. Instalación de dependencias del sistema
# Necesitamos gcc y librerías de cliente MySQL para que Python hable con tu MariaDB/MySQL nativo
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 5. Instalación de dependencias de Python
# Copiamos primero solo el requirements para aprovechar el sistema de capas de Docker
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copiado de la estructura del proyecto
# Copiamos todo el contenido de la carpeta actual al contenedor
COPY . .

# 7. Exposición del puerto interno
# Gunicorn escuchará en el 8000 por defecto
EXPOSE 8000

# 8. Comando de ejecución de grado industrial
# --workers 4: Permite manejar múltiples reportes a la vez
# --timeout 300: Da 5 minutos para reportes pesados (las 200 variables pueden tardar en renderizar)
# app.main:app: Indica que busque el objeto 'app' dentro de 'app/main.py'
CMD ["gunicorn", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app.main:app"]