import os
import sys

# Asegurar que Python reconozca la carpeta 'app'
base_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(base_dir)

from app.schemas.cv_request import CVRequest, PersonalInfo, PerfilInfo
from app.services.llm_service import _get_relevant_jobs

def main():
    print("🤖 Iniciando prueba aislada del Retriever (RAG)...")
    
    # 1. Armamos un CVRequest de mentira con palabras clave
    dummy_request = CVRequest(
        user_id="test_01",
        personal=PersonalInfo(
            nombre_completo="Prueba", profesion="Dev", email="a@a.cl", 
            telefono="123", linkedin="x", rut="1", ciudad="STG"
        ),
        perfil=PerfilInfo(
            anios_experiencia=2,
            experticia="Desarrollo Backend y creación de APIs con Python",
            propuesta_valor="Soy programador"
        ),
        experiencias=[],
        formacion=[],
        # Aquí ponemos las habilidades clave que el Retriever usará para buscar
        habilidades="Python, SQL, FastAPI, Git, Docker" 
    )

    # 2. Llamamos a nuestra nueva función
    resultado = _get_relevant_jobs(dummy_request)
    
    # 3. Imprimimos lo que encontró
    print("\n" + "="*50)
    print("📄 RESULTADO DEL CONTEXTO RECUPERADO:")
    print("="*50)
    print(resultado)
    print("="*50)

if __name__ == "__main__":
    main()