# SAMR-44 · US-4.3 — Lecturas Continuas de Dispositivos IoT al Motor ML

> **Rama:** `SAMR-44-US-4.3-Como-paciente-monitoreado-quiero-que-mis-dispositivos-envíen-lecturas-continuas-al-Motor-ML`  
> **Épica:** SAMR-4 — Telemetría IoT, Monitoreo Predictivo y Machine Learning  
> **Rol:** Capa de Base de Datos & Persistencia  
> **Fecha de implementación:** 2026-07-20  
> **Estado:** ✅ Implementado (infraestructura de persistencia) · 🔲 Extensión recomendada (pipeline ML en tiempo real)

---

## 1. Historia de Usuario

```
Como paciente monitoreado con biosensores domiciliarios,
quiero que mis dispositivos IoT (EKG, EEG, pulsioxímetro, glucómetro)
envíen lecturas continuas de mis signos vitales al Motor de Machine Learning,
para que el sistema detecte anomalías en tiempo real,
emita alertas tempranas antes de que una emergencia sea crítica
y notifique automáticamente a mi médico especialista.
```

### Criterios de Aceptación

| # | Criterio | Mecanismo de Verificación |
|---|----------|--------------------------|
| CA-1 | El sistema tiene una tabla dedicada para almacenar datos de telemetría IoT | Modelo `Telemetria` en `core/models.py` |
| CA-2 | Los datos de telemetría se almacenan cifrados en reposo | `datosTelemetria` usa `EncryptedJSONField` (AES-256) |
| CA-3 | Cada lectura queda vinculada al paciente mediante ID seudonimizado | `Telemetria.paciente_id` (FK a `Paciente`, no PII directa) |
| CA-4 | Cada ingesta de telemetría genera un registro de auditoría inmutable | Signal `post_save` en `Telemetria` → `AuditLog` + SHA-256 |
| CA-5 | La última lectura de telemetría se usa como contexto para el motor de triaje IA | `chatbot_api` consulta `Telemetria.objects.filter(paciente=...).order_by('-timestamp').first()` |
| CA-6 | El sistema soporta comunicación en tiempo real mediante WebSockets | Django Channels + Daphne (`ws/dashboard/`, `ws/paciente/`) |
| CA-7 | El estado de procesamiento de cada lectura es rastreable | Campo `estadoProcesamiento` en `Telemetria` |
| CA-8 | Las anomalías detectadas disparan alertas al dashboard médico en tiempo real | `chatbot_api` publica en grupo WebSocket `medicos_dashboard` |

---

## 2. Problema que Resuelve

El modelo de atención médica tradicional es **reactivo**: el paciente espera a sentirse muy mal para buscar atención. Los biosensores domiciliarios permiten un modelo **predictivo**: monitorear constantemente los signos vitales y detectar anomalías **antes** de que se conviertan en emergencias graves.

Los riesgos que esta historia mitiga:

| Riesgo | Sin SAMR-IA | Con SAMR-IA + IoT |
|--------|-------------|-------------------|
| Infarto silencioso | Se detecta cuando el paciente colapsa | EKG detecta anomalía → alerta en minutos |
| Hipoglucemia nocturna | El paciente puede no despertar | Glucómetro envía alerta automática |
| Saturación de O₂ baja (SpO₂) | El paciente no sabe que está en riesgo | Pulsioxímetro supera umbral → alerta |
| Crisis epiléptica | Nadie es notificado | EEG detecta patrón → notifica familiar y médico |

---

## 3. Arquitectura IoT → ML → Alerta

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│               PIPELINE COMPLETO: BIOSENSOR → BD → ML → ALERTA                 │
└─────────────────────────────────────────────────────────────────────────────────┘

[DISPOSITIVOS IoT DEL PACIENTE]
  EKG  ─────┐
  EEG  ─────┤
  SpO₂ ─────┼──► POST /api/telemetria/ingest/  (endpoint propuesto)
  FC   ─────┤     ó WebSocket ws/telemetria/
  Glucosa ──┘

        │
        ▼
[CAPA DE PERSISTENCIA — core/models.py]
  Telemetria.objects.create(
      paciente_id    = <id_seudonimizado>,
      datosTelemetria= {"fc": 120, "spo2": 88, "ecg": [...]},  ← JSON cifrado AES-256
      umbralAnomalia = "CRITICO",
      estadoProcesamiento = "Pendiente"
  )

        │
        ▼ Signal post_save (signals.py)
[AUDIT LOG INMUTABLE]
  AuditLog: CREATED | Telemetria | id=X | SHA-256 hash

        │
        ▼ (Motor ML — propuesto en roadmap)
[PROCESAMIENTO ML]
  Analizar datosTelemetria → detectar patrón de anomalía
  Actualizar: estadoProcesamiento = "Procesado" | "Anomalía"

        │ Si anomalía detectada
        ▼
[NOTIFICACIÓN EN TIEMPO REAL — consumers.py]
  channel_layer.group_send("medicos_dashboard", {
      "type": "alerta_emergencia",
      "nivel": "critico",
      "message": "SpO₂ 88% en paciente #X — posible hipoxia"
  })

        │
        ▼ WebSocket ws/dashboard/
[DASHBOARD MÉDICO] ← recibe alerta en tiempo real
  MedicoDashboardConsumer.alerta_emergencia()
  → El médico ve la alerta sin refrescar la página
```

---

## 4. Implementación Existente — Archivos Analizados

### 4.1 Modelo de Persistencia: [`core/models.py`](../SAMRpg/core/models.py) — Clase `Telemetria`

Es la tabla central de esta historia. Almacena cada lectura enviada por los biosensores:

```python
class Telemetria(models.Model):
    # Vinculación seudonimizada al paciente (FK, no expone PII)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)

    # JSON con las lecturas del biosensor — CIFRADO AES-256 en reposo
    # Estructura esperada: {"fc": int, "spo2": int, "ecg": [...], "glucosa": float}
    datosTelemetria = EncryptedJSONField(blank=True, null=True)

    # Resultado del análisis de umbral clínico
    # Valores: "Normal", "Precaución", "Critico"
    umbralAnomalia = models.CharField(max_length=50)

    # Estado del pipeline de procesamiento ML
    # Valores: "Pendiente", "Procesado", "Anomalía"
    estadoProcesamiento = models.CharField(max_length=50, default='Pendiente')

    # Timestamp inmutable (auto_now_add) para series de tiempo
    timestamp = models.DateTimeField(auto_now_add=True)
```

**Esquema en base de datos:**

```sql
CREATE TABLE core_telemetria (
    id                   BIGINT       PRIMARY KEY AUTO_INCREMENT,
    paciente_id          BIGINT       NOT NULL REFERENCES core_paciente(id),
    datosTelemetria      TEXT         NULL,      -- JSON cifrado AES-256 (token Fernet)
    umbralAnomalia       VARCHAR(50)  NOT NULL,  -- "Normal" | "Precaución" | "Critico"
    estadoProcesamiento  VARCHAR(50)  NOT NULL DEFAULT 'Pendiente',
    timestamp            DATETIME     NOT NULL   -- auto_now_add, serie de tiempo
);
```

**Ejemplo de registro en BD (datos cifrados):**
```
id  | paciente_id | datosTelemetria        | umbralAnomalia | estadoProcesamiento | timestamp
1   | 3           | gAAAAABo7fk2Xm3Np...   | Critico        | Pendiente           | 2026-07-20 05:30:00
2   | 3           | gAAAAABo8gJ3Yn4Oq...   | Normal         | Procesado           | 2026-07-20 05:30:10
```

**Ejemplo del JSON descifrado (lo que contiene):**
```json
{
  "fc": 118,
  "spo2": 88,
  "ecg_ritmo": "taquicardia_sinusal",
  "presion_sistolica": 145,
  "presion_diastolica": 92,
  "glucosa": 320,
  "temperatura": 38.2,
  "frecuencia_respiratoria": 22,
  "dispositivo_id": "BIOSENS-ESP32-A4:CF:12:B7:6E:2A",
  "firmware_version": "2.1.4"
}
```

---

### 4.2 Auditoría Automática de Ingestas: [`core/signals.py`](../SAMRpg/core/signals.py)

Cada vez que se crea un registro en `core_telemetria`, el signal `post_save` dispara automáticamente un registro en `core_auditlog`:

```python
@receiver(post_save, sender=Telemetria)
def audit_telemetria(sender, instance, created, **kwargs):
    """
    Auditoría automática de cada ingesta IoT.
    Cumple ISO 27001 A.12.4.1: registrar QUIÉN creó/modificó QUÉ y CUÁNDO.
    El hash SHA-256 garantiza la inmutabilidad del registro de auditoría.
    """
    create_audit_log(sender, instance, created, **kwargs)

def create_audit_log(sender, instance, created, **kwargs):
    action = "CREATED" if created else "UPDATED"
    raw_data = f"{action}|{sender.__name__}|{instance.id}|{instance.__dict__.get('timestamp', '')}"
    crypto_hash = hashlib.sha256(raw_data.encode()).hexdigest()

    AuditLog.objects.create(
        action=action,
        model_name=sender.__name__,   # "Telemetria"
        object_id=str(instance.id),
        cryptographic_hash=crypto_hash
    )
```

**Resultado:** Por cada lectura IoT → 2 filas en la BD:
1. `core_telemetria` (el dato cifrado)
2. `core_auditlog` (el sello de trazabilidad)

---

### 4.3 Uso de Telemetría en el Motor de Triaje IA: [`core/views.py`](../SAMRpg/core/views.py) — `chatbot_api`

La última lectura de telemetría se inyecta automáticamente como contexto del paciente antes de llamar al LLM. Esto conecta el pipeline IoT con el motor de decisión de la IA:

```python
# views.py — chatbot_api (líneas 329-336)
from .models import Telemetria

# Recuperar la lectura más reciente del biosensor para este paciente
telemetria_info = "Sin telemetría reciente."
ultima_telemetria = Telemetria.objects.filter(
    paciente=paciente
).order_by('-timestamp').first()

if ultima_telemetria and ultima_telemetria.datosTelemetria:
    # El EncryptedJSONField descifra automáticamente el dato
    telemetria_info = str(ultima_telemetria.datosTelemetria)

# Este contexto se inyecta en el prompt del LLM
contexto_clinico = (
    f"Edad: {edad} años. Sexo: {sexo}. "
    f"Historial Clínico: {historial}. Alergias: {alergias}. "
    f"Telemetría actual: {telemetria_info}."  # ← Lecturas IoT en tiempo real
)
```

**Importancia:** El LLM recibe las lecturas actuales del biosensor junto con los síntomas reportados. Si el paciente dice "me siento bien" pero el EKG muestra taquicardia → la IA puede detectar la contradicción y elevar el nivel de alerta.

---

### 4.4 Notificación en Tiempo Real: [`core/consumers.py`](../SAMRpg/core/consumers.py)

El sistema usa **Django Channels** (WebSockets) para notificar al dashboard médico sin que el médico deba refrescar la página:

```python
class MedicoDashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # El médico se une al grupo de alertas al abrir el dashboard
        self.group_name = 'medicos_dashboard'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def alerta_emergencia(self, event):
        # Recibe alertas publicadas por chatbot_api o el motor de telemetría
        await self.send(text_data=json.dumps({
            'type':     'alerta_emergencia',
            'message':  event['message'],   # Resumen médico de la anomalía
            'paciente': event.get('paciente', 'Desconocido'),
            'nivel':    event.get('nivel', 'info')  # critico | medio | bajo
        }))
```

**Publicación desde el backend** (cuando una anomalía IoT es detectada):
```python
# views.py — chatbot_api (líneas ~415-433)
channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    "medicos_dashboard",
    {
        "type":      "alerta_emergencia",
        "message":   resumen_medico,
        "paciente":  nombre_paciente,
        "nivel":     nivel_alerta,
        "triaje_id": triage_log.id
    }
)
```

---

### 4.5 Configuración WebSocket: [`core/routing.py`](../SAMRpg/core/routing.py) + [`samr_project/asgi.py`](../SAMRpg/samr_project/asgi.py)

```python
# routing.py — Mapeo de rutas WebSocket
websocket_urlpatterns = [
    re_path(r'ws/dashboard/$', consumers.MedicoDashboardConsumer.as_asgi()),
    re_path(r'ws/paciente/$',  consumers.PacienteConsumer.as_asgi()),
]
```

```python
# asgi.py — Servidor ASGI con soporte HTTP + WebSocket
application = ProtocolTypeRouter({
    "http":      get_asgi_application(),          # Peticiones HTTP normales
    "websocket": AuthMiddlewareStack(             # WebSockets autenticados
        URLRouter(core.routing.websocket_urlpatterns)
    ),
})
```

El servidor **Daphne** (incluido en `requirements.txt`) maneja el protocolo ASGI para soportar conexiones WebSocket persistentes de larga duración.

---

## 5. Esquema Completo de Tablas Involucradas

```
core_paciente                        core_telemetria
─────────────                        ───────────────
id          PK ◄─── FK (paciente_id)─ id             PK
usuario_id  FK                         paciente_id    FK
                                       datosTelemetria [JSON CIFRADO]
                                         {"fc":118, "spo2":88, ...}
                                       umbralAnomalia   VARCHAR
                                       estadoProcesamiento VARCHAR
                                       timestamp        DATETIME (inmutable)
                                              │
                                              │ post_save signal
                                              ▼
                                       core_auditlog
                                       ─────────────
                                       id              PK
                                       timestamp       INMUTABLE
                                       action          "CREATED"
                                       model_name      "Telemetria"
                                       object_id       "42"
                                       cryptographic_hash SHA-256
```

---

## 6. Gap Analysis — Implementado vs. Propuesto para Producción

### ✅ Implementado (infraestructura base)

| Funcionalidad | Archivo | Estado |
|---|---|---|
| Tabla `core_telemetria` con JSON cifrado | `models.py` | ✅ |
| Auditoría automática por signal `post_save` | `signals.py` | ✅ |
| Inyección de telemetría en contexto del LLM | `views.py:chatbot_api` | ✅ |
| Notificación WebSocket al dashboard médico | `consumers.py` | ✅ |
| Servidor ASGI con soporte WebSocket | `asgi.py` + Daphne | ✅ |
| Cifrado AES-256 de los datos IoT en reposo | `fields.py:EncryptedJSONField` | ✅ |

### 🔲 Propuesto para Implementación Completa

#### a) Endpoint REST para Ingesta IoT (`/api/telemetria/ingest/`)

```python
# Propuesta en views.py:
@csrf_exempt
def ingest_telemetria(request):
    """
    Endpoint para recibir lecturas de biosensores IoT.
    Autenticación: API Key del dispositivo (no sesión de usuario).
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        api_key  = request.headers.get('X-Device-API-Key')
        paciente = validar_api_key_dispositivo(api_key)

        lectura = data.get('lectura', {})
        umbral  = evaluar_umbral_clinico(lectura)   # Motor ML

        Telemetria.objects.create(
            paciente          = paciente,
            datosTelemetria   = lectura,   # EncryptedJSONField cifra automáticamente
            umbralAnomalia    = umbral,
            estadoProcesamiento = 'Pendiente'
        )

        if umbral == 'Critico':
            notificar_dashboard_medico(paciente, lectura, umbral)

        return JsonResponse({'status': 'ok', 'umbral': umbral})
```

**URL propuesta en `urls.py`:**
```python
path('api/telemetria/ingest/', views.ingest_telemetria, name='ingest_telemetria'),
```

#### b) WebSocket Consumer para Telemetría en Streaming (`TelemetriaConsumer`)

```python
# Propuesta en consumers.py:
class TelemetriaConsumer(AsyncWebsocketConsumer):
    """
    Consumer para recibir lecturas IoT en streaming por WebSocket.
    Los dispositivos se conectan a ws/telemetria/<paciente_id>/
    y envían lecturas cada N segundos sin overhead HTTP.
    """
    async def connect(self):
        self.paciente_id = self.scope['url_route']['kwargs']['paciente_id']
        await self.accept()

    async def receive(self, text_data):
        lectura = json.loads(text_data)
        # Procesar y persistir lectura
        await self.persistir_telemetria(lectura)
        # Enviar confirmación al dispositivo
        await self.send(json.dumps({'status': 'ok'}))
```

**Ruta propuesta en `routing.py`:**
```python
re_path(r'ws/telemetria/(?P<paciente_id>\d+)/$', consumers.TelemetriaConsumer.as_asgi()),
```

#### c) Motor de Evaluación de Umbrales Clínicos

```python
# Propuesta en nuevo archivo core/ml_engine.py:
UMBRALES_CRITICOS = {
    'fc':          {'min': 40, 'max': 150},   # Frecuencia cardíaca (lpm)
    'spo2':        {'min': 90, 'max': 100},   # Saturación O₂ (%)
    'glucosa':     {'min': 60, 'max': 400},   # Glucemia (mg/dL)
    'temperatura': {'min': 35, 'max': 40},    # Temperatura corporal (°C)
    'presion_sistolica': {'min': 70, 'max': 180},
}

def evaluar_umbral_clinico(lectura: dict) -> str:
    """
    Evalúa si una lectura IoT supera umbrales clínicos.
    Retorna: 'Normal' | 'Precaución' | 'Critico'
    En producción: llamada al Motor ML con modelo predictivo entrenado.
    """
    for campo, limites in UMBRALES_CRITICOS.items():
        valor = lectura.get(campo)
        if valor is not None:
            if valor < limites['min'] or valor > limites['max']:
                return 'Critico'
    return 'Normal'
```

---

## 7. Resumen de Archivos Analizados

| Archivo | Acción | Descripción del rol en US-4.3 |
|---------|--------|-------------------------------|
| [`core/models.py`](../SAMRpg/core/models.py) | **USA / IMPLEMENTA** | Modelo `Telemetria` — tabla central de lecturas IoT con JSON cifrado |
| [`core/fields.py`](../SAMRpg/core/fields.py) | **PROVEE** | `EncryptedJSONField` — cifra los datos biométricos en reposo |
| [`core/signals.py`](../SAMRpg/core/signals.py) | **AUDITA** | Signal `post_save` en `Telemetria` → `AuditLog` automático |
| [`core/views.py`](../SAMRpg/core/views.py) | **CONSUME** | `chatbot_api` inyecta última telemetría en el contexto del LLM |
| [`core/consumers.py`](../SAMRpg/core/consumers.py) | **NOTIFICA** | `MedicoDashboardConsumer` recibe alertas IoT vía WebSocket |
| [`core/routing.py`](../SAMRpg/core/routing.py) | **ENRUTA** | `ws/dashboard/` y `ws/paciente/` — rutas WebSocket activas |
| [`samr_project/asgi.py`](../SAMRpg/samr_project/asgi.py) | **CONFIGURA** | Protocolo dual HTTP + WebSocket con Daphne |
| `core/views.py` | 🔲 **PROPUESTO** | Endpoint `POST /api/telemetria/ingest/` para dispositivos IoT |
| `core/consumers.py` | 🔲 **PROPUESTO** | `TelemetriaConsumer` para streaming WebSocket desde biosensores |
| `core/ml_engine.py` | 🔲 **PROPUESTO** | Motor de evaluación de umbrales clínicos |

---

## 8. Flujo de Datos Seguro End-to-End

```
Biosensor (ESP32 / Raspberry Pi)
  │ HTTPS POST + API Key del dispositivo
  ▼
Django REST API (/api/telemetria/ingest/)
  │ Validación de API Key → identificación del paciente
  ▼
EncryptedJSONField.get_prep_value()
  │ AES-256 cifra los datos biométricos
  ▼
core_telemetria (BD)
  │ Datos almacenados: token Fernet ilegible
  │
  ├─► Signal post_save → core_auditlog (SHA-256 hash)
  │
  └─► evaluar_umbral_clinico()
        │ Si CRITICO:
        ▼
      channel_layer.group_send("medicos_dashboard")
        │ WebSocket
        ▼
      Dashboard del médico (notificación push sin refresh)
        │
        ▼ Médico acepta → aceptar_triaje()
      TriageLog.estado_asignacion = "ATENDIDO"
        │ WebSocket ws/paciente/
        ▼
      Paciente recibe: "El Dr. X está revisando tu caso"
```

---

## 9. Cumplimiento Normativo

| Norma | Control | Implementación |
|-------|---------|----------------|
| **LOPDP Ecuador Art. 37** | Datos biométricos de salud | `EncryptedJSONField` cifra datos IoT en reposo |
| **ISO 27001 A.12.4** | Registro de eventos | Signal `post_save` → `AuditLog` por cada lectura |
| **ISO 27799 §9.5** | Integridad de datos clínicos en tiempo real | Hash SHA-256 en `AuditLog` + timestamp inmutable |
| **ISO/IEC 25010** | Eficiencia de desempeño (tiempo real) | Django Channels + Daphne (ASGI, no bloqueante) |
| **HIPAA §164.312(a)(2)(iv)** | Cifrado y descifrado de PHI | AES-256 via Fernet en `EncryptedJSONField` |

---

*Documentado por: Rol Base de Datos — SAMR-IA v1.0 | Historia SAMR-44 / US-4.3*  
*Estándares cubiertos: LOPDP Ecuador Art. 37, ISO 27001 A.12.4, ISO 27799 §9.5, ISO/IEC 25010*
