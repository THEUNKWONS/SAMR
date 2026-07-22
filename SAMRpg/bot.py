import os
import discord
from openai import AsyncOpenAI
from dotenv import load_dotenv

# 1. Cargar las credenciales de tu .env
load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')
openai_key = os.getenv('OPENAI_API_KEY')

# 2. Inicializar el cliente de OpenAI
cliente_openai = AsyncOpenAI(api_key=openai_key)

# 3. Configurar Discord
intents = discord.Intents.default()
intents.message_content = True
cliente_discord = discord.Client(intents=intents)

@cliente_discord.event
async def on_ready():
    print(f'✅ ¡OpenAI Dev-Mode en línea! Conectado como {cliente_discord.user}')
    print('✅ Llave de OpenAI cargada. Listo para revisar código de SAMR en Django.')

@cliente_discord.event
async def on_message(mensaje):
    # Radar en consola
    print(f"📥 Mensaje de [{mensaje.author}]: {mensaje.content}")

    # Evitar bucles
    if mensaje.author == cliente_discord.user:
        return

    async with mensaje.channel.typing():
        try:
            # Enviar el mensaje a ChatGPT
            respuesta = await cliente_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un desarrollador Senior experto en Arquitectura de Software, Python, Django, Docker, Git y diseño UI/UX. Estás en el servidor de Discord del equipo para ayudar a construir el proyecto SAMR (Sistema de Atención Médica Remota). Da respuestas directas, sin rodeos y con código limpio."},
                    {"role": "user", "content": mensaje.content}
                ]
            )
            texto_respuesta = respuesta.choices[0].message.content
            
            # Cortar mensajes largos para Discord
            if len(texto_respuesta) > 2000:
                for chunk in [texto_respuesta[i:i+1990] for i in range(0, len(texto_respuesta), 1990)]:
                    await mensaje.channel.send(chunk)
            else:
                await mensaje.channel.send(texto_respuesta)
            
            print("📤 Respuesta enviada con éxito.")
            
        except Exception as error:
            print(f"❌ Error crítico en OpenAI: {error}")
            await mensaje.channel.send("Se rompió la Matrix de OpenAI. Revisa la terminal.")

# 4. A correr
cliente_discord.run(discord_token)