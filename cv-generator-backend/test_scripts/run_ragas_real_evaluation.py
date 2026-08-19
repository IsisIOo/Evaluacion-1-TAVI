import asyncio
import csv
import json
import os
import statistics
import sys

from dotenv import load_dotenv
from openai import AsyncOpenAI

from ragas.llms import llm_factory
from ragas.metrics.collections import (
    ContextPrecision,
    ContextRecall,
    ContextRelevance,
)

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


# ============================================================
# RUTAS
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("No se encontró GROQ_API_KEY en el .env")


# ============================================================
# CONFIGURACIÓN RAGAS
# ============================================================

groq_client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

ragas_juez = llm_factory(
    "openai/gpt-oss-20b",
    client=groq_client,
)

evaluador_precision = ContextPrecision(
    llm=ragas_juez
)

evaluador_recall = ContextRecall(
    llm=ragas_juez
)

evaluador_relevancia = ContextRelevance(
    llm=ragas_juez
)


# ============================================================
# CASOS
# ============================================================

CASOS = [
    {
        "nombre": "Desarrollador Backend",
        "query": (
            "Desarrollador Backend con experiencia "
            "en Python, APIs REST, SQL y Docker"
        ),
        "reference": (
            "Oferta laboral para Desarrollador Backend "
            "con experiencia en Python, desarrollo de APIs, "
            "bases de datos SQL y Docker."
        ),
    },

    {
        "nombre": "Analista de Datos",
        "query": (
            "Analista de Datos con experiencia en Python, "
            "Pandas, NumPy, SQL y Excel"
        ),
        "reference": (
            "Oferta laboral para Analista de Datos "
            "con experiencia en Python, análisis de datos, "
            "Pandas, SQL y herramientas de reportes."
        ),
    },

    {
        "nombre": "Desarrollador Full Stack",
        "query": (
            "Desarrollador Full Stack con experiencia "
            "en React, JavaScript, Python, Flask y PostgreSQL"
        ),
        "reference": (
            "Oferta laboral para Desarrollador Full Stack "
            "con experiencia en desarrollo frontend y backend, "
            "React, JavaScript, Python y bases de datos."
        ),
    },

    {
        "nombre": "Ingeniero DevOps",
        "query": (
            "Ingeniero DevOps con experiencia en Docker, "
            "Linux, CI/CD, Git y AWS"
        ),
        "reference": (
            "Oferta laboral para Ingeniero DevOps "
            "con experiencia en automatización, Docker, "
            "Linux, integración continua y servicios cloud."
        ),
    },

    {
        "nombre": "Analista QA",
        "query": (
            "Analista QA con experiencia en testing, "
            "Selenium, Postman, SQL y Jira"
        ),
        "reference": (
            "Oferta laboral para Analista QA "
            "con experiencia en pruebas de software, "
            "automatización, testing y documentación de errores."
        ),
    },

    {
        "nombre": "Administrador de Sistemas",
        "query": (
            "Administrador de Sistemas con experiencia "
            "en Linux, Windows Server, redes y Bash"
        ),
        "reference": (
            "Oferta laboral para Administrador de Sistemas "
            "con experiencia en administración de servidores, "
            "Linux, Windows y redes."
        ),
    },

    {
        "nombre": "Soporte TI",
        "query": (
            "Especialista en Soporte TI con experiencia "
            "en Windows, Linux, redes y hardware"
        ),
        "reference": (
            "Oferta laboral para Soporte TI "
            "con experiencia en soporte técnico, "
            "resolución de incidencias y atención a usuarios."
        ),
    },

    {
        "nombre": "Ingeniero de Software",
        "query": (
            "Ingeniero de Software con experiencia "
            "en Java, Python, SQL, Git, Docker y APIs REST"
        ),
        "reference": (
            "Oferta laboral para Ingeniero de Software "
            "con experiencia en desarrollo y mantenimiento "
            "de sistemas, programación y APIs."
        ),
    },

    {
        "nombre": "Analista de Sistemas",
        "query": (
            "Analista de Sistemas con experiencia "
            "en levantamiento de requerimientos, UML, SQL "
            "y metodologías ágiles"
        ),
        "reference": (
            "Oferta laboral para Analista de Sistemas "
            "con experiencia en análisis de requerimientos, "
            "documentación, diseño de soluciones y metodologías ágiles."
        ),
    },

    {
        "nombre": "Ingeniero de Datos",
        "query": (
            "Ingeniero de Datos con experiencia "
            "en Python, SQL, PostgreSQL, Pandas y ETL"
        ),
        "reference": (
            "Oferta laboral para Ingeniero de Datos "
            "con experiencia en procesamiento de datos, "
            "SQL, Python, ETL y construcción de pipelines."
        ),
    },
]


# ============================================================
# CHROMADB
# ============================================================

def cargar_chromadb():

    data_dir = os.path.join(
        BACKEND_ROOT,
        "data"
    )

    pointer_path = os.path.join(
        data_dir,
        "active_pointer.json"
    )

    print(f"   Data: {data_dir}")

    if not os.path.exists(pointer_path):
        raise FileNotFoundError(
            f"No existe: {pointer_path}"
        )

    with open(
        pointer_path,
        "r",
        encoding="utf-8"
    ) as f:

        active_store = json.load(f).get(
            "active",
            "blue"
        )

    vector_dir = os.path.join(
        data_dir,
        f"vector_store_{active_store}"
    )

    print(f"   Vector store activo: {active_store}")
    print(f"   ChromaDB: {vector_dir}")

    if not os.path.exists(vector_dir):
        raise FileNotFoundError(
            f"No existe el vector store: {vector_dir}"
        )

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    db = Chroma(
        persist_directory=vector_dir,
        embedding_function=embeddings,
    )

    return db


# ============================================================
# EVALUAR UN CASO
# ============================================================

async def evaluar_caso(caso, numero, db):

    print("\n" + "=" * 70)
    print(
        f"CASO {numero}/10: {caso['nombre']}"
    )
    print("=" * 70)

    query = caso["query"]

    print("\n→ Consulta:")
    print(query)

    print("\n→ Buscando documentos en ChromaDB...")

    documentos = db.similarity_search(
        query,
        k=3
    )

    print(
        f"→ Contextos recuperados: "
        f"{len(documentos)}"
    )

    if not documentos:
        print("⚠ No se recuperaron documentos.")
        return None

    # --------------------------------------------------------
    # Mostrar documentos
    # --------------------------------------------------------

    for i, doc in enumerate(
        documentos,
        start=1
    ):

        print(
            f"\n--- Contexto {i} ---"
        )

        print(
            doc.page_content[:1000]
        )

    # --------------------------------------------------------
    # RAGAS
    # --------------------------------------------------------

    contextos = [
        doc.page_content
        for doc in documentos
    ]

# --------------------------------------------------------
# RAGAS
# --------------------------------------------------------

    print(
        "\n→ Evaluando Context Precision..."
    )

    resultado_precision = await evaluador_precision.ascore(
        user_input=query,
        retrieved_contexts=contextos,
        reference=caso["reference"],
    )

    precision = resultado_precision.value

    print(
        f"→ Context Precision: {precision:.3f}"
    )


    print(
        "\n→ Evaluando Context Relevance..."
    )

    resultado_relevancia = await evaluador_relevancia.ascore(
        user_input=query,
        retrieved_contexts=contextos,
    )

    relevancia = resultado_relevancia.value

    print(
        f"→ Context Relevance: {relevancia:.3f}"
    )


    print(
        "\n→ Evaluando Context Recall..."
    )

    resultado_recall = await evaluador_recall.ascore(
        user_input=query,
        retrieved_contexts=contextos,
        reference=caso["reference"],
    )

    recall = resultado_recall.value

    print(
        f"→ Context Recall: {recall:.3f}"
    )

    return {
    "caso": numero,
    "perfil": caso["nombre"],
    "context_precision": precision,
    "context_relevance": relevancia,
    "context_recall": recall,
    "contextos": len(contextos),
    }


# ============================================================
# MAIN
# ============================================================

async def main():

    print("\n" + "=" * 70)
    print("EVALUACIÓN RAGAS - RETRIEVAL")
    print("=" * 70)

    print(
        "\n→ Inicializando ChromaDB..."
    )

    db = cargar_chromadb()

    resultados = []

    for numero, caso in enumerate(
        CASOS,
        start=1
    ):

        try:

            resultado = await evaluar_caso(
                caso,
                numero,
                db
            )

            if resultado:
                resultados.append(
                    resultado
                )

        except Exception as e:

            print(
                f"\n⚠ Error en caso "
                f"{numero}: {e}"
            )

    # ========================================================
    # RESULTADOS
    # ========================================================

    if not resultados:

        print(
            "\nNo se obtuvieron resultados."
        )

        return

    precisions = [
    r["context_precision"]
    for r in resultados
    ]   

    relevances = [
        r["context_relevance"]
        for r in resultados
    ]

    recalls = [
        r["context_recall"]
        for r in resultados
    ]

    promedio_precision = statistics.mean(precisions)
    promedio_relevancia = statistics.mean(relevances)
    promedio_recall = statistics.mean(recalls)

    desviacion_precision = (
        statistics.stdev(precisions)
        if len(precisions) > 1
        else 0
    )

    desviacion_relevancia = (
        statistics.stdev(relevances)
        if len(relevances) > 1
        else 0
    )

    desviacion_recall = (
        statistics.stdev(recalls)
        if len(recalls) > 1
        else 0
        )

    print("\n")
    print("=" * 70)
    print("RESULTADOS FINALES")
    print("=" * 70)

    for r in resultados:

        print(
            f"Caso {r['caso']:02d} | "
            f"{r['perfil']:<30} | "
            f"Precision: {r['context_precision']:.3f} | "
            f"Relevance: {r['context_relevance']:.3f} | "
            f"Recall: {r['context_recall']:.3f}"
        )

    print("-" * 70)

    print(
        f"Context Precision promedio: "
        f"{promedio_precision:.3f}"
    )

    print(
        f"Context Relevance promedio: "
        f"{promedio_relevancia:.3f}"
    )

    print(
        f"Context Recall promedio:    "
        f"{promedio_recall:.3f}"
    )

    print("-" * 70)

    print(
        f"Desv. Precision: {desviacion_precision:.3f}"
    )

    print(
        f"Desv. Relevance: {desviacion_relevancia:.3f}"
    )

    print(
        f"Desv. Recall:    {desviacion_recall:.3f}"
    )

    print("=" * 70)

    # ========================================================
    # CSV
    # ========================================================

    ruta_csv = os.path.join(
        os.path.dirname(__file__),
        "resultados_ragas_retrieval.csv"
    )

    with open(
        ruta_csv,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "caso",
                "perfil",
                "context_precision",
                "context_relevance",
                "context_recall",
                "contextos",
            ],
        )

        writer.writeheader()

        writer.writerows(
            resultados
        )

    print(
        "\nResultados guardados en:"
    )

    print(ruta_csv)


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())