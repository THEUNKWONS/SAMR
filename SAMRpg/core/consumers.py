import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MedicoDashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Unirse a un grupo general de médicos (simulación de panel)
        self.group_name = 'medicos_dashboard'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Recibir mensaje de un evento de grupo
    async def alerta_emergencia(self, event):
        message = event['message']
        paciente = event.get('paciente', 'Desconocido')
        nivel = event.get('nivel', 'info')

        # Enviar al WebSocket
        await self.send(text_data=json.dumps({
            'type': 'alerta_emergencia',
            'message': message,
            'paciente': paciente,
            'nivel': nivel
        }))

class PacienteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.group_name = f"paciente_{self.scope['user'].id}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def medico_conectado(self, event):
        await self.send(text_data=json.dumps({
            'type': 'medico_conectado',
            'message': event['message']
        }))

# SAMR-US-4.3: Consumidor de WebSocket para ingestión de telemetría IoT.
# Los dispositivos se conectan a esta ruta para transmitir sus datos en tiempo real.
from channels.db import database_sync_to_async

class IoTTelemetriaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        # Solo pacientes pueden enviar telemetría de sus propios dispositivos
        if user.is_anonymous or user.tipoUsuario != 'PACIENTE':
            await self.close()
            return
            
        self.paciente_id = user.perfil_paciente.id
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            # Guardamos la telemetría en base de datos.
            # El campo datosTelemetria está cifrado por defecto (US-4.2).
            # estadoProcesamiento se guarda como 'Pendiente' para que el Motor ML lo procese luego.
            await self.guardar_telemetria(data)
            
            await self.send(text_data=json.dumps({
                'status': 'success',
                'message': 'Lectura registrada y encolada para el Motor ML'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': str(e)
            }))

    @database_sync_to_async
    def guardar_telemetria(self, datos_json):
        from .models import Telemetria
        Telemetria.objects.create(
            paciente_id=self.paciente_id,
            datosTelemetria=datos_json,
            umbralAnomalia='Pendiente',
            estadoProcesamiento='Pendiente'
        )

