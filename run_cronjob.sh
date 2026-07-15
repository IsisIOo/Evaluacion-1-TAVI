#!/bin/bash

# 1. busca la ruta del proyecto y navega a ella
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$PROJECT_DIR"

# 2. carga las variables de entorno desde el archivo .env
# espera encontrar
# PYTHON_PATH: la ruta al ejecutable de Python que se usará para ejecutar el script
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "Error: .env file not found!"
    exit 1
fi

# exit con error si PYTHON_PATH no está definido
if [ -z "$PYTHON_PATH" ]; then
    echo "Error: PYTHON_PATH is not defined in .env file!"
    exit 1
fi

# 3. ejecuta el script
"$PYTHON_PATH" cv-generator-backend/pipeline/scraper.py