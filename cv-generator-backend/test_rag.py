import json
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# 1. Rutas a la base de datos
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
POINTER_PATH = os.path.join(DATA_DIR, "active_pointer.json")

def main():
    print("- Iniciando prueba de búsqueda en el RAG (Local)...\n")

    # 2. Leer qué base de datos está activa actualmente
    if not os.path.exists(POINTER_PATH):
        print("❌ No se encontró el puntero. Corre update_rag.py primero.")
        return

    with open(POINTER_PATH, "r") as f:
        active_store = json.load(f).get("active", "blue")
    
    vector_dir = os.path.join(DATA_DIR, f"vector_store_{active_store}")
    print(f"- Conectando a la base de datos activa: [{active_store.upper()}]")

    # 3. Cargar el modelo local
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory=vector_dir, embedding_function=embeddings)

    print(f"- La base de datos tiene actualmente {db._collection.count()} ofertas guardadas.\n")

    # ---------------------------------------------------------
    # ZONA DE PRUEBAS
    # ---------------------------------------------------------
    pregunta = "Busco un trabajo donde pueda usar mis conocimientos de Python, bases de datos SQL y creación de APIs."
    
    print(f"🗣️  Buscando ofertas para el perfil: '{pregunta}'\n")

    # Pedimos los 3 mejores resultados (k=3)
    resultados = db.similarity_search(pregunta, k=3)

    for i, doc in enumerate(resultados):
        print(f"- RESULTADO {i+1} (Área: {doc.metadata.get('area_trabajo')}):")
        print(f"   {doc.page_content}\n")
        print("-" * 50)

if __name__ == "__main__":
    main()