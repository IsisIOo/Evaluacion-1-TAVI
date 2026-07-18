import os
import sys

# 1. Configurar el path para que Python encuentre el módulo 'app'
# Subimos un nivel desde test_scripts hacia la raíz del backend
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

# 2. Importar la nueva función de recuperación desde tu servicio
from app.services.llm_service import _get_matching_job_offers

def main():
    print("🤖 Iniciando prueba aislada del Retriever (RAG)...\n")

    # 3. Simular la query exacta que construye tu API usando la concatenación
    # (Profesión + Experticia + Habilidades)
    query_prueba = "Desarrollador Backend Desarrollo web y APIs Python, Bases de Datos, Trabajo en equipo"
    
    print(f"🗣️ Buscando ofertas para la query: '{query_prueba}'\n")

    # 4. Ejecutar la función
    resultado = _get_matching_job_offers(query=query_prueba, k=3)

    # 5. Imprimir los resultados devueltos por el sistema Blue/Green
    print("=" * 70)
    print("📄 CONTEXTO RECUPERADO LISTO PARA EL LLM:")
    print("=" * 70)
    
    if resultado:
        print(resultado)
    else:
        print("❌ No se encontraron ofertas o hubo un error en la conexión.")
        
    print("=" * 70)

if __name__ == "__main__":
    main()