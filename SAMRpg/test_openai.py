import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'samr_project.settings')
django.setup()

from django.conf import settings
from openai import OpenAI
import json

client = OpenAI(api_key=settings.OPENAI_API_KEY)

system_instruction = (
    "Eres SAMR-IA, un asistente de triaje médico avanzado. Analiza los síntomas del paciente y devuelve SIEMPRE un JSON válido con la siguiente estructura exacta: "
    "{"
    "  \"nivel_alerta\": \"critico\", \"medio\" o \"bajo\"; "
    "  \"respuesta_paciente\": \"Mensaje empático\"; "
    "  \"resumen_medico\": \"Resumen técnico\""
    "}"
)

try:
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": "me duele el estomago demasiado"}
        ],
        response_format={"type": "json_object"}
    )
    print("Success:")
    print(response.choices[0].message.content)
except Exception as e:
    import traceback
    traceback.print_exc()
