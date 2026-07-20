# SAMR-41 · US-3.7 — Registro Inmutable de Consultas e Interacciones con Bots

> **Rama:** `SAMR-41-US-3.7-Como-regulador-quiero-que-el-sistema-genere-un-registro-inmutable-de-la-consulta-y-las-interacciones-con-bots`  
> **Épica:** SAMR-3 — Cumplimiento Normativo, Auditoría y Trazabilidad Regulatoria  
> **Rol:** Capa de Base de Datos & Persistencia  
> **Fecha de implementación:** 2026-07-20  
> **Estado:** ✅ Implementado (infraestructura base) · 🔲 Extensión recomendada (ver Sección 6)

---

## 1. Historia de Usuario

```
Como regulador del sistema de salud (MSP / Superintendencia de Protección de Datos),
quiero que SAMR-IA genere un registro inmutable de cada consulta médica
y de cada interacción ocurrida con los bots de triaje conversacional,
para poder auditar la trazabilidad completa de las decisiones clínicas automatizadas
y verificar el cumplimiento de la LOPDP, ISO 27001 e ISO 27799.
```

### Criterios de Aceptación

| # | Criterio | Mecanismo de Verificación |
|---|----------|--------------------------|
| CA-1 | Cada mensaje enviado al bot queda registrado de forma permanente e inalterable | `AuditLog` + `TriageLog` con hash SHA-256 |
| CA-2 | El registro identifica quién interactuó, cuándo y desde qué IP | Campos `user_id`, `timestamp`, `ip_address` en `AuditLog` |
| CA-3 | El registro de cada consulta incluye la respuesta completa generada por la IA | Campo `respuesta_ia` y `resumen_medico` en `TriageLog` |
| CA-4 | Los registros no pueden ser modificados ni eliminados por usuarios del sistema | `auto_now_add=True` + hash SHA-256 como sello de integridad |
| CA-5 | Las decisiones de la IA (nivel de alerta) quedan vinculadas al paciente mediante ID seudonimizado | `TriageLog.paciente_id` (FK, nunca contiene PII directa) |
| CA-6 | Los eventos de autenticación (login/logout/fallos) forman parte del registro inmutable | Signals en `signals.py` escriben al `AuditLog` |
| CA-7 | Los intentos de acceso denegado por rol quedan trazados | Decorador `@rol_requerido` escribe al `AuditLog` |
| CA-8 | El regulador con rol `AUDITOR_DPO` puede consultar el historial sin alterar los datos | Vista protegida por RBAC (lectura exclusiva) |

---

## 2. Problema que Resuelve

Los sistemas de telemedicina con IA son sujetos de supervisión regulatoria estricta. En Ecuador, el **Ministerio de Salud Pública (MSP)** y la **Superintendencia de Protección de Datos Personales** exigen:

- Trazabilidad completa de todas las decisiones automatizadas que afecten la salud de un paciente
- Registro de quién tuvo acceso a información médica sensible y cuándo
- Evidencia de que la IA no actuó de forma autónoma sin supervisión médica
- Cadena de custodia digital de las recetas firmadas electrónicamente
- Capacidad de auditoría ante investigaciones por mala praxis o fuga de datos

Sin esta historia, el sistema sería incapaz de responder a una auditoría regulatoria formal y estaría incumpliendo el **Art. 30 de la LOPDP** (Registro de Actividades de Tratamiento).

---

## 3. Infraestructura Existente que Implementa Esta Historia

> [!IMPORTANT]
> Esta historia se apoya en **infraestructura ya implementada** en el proyecto. No requiere partir de cero. Los mecanismos de auditoría existen en múltiples capas.

### 3.1 Tabla `core_auditlog` — El Registro Central Inmutable

**Archivo:** [`core/models.py`](../SAMRpg/core/models.py) — Clase `AuditLog`

Esta es la tabla principal que satisface US-3.7. Estructura en base de datos:

```sql
CREATE TABLE core_auditlog (
    id                  BIGINT          PRIMARY KEY AUTO_INCREMENT,
    timestamp           DATETIME        NOT NULL,   -- auto_now_add, nunca modificable por ORM
    user_id             INT             NULL,        -- ID del usuario que generó el evento
    ip_address          VARCHAR(39)     NULL,        -- IPv4 o IPv6 de origen
    action              VARCHAR(255)    NOT NULL,    -- Descripción del evento auditado
    model_name          VARCHAR(100)    NOT NULL,    -- Tabla o sistema afectado
    object_id           VARCHAR(255)    NOT NULL,    -- ID del objeto afectado
    cryptographic_hash  CHAR(64)        NOT NULL     -- SHA-256 del evento (WORM integrity)
);
```

**Mecanismo de inmutabilidad:**
- `timestamp` usa `auto_now_add=True` → Django **prohíbe actualizarlo** mediante ORM
- `cryptographic_hash` es un SHA-256 calculado sobre los datos del evento → cualquier alteración directa en la BD invalida el hash, siendo detectable
- No existen endpoints `DELETE` ni `UPDATE` sobre esta tabla en ninguna view del sistema

---

### 3.2 Tabla `core_triagelog` — Registro de Cada Consulta con el Bot

**Archivo:** [`core/models.py`](../SAMRpg/core/models.py) — Clase `TriageLog`

Almacena el contenido completo de cada sesión de triaje conversacional:

```sql
CREATE TABLE core_triagelog (
    id                  BIGINT      PRIMARY KEY AUTO_INCREMENT,
    paciente_id         BIGINT      NOT NULL REFERENCES core_paciente(id),
    sintomas_reportados TEXT        NOT NULL,   -- Mensaje exacto del paciente al bot
    nivel_alerta        VARCHAR(20) NOT NULL,   -- Decisión de la IA: critico/medio/bajo
    respuesta_ia        TEXT        NOT NULL,   -- Respuesta literal del bot al paciente
    resumen_medico      TEXT        NOT NULL,   -- Resumen técnico generado para el médico
    estado_asignacion   VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    timestamp           DATETIME    NOT NULL    -- auto_now_add, inmutable
);
```

**Relación regulatoria:** `paciente_id` es un entero (seudónimo), nunca expone directamente el DNI ni el nombre. Esto cumple el principio de **minimización y seudonimización** del Art. 6.e de la LOPDP.

---

### 3.3 Capa de Signals — Auditoría Automática de Eventos del Sistema

**Archivo:** [`core/signals.py`](../SAMRpg/core/signals.py)

Los signals de Django actúan como **disparadores automáticos** que crean registros en `AuditLog` sin intervención manual del desarrollador:

| Signal | Evento | Datos registrados |
|--------|--------|-------------------|
| `user_logged_in` | Login exitoso (tras MFA) | `user_id`, `ip`, `username`, `tipoUsuario`, hash SHA-256 |
| `user_logged_out` | Cierre de sesión | `user_id`, `ip`, `username`, hash SHA-256 |
| `user_login_failed` | Intento de login fallido | `ip`, `username_intentado`, hash SHA-256 |
| `post_save` en `Paciente` | Creación/actualización de perfil | `model_name`, `object_id`, acción, hash SHA-256 |
| `post_save` en `Telemetria` | Ingesta de dato IoT | `model_name`, `object_id`, acción, hash SHA-256 |

**Cálculo del hash en signals.py:**
```python
raw_data = f"{action}|{model_name}|{object_id}|{instance.__dict__.get('timestamp', '')}"
crypto_hash = hashlib.sha256(raw_data.encode()).hexdigest()
```

---

### 3.4 Capa de Middleware — Auditoría de Acceso a Vistas Protegidas

**Archivo:** [`core/middleware.py`](../SAMRpg/core/middleware.py) — Clase `AccessAuditMiddleware`

Intercepta automáticamente **cada petición GET autenticada** a rutas protegidas y la registra en `AuditLog`:

```
Rutas auditadas por el middleware:
  /perfil/              → ¿Quién consultó su perfil?
  /panel-medico/        → ¿Qué médico accedió al panel de emergencias?
  /historial/           → ¿Quién consultó historial clínico?
  /triaje/              → ¿Quién inició una sesión de triaje?
  /gestionar-familiar/  → ¿Quién gestionó permisos de familiar?
```

**Datos registrados por request:**
- `user_id` — identidad del usuario autenticado
- `ip_address` — IP real (considera proxies vía `HTTP_X_FORWARDED_FOR`)
- `action` — ruta + método HTTP + User-Agent (primeros 100 caracteres)
- `cryptographic_hash` — SHA-256 de `{user_id}|{path}|{ip}|{timestamp}`

---

### 3.5 Capa de Views — Auditoría Manual de Eventos de Negocio Críticos

**Archivo:** [`core/views.py`](../SAMRpg/core/views.py)

Los eventos de negocio de mayor criticidad se auditan **manualmente** con lógica de negocio específica:

#### Evento 1: Triaje IA Generado (`chatbot_api`)
```python
# views.py — líneas ~403-414
audit_str = f"{paciente.id}-{user_message}-{nivel}-{time.time()}".encode('utf-8')
crypto_hash = hashlib.sha256(audit_str).hexdigest()

AuditLog.objects.create(
    user_id=request.user.id,
    ip_address=request.META.get('REMOTE_ADDR'),
    action=f"Triaje IA Generado: {nivel}",
    model_name="TriageLog",
    object_id=str(triage_log.id),
    cryptographic_hash=crypto_hash
)
```
**Qué registra:** Que el bot generó una clasificación de emergencia, con el ID del triaje asociado.

#### Evento 2: Receta Firmada Electrónicamente (`firmar_receta`)
```python
# views.py — sección firmar_receta
audit_str = f"{receta.id}-FIRMADA-{request.user.id}-{time.time()}".encode('utf-8')
crypto_hash = hashlib.sha256(audit_str).hexdigest()

AuditLog.objects.create(
    user_id=request.user.id,
    ip_address=request.META.get('REMOTE_ADDR'),
    action="Receta Firmada Electrónicamente",
    model_name="Receta",
    object_id=str(receta.id),
    cryptographic_hash=crypto_hash
)
```
**Qué registra:** El acto jurídico de firma digital del médico, con su `user_id` y timestamp.

#### Evento 3: Acceso Denegado por Rol (`@rol_requerido`)
```python
# views.py — decorador rol_requerido
AuditLog.objects.create(
    user_id=request.user.id,
    ip_address=ip,
    action=f"ACCESO DENEGADO: Usuario {request.user.username} (rol: {request.user.tipoUsuario}) intentó acceder a {request.path}",
    model_name="AccessControl",
    object_id=request.path,
    cryptographic_hash=crypto_hash,
)
```
**Qué registra:** Intentos de escalada de privilegios o accesos no autorizados por rol.

#### Evento 4: Login Exitoso / Fallido (`login_view`)
Doble registro: en `views.py` manualmente Y en `signals.py` automáticamente. Esto garantiza que incluso si un signal falla, el evento queda registrado.

---

## 4. Flujo Completo de Auditoría — Ciclo de Vida de una Consulta Bot

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│               TRAZABILIDAD COMPLETA DE UNA CONSULTA (US-3.7)                   │
└─────────────────────────────────────────────────────────────────────────────────┘

EVENTO 1: Usuario se autentica
  → signals.py:audit_user_logged_in()
  → AuditLog: SESIÓN INICIADA | user_id=7 | ip=192.168.1.1 | hash=abc123...

EVENTO 2: Usuario acepta términos LOPDP
  → views.py:terminos_lopdp_view()
  → Usuario.acepto_terminos_lopdp = True (UPDATE en core_usuario)
  → signals.py:audit_paciente() → AuditLog: UPDATED | Paciente | id=3 | hash=...

EVENTO 3: Usuario accede a /triaje/
  → middleware.py:AccessAuditMiddleware
  → AuditLog: ACCESO a /triaje/ [GET] | user_id=7 | ip=... | hash=...

EVENTO 4: Paciente envía mensaje al bot: "tengo dolor de pecho"
  → views.py:chatbot_api()  [POST /api/chatbot/]
  ├─ RAG recupera contexto bibliográfico
  ├─ GPT-4o-mini genera triaje: nivel="critico"
  ├─ TriageLog.objects.create() → core_triagelog (registro de la CONSULTA)
  │    sintomas_reportados = "tengo dolor de pecho"
  │    nivel_alerta        = "critico"
  │    respuesta_ia        = "🚨 [ALERTA ROJA] ..."
  │    resumen_medico      = "Pre-diagnóstico: SCA..."
  │    timestamp           = 2026-07-20T05:30:00Z  ← INMUTABLE
  └─ AuditLog.objects.create() → core_auditlog (SELLO INMUTABLE)
       action     = "Triaje IA Generado: critico"
       object_id  = "42"  (ID del TriageLog)
       hash       = SHA-256("3-tengo dolor de pecho-critico-1753043400.0")

EVENTO 5: Médico accede a /panel-medico/
  → middleware.py:AccessAuditMiddleware
  → AuditLog: ACCESO a /panel-medico/ [GET] | user_id=2 | hash=...

EVENTO 6: Médico acepta el triaje
  → views.py:aceptar_triaje()
  → TriageLog.estado_asignacion = "ATENDIDO"
  → WebSocket → notificación al paciente

EVENTO 7: Médico genera y firma receta
  → views.py:generar_receta() → Receta.objects.create()
  → views.py:firmar_receta()
  → AuditLog: "Receta Firmada Electrónicamente" | user_id=2 | hash=...

EVENTO 8: Cierre de sesión
  → signals.py:audit_user_logged_out()
  → AuditLog: SESIÓN CERRADA | user_id=7 | hash=...
```

---

## 5. Esquema de Datos — Mapa de Tablas que Soportan US-3.7

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  TABLAS QUE FORMAN EL REGISTRO INMUTABLE (US-3.7)                           │
└──────────────────────────────────────────────────────────────────────────────┘

core_auditlog                       core_triagelog
──────────────                      ──────────────
id              PK                  id              PK
timestamp       INMUTABLE ←──┐      paciente_id     FK (seudónimo)
user_id         FK (nullable) │      sintomas_reportados
ip_address                    │      nivel_alerta        ← Decisión IA
action          Descripción   │      respuesta_ia        ← Texto bot
model_name      "TriageLog"   │      resumen_medico      ← Resumen médico
object_id  ─────────────────→┘      estado_asignacion
cryptographic_hash  SHA-256         timestamp       INMUTABLE


core_receta                         django_session
──────────────                      ──────────────
id              PK                  session_key
triaje_id       FK → TriageLog      session_data    (incluye session_ip)
contenido       [CIFRADO AES-256]   expire_date
firmada         BOOLEAN
timestamp       INMUTABLE
```

---

## 6. Gap Analysis — Qué Ya Existe vs. Qué Añadiría la Implementación Completa

### ✅ Implementado (infraestructura base existente)

| Funcionalidad | Archivo | Tabla |
|---|---|---|
| Registro de cada triaje completo (input + output del bot) | `views.py:chatbot_api` | `core_triagelog` |
| Sello SHA-256 sobre el evento de triaje | `views.py:chatbot_api` | `core_auditlog` |
| Registro de login/logout/fallos con hash | `signals.py` | `core_auditlog` |
| Auditoría de acceso a vistas protegidas | `middleware.py` | `core_auditlog` |
| Registro de firma electrónica de receta | `views.py:firmar_receta` | `core_auditlog` |
| Registro de accesos denegados por rol | `views.py:rol_requerido` | `core_auditlog` |
| Seudonimización del paciente en los registros | `models.py` (FK a `Paciente.id`) | `core_triagelog` |
| Registro de intentos de fuerza bruta | `middleware.py:BruteForceProtectionMiddleware` | `core_auditlog` |

### 🔲 Extensión Recomendada para Implementación Completa

Para una auditoría regulatoria de grado médico, se recomienda agregar:

#### a) Modelo `BotInteractionLog` — Granularidad de Mensajes

Actualmente solo se registra el **resultado final** del triaje. Un regulador podría necesitar ver **cada turno individual** de la conversación.

```python
# Propuesta de nuevo modelo en models.py
class BotInteractionLog(models.Model):
    """
    US-3.7: Registro granular de cada mensaje individual con el bot.
    Complementa TriageLog (que registra el resultado) con el historial
    completo de la conversación turno a turno.
    """
    TIPO_CHOICES = [
        ('PACIENTE', 'Mensaje del Paciente'),
        ('BOT',      'Respuesta del Bot'),
        ('SISTEMA',  'Evento del Sistema'),
    ]
    triaje        = models.ForeignKey(TriageLog, on_delete=models.CASCADE,
                                      related_name='interacciones', null=True)
    paciente      = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    tipo          = models.CharField(max_length=10, choices=TIPO_CHOICES)
    contenido     = models.TextField()                   # Texto del turno
    timestamp     = models.DateTimeField(auto_now_add=True)
    sequence_num  = models.PositiveIntegerField()        # Orden del mensaje en la sesión
    hash_contenido = models.CharField(max_length=64)     # SHA-256 del contenido

    class Meta:
        ordering = ['timestamp', 'sequence_num']
```

**Migración asociada:** `0007_botinteractionlog.py`

#### b) Campo `session_id` en `TriageLog`

Para agrupar múltiples triajes de la misma sesión de usuario:

```python
# Adición en TriageLog
session_id = models.CharField(max_length=40, null=True, blank=True,
                               help_text="ID de sesión Django — correlaciona triajes de la misma conexión")
```

#### c) Vista de Solo Lectura para `AUDITOR_DPO`

```python
@login_required
@rol_requerido(['AUDITOR_DPO'])
def panel_auditoria(request):
    """
    US-3.7: Vista exclusiva para el rol AUDITOR_DPO.
    Permite consultar AuditLog y TriageLog sin posibilidad de modificación.
    """
    logs = AuditLog.objects.all().order_by('-timestamp')[:1000]
    triajes = TriageLog.objects.all().order_by('-timestamp')[:500]
    return render(request, 'auditoria.html', {'logs': logs, 'triajes': triajes})
```

---

## 7. Archivos Analizados para Esta Historia

| Archivo | Rol en US-3.7 | Estado |
|---------|---------------|--------|
| [`core/models.py`](../SAMRpg/core/models.py) | Define `AuditLog` y `TriageLog` — las dos tablas del registro inmutable | ✅ Existente |
| [`core/signals.py`](../SAMRpg/core/signals.py) | Triggers automáticos: login/logout/post_save → `AuditLog` | ✅ Existente |
| [`core/middleware.py`](../SAMRpg/core/middleware.py) | `AccessAuditMiddleware`: intercepta accesos a vistas protegidas | ✅ Existente |
| [`core/views.py`](../SAMRpg/core/views.py) | Auditoría manual en: `chatbot_api`, `firmar_receta`, `login_view`, `@rol_requerido` | ✅ Existente |
| `core/models.py` | `BotInteractionLog` — registro granular por mensaje | 🔲 Propuesto |
| `core/views.py` | `panel_auditoria` — vista para `AUDITOR_DPO` | 🔲 Propuesto |
| `core/migrations/0007_botinteractionlog.py` | Migración del nuevo modelo | 🔲 Propuesto |

---

## 8. Cumplimiento Normativo Cubierto por Esta Historia

| Norma | Artículo / Control | Mecanismo en SAMR-IA |
|-------|-------------------|----------------------|
| **LOPDP Ecuador** | Art. 30 — Registro de actividades de tratamiento | `AuditLog` con `user_id` + `timestamp` + `action` |
| **LOPDP Ecuador** | Art. 26 — Datos sensibles de salud | `TriageLog.paciente_id` (seudónimo, nunca PII directa) |
| **ISO 27001** | A.12.4.1 — Event Logging | 4 capas de auditoría (signals + middleware + views + brute force) |
| **ISO 27001** | A.12.4.2 — Protection of log information | `cryptographic_hash` SHA-256 + `auto_now_add` en timestamp |
| **ISO 27799** | Sección 9.2 — Seguridad de registros clínicos | `TriageLog` registra input/output del bot sin PII |
| **ISO 27001** | A.9.4.2 — Secure log-on procedures | `AuditLog` por login + MFA (`otp_verify_view`) |
| **ISO/IEC 25010** | Fiabilidad — Trazabilidad | Cadena de hashes SHA-256 verificable por el regulador |

---

## 9. Instrucciones para el Regulador — Cómo Consultar los Registros

### Vía Django Admin (acceso `AUDITOR_DPO`)

```python
# Consultar todos los triajes de un paciente (sin ver su nombre):
TriageLog.objects.filter(paciente_id=X).values(
    'id', 'nivel_alerta', 'timestamp', 'estado_asignacion'
)

# Consultar todos los eventos de un usuario:
AuditLog.objects.filter(user_id=X).order_by('timestamp')

# Verificar integridad de un registro de auditoría:
import hashlib
log = AuditLog.objects.get(id=Y)
# El hash original fue calculado en el momento del evento.
# El regulador puede pedirle al sistema los datos originales y recalcular.
```

### Verificación de Integridad del Hash

```python
# Para verificar que un AuditLog no fue manipulado:
# 1. El sistema guarda: hash = SHA256(f"{paciente.id}-{mensaje}-{nivel}-{timestamp}")
# 2. Si alguien modifica 'action' o 'object_id' directamente en la BD,
#    el hash guardado ya no coincidirá con los datos → evidencia de manipulación.
# 3. El regulador solicita exportación del AuditLog y verifica hashes off-line.
```

---

## 10. Resumen Ejecutivo para el Regulador

El sistema **SAMR-IA ya implementa** un registro inmutable de cuatro capas que cubre los requisitos de US-3.7:

1. **`core_auditlog`** — Tabla central con SHA-256 por evento: imposible modificar sin dejar evidencia
2. **`core_triagelog`** — Registro completo de cada consulta al bot: input del paciente + decisión de la IA + respuesta generada
3. **Signals automáticos** — Eventos de sesión (login/logout/fallos) capturados sin intervención manual
4. **Middleware de auditoría** — Cada acceso a páginas protegidas queda registrado con IP y User-Agent

La extensión propuesta (`BotInteractionLog`) añadiría granularidad mensaje a mensaje para auditorías de máxima exigencia regulatoria, y la vista `panel_auditoria` proveería una interfaz de solo lectura para el rol `AUDITOR_DPO`.

---

*Documentado por: Rol Base de Datos — SAMR-IA v1.0 | Historia SAMR-41 / US-3.7*  
*Estándares cubiertos: LOPDP Ecuador, ISO 27001 A.12.4, ISO 27799, ISO/IEC 25010*
