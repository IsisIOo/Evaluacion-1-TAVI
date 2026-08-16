import os
import warnings
from langchain_groq import ChatGroq
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevance
from datasets import Dataset

# Obtener la llave del entorno
groq_api_key = os.getenv("GROQ_API_KEY")

def run_evaluation():
    if not groq_api_key:
        warnings.warn("GROQ_API_KEY no encontrada en el .env. Saltando evaluación.")
        return

    # 1. Inicializar el Juez Evaluador
    juez_llm = ChatGroq(
        model_name="llama-3.3-70b-versatile", 
        api_key=groq_api_key,
        temperature=0.0
    )
    
    print("Juez inicializado. Preparando datos de prueba...")

    # 2. Aquí prepararemos el diccionario con los datos (Pregunta, Contextos, Respuesta)
    # data_samples = { ... }

# 2. Leer la primera oferta de trabajo del archivo JSONL
    ruta_archivo = os.path.join(os.path.dirname(__file__), '..', 'data', 'datos_ofertas.jsonl')
    
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            primera_oferta = json.loads(f.readline())
            oferta_texto = str(primera_oferta)
    except Exception as e:
        print(f"Error leyendo el JSONL: {e}")
        oferta_texto = "Oferta genérica de Desarrollador Backend"

    print("Preparando dataset de Ragas...")

    # 3. Preparar los datos de prueba con un perfil GENÉRICO
    data_samples = {
        "question": [f"Optimiza este perfil para la siguiente oferta laboral en Chile: {oferta_texto}"],
        
        # Contexto genérico simulado recuperado de la base de datos
        "contexts": [[
            "Profesional del área TI con 3 años de experiencia en desarrollo de software.",
            "Conocimientos intermedios en lenguajes orientados a objetos y bases de datos relacionales.",
            "Experiencia trabajando en equipos bajo metodologías ágiles (Scrum)."
        ]],
        
        # Respuesta genérica generada por el LLM
        "answer": [
            "Desarrollador de software con más de 3 años de trayectoria creando soluciones tecnológicas. "
            "Poseo un sólido manejo de bases de datos relacionales y programación orientada a objetos. "
            "Destaco por mi capacidad para integrarme rápidamente a equipos multidisciplinarios utilizando metodologías ágiles como Scrum, asegurando la entrega continua de valor."
        ]
    }

    # 3. Ejecutar Ragas
    # dataset = Dataset.from_dict(data_samples)
    # resultado = evaluate(dataset, llm=juez_llm, metrics=[faithfulness, answer_relevance])
    # print(resultado)

# 4. Convertir a formato HuggingFace y Ejecutar Ragas
    dataset = Dataset.from_dict(data_samples)
    
    print("Iniciando evaluación con Llama 3 (esto puede tomar unos segundos)...")
    resultado = evaluate(dataset, llm=juez_llm, metrics=[faithfulness, answer_relevance])
    
    print("\n RESULTADOS DE LA EVALUACIÓN")
    print(resultado)
    
if __name__ == "__main__":
    run_evaluation()