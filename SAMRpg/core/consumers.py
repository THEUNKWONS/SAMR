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
        triaje_id = event.get('triaje_id')
        especialidad_requerida = event.get('especialidad_requerida', 'General')

        # Enviar al WebSocket
        await self.send(text_data=json.dumps({
            'type': 'alerta_emergencia',
            'message': message,
            'paciente': paciente,
            'nivel': nivel,
            'triaje_id': triaje_id,
            'especialidad_requerida': especialidad_requerida
        }))

    async def chat_message_paciente(self, event):
        # Reenviar mensaje de chat del paciente al médico
        await self.send(text_data=json.dumps({
            'type': 'chat_message_paciente',
            'message': event['message'],
            'paciente': event.get('paciente', 'Paciente'),
            'triaje_id': event.get('triaje_id')
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

    async def emergencia_medica(self, event):
        await self.send(text_data=json.dumps({
            'type': 'emergencia_medica',
            'message': event['message']
        }))
