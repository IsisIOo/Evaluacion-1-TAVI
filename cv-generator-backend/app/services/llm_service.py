# servicio para manejar la interacción con el modelo de lenguaje (LLM) y generar el contenido del CV a partir de la información del usuario
from app.core.llm_factory import get_deterministic_llm, get_creative_llm
from app.schemas.cv_response import CVResponse
from app.core.observability import AsyncObservabilityCallback

# [Para Toto]: para acceder a los modelos dentro de una función usa:
llm_estricto = get_deterministic_llm()
llm_creativo = get_creative_llm()

# [Para Toto]: la salida es un json cuya estructura debes definir en schemas/cv_response.py
# con este comando aseguras que el LLM respete esa estructura
modelo_con_formato = llm_estricto.with_structured_output(CVResponse)

# [Para Toto]: cuando llames al modelo, asegúrate de pasarle el callback para que registre la información de uso:
observability_callback = AsyncObservabilityCallback(user_id="user123")
respuesta = await modelo_con_formato.ainvoke(
    "Tu prompt aquí",
    config=["callbacks": observability_callback]
)