import json
import os
import shutil
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configurar rutas 
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
JSONL_PATH = os.path.join(DATA_DIR, "datos_ofertas.jsonl")
POINTER_PATH = os.path.join(DATA_DIR, "active_pointer.json")
BLUE_DIR = os.path.join(DATA_DIR, "vector_store_blue")
GREEN_DIR = os.path.join(DATA_DIR, "vector_store_green")

def main():
    print("- Iniciando actualización masiva de la Base de Datos Vectorial...")

    os.makedirs(DATA_DIR, exist_ok=True)

    active_store = "blue"
    if os.path.exists(POINTER_PATH):
        with open(POINTER_PATH, "r") as f:
            data = json.load(f)
            active_store = data.get("active", "blue")

    target_store = "green" if active_store == "blue" else "blue"
    target_dir = GREEN_DIR if target_store == "green" else BLUE_DIR

    print(f"- Store activo: [{active_store.upper()}]. Construyendo en: [{target_store.upper()}]...")

    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)

    # Leer el JSONL
    if not os.path.exists(JSONL_PATH):
        print(f"❌ Error: No se encontró el archivo {JSONL_PATH}")
        return

    documents = []
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                oferta = json.loads(line)
                contenido = oferta.get("descripcion", oferta.get("texto_para_llm", ""))
                area = oferta.get("area_trabajo", "General")
                
                if not contenido or len(str(contenido)) < 10:
                    continue
                    
                doc = Document(page_content=str(contenido), metadata={"area_trabajo": str(area)})
                documents.append(doc)
            except json.JSONDecodeError:
                pass

    total_docs = len(documents)
    print(f"✅ Se validaron {total_docs} ofertas de trabajo reales.")

    if total_docs == 0:
        return

    # Vectorizar OFFLINE con HuggingFace (Sin límites de API)
    print("- Cargando modelo de IA local...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print(f"- Procesando {total_docs} ofertas a máxima velocidad usando el procesador de tu PC...")
    
    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=target_dir
    )

    # Actualizar el puntero
    with open(POINTER_PATH, "w") as f:
        json.dump({"active": target_store}, f)

    print(f"\n- Éxito. La base de datos vectorial está lista en '{target_store}'.")

if __name__ == "__main__":
    main()