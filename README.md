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
1. **Backend:** `cd cv-generator-backend && pip install -r requirements.txt` <- cuidado, escrito con pip freeze
2. **Frontend:** `cd cv-generator-frontend && npm install`

## Correr FastAPI Backend
uvicorn cv-generator-backend.app.main:app --reload

.








---

## 🚀 Instalación PASO A PASO

### 1️⃣ Clonar o descargar el repositorio

```bash
cd "/tu/ruta/Evaluacion-1-TAVI"
```

---

### 2️⃣ Crear archivo `.env` en la raíz del proyecto

**Ubicación**: `/Evaluacion-1-TAVI/.env`

Contenido:
```env
# Backend - MongoDB
MONGO_URI=mongodb://localhost:27017/cv_db
MONGO_DB_NAME=cv_db

# Backend - Google Gemini AI
GEMINI_API_KEY=tu_clave_api_de_gemini_aqui
MODEL_NAME=gemini-2.5-flash
MAX_TOKENS=1000

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
```

**Obtener GEMINI_API_KEY**:
1. Ve a https://aistudio.google.com/apikey
2. Haz clic en "Create API Key"
3. Copia la clave y pégala en `GEMINI_API_KEY`

---

### 3️⃣ Configurar y ejecutar MongoDB

**Terminal 1** (déjala corriendo):

```bash
# Crear directorio para datos de MongoDB
mkdir -p ~/mongodb_data

# Iniciar MongoDB
mongod --dbpath ~/mongodb_data
```

Deberías ver:
```
"Waiting for connections","port":27017
```

✅ MongoDB está listo.

---

### 4️⃣ Configurar e instalar Backend

**Terminal 2**:

```bash
cd cv-generator-backend

# Crear virtual environment
python3 -m venv venv

# Activar venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar .env al backend
cp ../.env .env
```

Si necesitas instalar `python3.12-venv`:
```bash
sudo apt install python3.12-venv
```

---

### 5️⃣ Ejecutar Backend

**Terminal 2** (con venv activo):

```bash
uvicorn app.main:app --reload
```

Deberías ver:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Conexión a MongoDB establecida
```

✅ Backend en http://localhost:8000
✅ Documentación en http://localhost:8000/docs

---

### 6️⃣ Configurar e instalar Frontend

**Terminal 3**:

```bash
cd cv-generator-frontend/tavi-cv-gen

# Instalar dependencias
npm install

# Instalar pdfmake (para exportar CV a PDF)
npm install pdfmake
```

---

### 7️⃣ Ejecutar Frontend

**Terminal 3**:

```bash
npm run serve
```

Deberías ver:
```
App running at:
- Local:   http://localhost:8080
```

✅ Frontend en http://localhost:3000 (o el puerto que muestre)

---

## 📊 Verificar que todo funciona

1. Abre http://localhost:8080 en tu navegador
2. Completa el formulario del CV
3. Presiona "Generar CV"
4. Deberías ver el CV generado

### Verificar datos en MongoDB

1. Abre **MongoDB Compass**: `mongodb://localhost:27017`
2. Base de datos: `cv_db`
3. Colección: `cvs`
4. Verifica que hay documentos guardados

---

## 📁 Archivos creados/modificados para persistencia

Durante el setup, se crearon/modificaron estos archivos:

### Backend - Persistencia en MongoDB:
- `/cv-generator-backend/app/db/models.py` - Modelos Pydantic para CV
- `/cv-generator-backend/app/db/cv_repository.py` - CRUD de CVs en MongoDB
- `/cv-generator-backend/app/api/v1/cv_endpoint.py` - Endpoints actualizados

### Endpoints disponibles:
- `POST /api/v1/generate` - Genera y guarda CV
- `GET /api/v1/{cv_id}` - Obtiene un CV por ID
- `GET /api/v1/user/{user_id}` - Obtiene todos los CVs de un usuario

---

## 🔧 Solución de problemas

### Error: `MONGO_URI field required`
- Verifica que `.env` existe en `/cv-generator-backend/.env`
- Asegúrate que MongoDB está corriendo (`mongod --dbpath ~/mongodb_data`)

### Error: `Module not found: pdfmake`
- Ejecuta: `npm install pdfmake`

### Error: `GenerativeModel not found`
- Actualiza el paquete: `pip install --upgrade google-generativeai`

### Error: `Proxy object could not be cloned`
- Es un problema frontend conocido. El CV se guardó en MongoDB correctamente, pero hay error en la navegación. Se arreglará próximamente.

---

## 📝 Notas de desarrollo

- El backend usa **Motor** (async MongoDB driver) para no bloquear el servidor
- Los CVs se guardan automáticamente con timestamp de creación/actualización
- La IA usa **Google Generative AI (Gemini)** para generar contenido
- El frontend usa **Vue 3** con **Vuetify** para UI

---

## 🚨 Importante

- ⚠️ **No commitear `.env`** - Ya está en `.gitignore`
- ⚠️ **No commitear `venv/`** - Ya está en `.gitignore`
- ⚠️ **No commitear `node_modules/`** - Ya está en `.gitignore`

---

## Próximas mejoras

- [ ] Arreglar error de "Proxy object could not be cloned" en el frontend
- [ ] Agregar autenticación de usuarios
- [ ] Agregar opción de descargar CV como PDF
- [ ] Agregar historial de CVs generados
- [ ] Validación más robusta del formulario