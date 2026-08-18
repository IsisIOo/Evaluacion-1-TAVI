import json
import os
import warnings
from datasets import Dataset
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from ragas import evaluate
from ragas.metrics import AnswerRelevancy, Faithfulness

# Cargar variables de entorno desde el archivo .env
load_dotenv()


def run_evaluation():
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        warnings.warn(
            "GROQ_API_KEY no encontrada en el .env. Asegúrate de definirla."
        )
        return

    # 1. Inicializar el Juez LLM y Embeddings para Ragas
    juez_llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        api_key=groq_api_key,
        temperature=0.0,
    )

    # Embeddings locales para calcular la métrica AnswerRelevancy
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("Juez y modelo de embeddings inicializados...")

    # 2. Leer oferta de trabajo del JSONL
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

    print("Preparando dataset de Ragas...")

    # 3. Preparar los datos de prueba
    data_samples = {
        "question": [
            f"Optimiza este perfil para la siguiente oferta laboral en Chile: {oferta_texto}"
        ],
        "contexts": [[
            "Profesional del área TI con 3 años de experiencia en desarrollo de software.",
            "Conocimientos intermedios en lenguajes orientados a objetos y bases de datos relacionales.",
            "Experiencia trabajando en equipos bajo metodologías ágiles (Scrum).",
        ]],
        "answer": [
            "Desarrollador de software con más de 3 años de trayectoria creando soluciones tecnológicas. "
            "Poseo un sólido manejo de bases de datos relacionales y programación orientada a objetos. "
            "Destaco por mi capacidad para integrarme rápidamente a equipos multidisciplinarios utilizando metodologías ágiles como Scrum, asegurando la entrega continua de valor."
        ],
    }

    dataset = Dataset.from_dict(data_samples)

    print("Iniciando evaluación...")
    resultado = evaluate(
        dataset=dataset,
        metrics=[Faithfulness(), AnswerRelevancy()],
        llm=juez_llm,
        embeddings=embeddings,
    )

    print("\nRESULTADOS DE LA EVALUACIÓN:")
    print(resultado)


if __name__ == "__main__":
    run_evaluation()