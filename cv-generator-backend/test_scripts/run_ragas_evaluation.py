import json
import os
import warnings
from dotenv import load_dotenv

# Sube DOS niveles para encontrar el .env
ruta_env = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(ruta_env)

# 1. CAMBIO CLAVE: Importamos AsyncOpenAI en lugar de OpenAI
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness

groq_api_key = os.getenv("GROQ_API_KEY")

async def run_evaluation():
    if not groq_api_key:
        warnings.warn("GROQ_API_KEY no encontrada en el .env. Asegúrate de definirla.")
        return

    # 2. CAMBIO CLAVE: Inicializamos el cliente asíncrono
    groq_client = AsyncOpenAI(
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1"
    )

    # Inicializar el juez y pasarlo a la métrica directamente
    ragas_juez = llm_factory("openai/gpt-oss-20b", client=groq_client)
    evaluador_fidelidad = Faithfulness(llm=ragas_juez)

    print("Juez y métrica inicializados...")

    # Leer oferta de trabajo del JSONL
    ruta_archivo = os.path.join(
        os.path.dirname(__file__), "..", "data", "datos_ofertas.jsonl"
    )

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            primera_oferta = json.loads(f.readline())
            oferta_texto = str(primera_oferta)
    except Exception as e:
        print(f"Error leyendo el JSONL ({e}). Usando oferta por defecto.")
        oferta_texto = "Oferta genérica de Desarrollador Backend"

    print("Iniciando evaluación...")

    # Datos directos
    pregunta = f"Optimiza este perfil para la siguiente oferta laboral en Chile: {oferta_texto}"
    
    contextos = [
        "Profesional del área TI con 3 años de experiencia en desarrollo de software.",
        "Conocimientos intermedios en lenguajes orientados a objetos y bases de datos relacionales.",
        "Experiencia trabajando en equipos bajo metodologías ágiles (Scrum)."
    ]
    
    respuestas = {
        "Respuesta 1 - fiel": (
            "Profesional del área TI con 3 años de experiencia en desarrollo de software. "
            "Cuenta con conocimientos intermedios en lenguajes orientados a objetos y bases de datos relacionales. "
            "Además, posee experiencia trabajando en equipos bajo metodologías ágiles como Scrum."
        ),

        "Respuesta 2 - agrega información": (
            "Desarrollador de software con más de 5 años de experiencia creando aplicaciones web. "
            "Poseo un dominio avanzado de Python, Java y PostgreSQL, además de experiencia trabajando "
            "con equipos multidisciplinarios mediante Scrum."
        ),

        "Respuesta 3 - mezcla información": (
            "Profesional TI con 3 años de experiencia en desarrollo de software y conocimientos "
            "intermedios en programación orientada a objetos y bases de datos relacionales. "
            "También tengo experiencia liderando equipos de desarrollo y trabajando con Docker."
        )
    }

    print("\nRESULTADOS DE LA EVALUACIÓN")

    for nombre, respuesta in respuestas.items():

        resultado = await evaluador_fidelidad.ascore(
            user_input=pregunta,
            retrieved_contexts=contextos,
            response=respuesta
        )

        print(f"\n--- {nombre} ---")
        print(f"Faithfulness Score: {resultado.value}")
        print(f"Razón: {resultado.reason}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_evaluation())


#Respuesta 1 = 1.0: toda la información está respaldada por los contextos.
#Respuesta 2 = 0.0: introduce información que no aparece en los contextos.
#Respuesta 3 = 0.6: mezcla información respaldada con información inventada/no recuperada.