ARG PYTHON_VERSION="3.14"

# Python
FROM python:${PYTHON_VERSION}-slim

ARG VERSION="0.0.0"

# Working directory
WORKDIR /app
COPY ./src/ ./src/
COPY ./alembic.ini .
COPY ./main.py .
COPY ./pyproject.toml .
COPY ./uv.lock .

# Environment variables
ENV GRANIAN_HOST="0.0.0.0"
ENV GRANIAN_INTERFACE="asgi"
ENV GRANIAN_LOOP="uvloop"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_CACHE=1
ENV UV_PYTHON_PREFERENCE="only-system"
ENV VERSION=$VERSION

# Update system dependencies
RUN apt-get update && apt-get upgrade -y

# Intall dependencies
RUN pip install --no-cache-dir --upgrade pip uv
RUN uv version --no-sync ${VERSION}
RUN uv export --frozen --no-default-groups > requirements.txt
RUN uv pip install -r requirements.txt --system

# Cleaning
RUN apt-get autoremove
RUN apt-get clean

EXPOSE ${GRANIAN_PORT:-8000}

CMD ["granian", "main:app"]
