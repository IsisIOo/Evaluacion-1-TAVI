# Evaluacion-1-TAVI
Desarrollo de la evaluación n°1 de **Taller de agentes virtuales inteligentes**

## Descripción
Aquí se irá subiendo el código y/o documentación necesaria para la evaluación.

## Estado
En desarrollo.

## Estructura
- `/cv-generator-backend`: FastAPI + LangChain
- `/cv-generator-frontend`: Vue 3 + Vuetify

## Requisitos
- Python 3.14+
- Node.js (versión LTS)
- MongoDB (local o Atlas)

## Instalación rápida
1. **Backend:** `cd cv-generator-backend && pip install -r requirements.txt <- cuidado, escrito con pip freeze`
2. **Frontend:** `cd cv-generator-frontend && npm install`

## Correr FastAPI Backend
uvicorn cv-generator-backend.app.main:app --reload