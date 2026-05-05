# ── Dev Container: imagen de desarrollo para el backend Django ──
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Herramientas útiles para el desarrollo colaborativo
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    sudo \
    bash-completion \
  && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para VS Code
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=${USER_UID}
RUN groupadd --gid ${USER_GID} ${USERNAME} \
  && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} -s /bin/bash \
  && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Instalar dependencias de Python
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
  && pip install --no-cache-dir coverage debugpy

USER ${USERNAME}
