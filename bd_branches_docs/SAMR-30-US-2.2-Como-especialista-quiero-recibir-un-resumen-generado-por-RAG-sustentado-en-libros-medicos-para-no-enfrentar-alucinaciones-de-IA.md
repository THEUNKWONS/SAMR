# SAMR-30 · US-2.2 — Resumen RAG con Literatura Médica para el Especialista

> **Rama:** `SAMR-30-US-2.2-Como-especialista-quiero-recibir-un-resumen-generado-por-RAG-sustentado-en-libros-médicos-para-no-enfrentar-alucinaciones-de-IA`  
> **Épica:** SAMR-2 — Motor de Triaje IA con Explicabilidad (XAI)  
> **Rol:** Capa de Base de Datos & Persistencia  
> **Fecha de implementación:** 2026-07-20  
> **Estado:** ✅ Implementado

---

## 1. Historia de Usuario

```
Como médico especialista,
quiero recibir un resumen de triaje generado por RAG
sustentado en libros médicos reconocidos,
para no enfrentar alucinaciones de IA al tomar decisiones clínicas.
```

### Criterios de Aceptación

| # | Criterio | Mecanismo de Verificación |
|---|----------|--------------------------|
| CA-1 | El resumen médico debe citar al menos una fuente bibliográfica verificada cuando los síntomas sean reconocibles | Campo `fuentes_rag` en `TriageLog` ≠ `null` |
| CA-2 | El LLM no debe generar diagnósticos fuera del contexto bibliográfico provisto | Instrucción explícita en `system_instruction` del prompt |
| CA-3 | El especialista puede ver en el panel qué libros médicos respaldaron el resumen | `fuentes_rag` accesible desde el `TriageLog` |
| CA-4 | Si no existe contexto relevante en la KB, el sistema sigue funcionando con degradación elegante | `rag_result["encontrado"] == False` → `fuentes_rag = null` |
| CA-5 | Las citas quedan registradas de forma inmutable junto al triaje | `fuentes_rag` almacenado en la misma fila que el triaje |

---

## 2. Problema que Resuelve

Los **Modelos de Lenguaje Grande (LLM)** como GPT-4o-mini tienen tendencia a generar información médica plausible pero incorrecta, fenómeno conocido como **alucinación**. En un sistema de triaje de emergencias médicas, una alucinación puede llevar a:

- Clasificación incorrecta del nivel de alerta (ej: triaje verde en un infarto)
- Recomendaciones farmacológicas con dosis erróneas
- Pre-diagnósticos que contradigan la evidencia clínica publicada
- Pérdida de confianza del especialista en el sistema

La técnica **RAG (Retrieval-Augmented Generation)** soluciona esto:
1. **Antes** de llamar al LLM, se recuperan fragmentos de literatura médica oficial
2. Esos fragmentos se inyectan en el prompt como contexto verificado
3. El LLM queda **instruido a razonar solo dentro de ese contexto**
4. El especialista recibe el resumen **con las citas** que lo respaldan

---

## 3. Archivos Creados y Modificados

### 3.1 Archivos Creados (NUEVOS)

#### [`core/rag_medical_kb.py`](../SAMRpg/core/rag_medical_kb.py) — Motor RAG Completo

Es el módulo central de esta historia. Contiene tres componentes:

| Componente | Elemento de código | Descripción |
|---|---|---|
| Knowledge Base | `MEDICAL_KNOWLEDGE_BASE` (dict) | 10 categorías de síntomas curadas con fragmentos de libros médicos y sus referencias APA |
| Retriever | `retrieve_medical_context(user_message, max_results=3)` | Busca los fragmentos más relevantes por coincidencia de palabras clave con puntaje de relevancia |
| Context Builder | `build_rag_context_block(rag_result)` | Ensambla el bloque de texto listo para inyectar en el prompt del LLM |

**Fuentes médicas indexadas en la Knowledge Base:**

| Libro / Guía | Categorías cubiertas |
|---|---|
| *Harrison's Principles of Internal Medicine, 21ª Ed.* (McGraw-Hill, 2022) | Disnea, ACV, Fiebre/Sepsis, Anafilaxis, Ansiedad |
| *Braunwald's Heart Disease, 12ª Ed.* (Elsevier, 2022) | Dolor de pecho/Infarto, Fibrilación Auricular |
| *Tintinalli's Emergency Medicine, 9ª Ed.* (McGraw-Hill, 2020) | Síncope, Dolor Abdominal, Trauma |
| *GOLD Guidelines 2024* | Asma, EPOC |
| *Guías AHA/ACC 2023* | Síndromes coronarios |
| *Guías MSP Ecuador 2023* | Contexto normativo local |

#### [`core/migrations/0006_triagelog_fuentes_rag.py`](../SAMRpg/core/migrations/0006_triagelog_fuentes_rag.py) — Migración de BD

Agrega el campo `fuentes_rag` (JSONField, nullable) a la tabla `core_triagelog`.

---

### 3.2 Archivos Modificados (EXISTENTES)

#### [`core/models.py`](../SAMRpg/core/models.py)

**Cambio:** Se añadió el campo `fuentes_rag` al modelo `TriageLog`.

```python
# Antes (sin US-2.2)
class TriageLog(models.Model):
    paciente            = models.ForeignKey(...)
    sintomas_reportados = models.TextField()
    nivel_alerta        = models.CharField(...)
    respuesta_ia        = models.TextField()
    resumen_medico      = models.TextField()
    estado_asignacion   = models.CharField(...)
    timestamp           = models.DateTimeField(auto_now_add=True)
```

```python
# Después (con US-2.2 — campo nuevo resaltado)
class TriageLog(models.Model):
    paciente            = models.ForeignKey(...)
    sintomas_reportados = models.TextField()
    nivel_alerta        = models.CharField(...)
    respuesta_ia        = models.TextField()
    resumen_medico      = models.TextField()
    estado_asignacion   = models.CharField(...)
    timestamp           = models.DateTimeField(auto_now_add=True)
    # ► NUEVO US-2.2
    fuentes_rag         = models.JSONField(null=True, blank=True,
                              help_text="[US-2.2] Citas bibliográficas del RAG")
```

**Impacto en la tabla `core_triagelog`:**

| Operación SQL generada | Descripción |
|---|---|
| `ALTER TABLE core_triagelog ADD COLUMN fuentes_rag JSON NULL` | Agrega el campo sin romper registros existentes |

---

#### [`core/views.py`](../SAMRpg/core/views.py)

**Cambio:** Se integró el motor RAG dentro de la función `chatbot_api`.

**Líneas afectadas:** importación (línea 21-23), lógica RAG (antes del `client = OpenAI()`), creación del `TriageLog`.

**Flujo completo modificado:**

```
Mensaje del paciente (user_message)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO RAG [NUEVO - US-2.2]                                      │
│                                                                 │
│  rag_result = retrieve_medical_context(user_message)            │
│      └─ Analiza keywords del mensaje                            │
│      └─ Busca en MEDICAL_KNOWLEDGE_BASE                         │
│      └─ Retorna top-3 fragmentos + citas_apa + encontrado:bool  │
│                                                                 │
│  rag_context = build_rag_context_block(rag_result)              │
│      └─ Formatea los fragmentos como bloque de texto            │
│      └─ Cadena vacía si encontrado=False                        │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM_INSTRUCTION AUMENTADO [MODIFICADO - US-2.2]             │
│                                                                 │
│  "Eres SAMR-IA..." + contexto_clínico + rag_context             │
│                          │                     │                │
│                          │                     └─ fragmentos de │
│                          │                        libros médicos│
│                          └─ Edad, sexo, historial, telemetría   │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
  GPT-4o-mini genera JSON:
  {
    "nivel_alerta":     "critico|medio|bajo",
    "respuesta_paciente": "...",
    "resumen_medico":   "... 📚 Referencias: [fuentes RAG]"
  }
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PERSISTENCIA [MODIFICADO - US-2.2]                             │
│                                                                 │
│  TriageLog.objects.create(                                      │
│      ...                                                        │
│      fuentes_rag = rag_result["citas_apa"]  # ← NUEVO CAMPO     │
│                   if rag_result["encontrado"] else None         │
│  )                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Esquema de Base de Datos — Cambio en `core_triagelog`

### Antes de la migración `0006`

```sql
CREATE TABLE core_triagelog (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    paciente_id         BIGINT NOT NULL REFERENCES core_paciente(id),
    sintomas_reportados TEXT NOT NULL,
    nivel_alerta        VARCHAR(20) NOT NULL,
    respuesta_ia        TEXT NOT NULL,
    resumen_medico      TEXT NOT NULL,
    estado_asignacion   VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    timestamp           DATETIME NOT NULL
);
```

### Después de la migración `0006`

```sql
ALTER TABLE core_triagelog
    ADD COLUMN fuentes_rag JSON NULL
        COMMENT '[US-2.2] Citas bibliográficas del motor RAG que sustentaron el resumen médico.';
```

### Ejemplo de registro en la BD post-US-2.2

```json
{
  "id": 42,
  "paciente_id": 7,
  "sintomas_reportados": "tengo dolor de pecho muy fuerte, me irradia al brazo izquierdo",
  "nivel_alerta": "critico",
  "respuesta_ia": "🚨 [ALERTA ROJA] He detectado síntomas que requieren atención inmediata...",
  "resumen_medico": "Paciente masculino 58 años con dolor torácico retroesternal irradiado al brazo izquierdo... Escala HEART score preliminar: alto riesgo. 📚 Referencias: Braunwald's Heart Disease, 12ª Ed. (Elsevier, 2022) — Cap. 56",
  "estado_asignacion": "PENDIENTE",
  "timestamp": "2026-07-20T05:30:00Z",
  "fuentes_rag": [
    "Braunwald's Heart Disease, 12ª Ed. (Elsevier, 2022) — Cap. 56: Chest Pain",
    "Harrison's Principles of Internal Medicine, 21ª Ed. (McGraw-Hill, 2022) — Cap. 33: Dyspnea"
  ]
}
```

---

## 5. Arquitectura RAG Implementada

### Patrón: Keyword-Based Retrieval (prototipo académico)

```
┌──────────────────────────────────────────────────────────────────────┐
│                   PIPELINE RAG — SAMR-IA US-2.2                     │
└──────────────────────────────────────────────────────────────────────┘

  [1] QUERY                [2] RETRIEVAL              [3] AUGMENTATION
  ───────────              ─────────────              ────────────────
  user_message        →   MEDICAL_KNOWLEDGE_BASE  →   system_instruction
  "dolor de pecho"        keyword scoring              + fragmentos RAG
                          top-K ranking                + instrucción XAI
                          fragmentos + citas

  [4] GENERATION           [5] PERSISTENCE
  ──────────────           ───────────────
  GPT-4o-mini          →   TriageLog.fuentes_rag
  resumen con citas         (JSONField en BD)
```

### Escalabilidad hacia Producción

En el prototipo, el retriever usa **coincidencia de palabras clave** (simple y sin dependencias externas). Para producción, la interfaz pública `retrieve_medical_context()` puede ser reemplazada por:

| Componente | Prototipo (actual) | Producción (roadmap) |
|---|---|---|
| Knowledge Base | Diccionario Python en memoria | PDFs de libros médicos indexados |
| Retriever | Keyword matching | Embeddings + búsqueda coseno |
| Vector Store | N/A | `pgvector` (PostgreSQL) o Pinecone |
| Embedding Model | N/A | `text-embedding-3-small` (OpenAI) |
| Interfaz pública | `retrieve_medical_context()` | **Misma firma** (sin cambios en views.py) |

---

## 6. Relación con Otros Requisitos

| Historia relacionada | Conexión |
|---|---|
| **US-2.1** — Triaje IA básico | Esta historia extiende el endpoint `chatbot_api` existente sin romper su funcionalidad |
| **SAMR-9** — Gestión de Identidad | `fuentes_rag` queda protegido por el mismo RBAC de `TriageLog` |
| **ISO 27001 Audit Trail** | La creación de `TriageLog` con `fuentes_rag` ya es auditada por el `AuditLog` existente |
| **LOPDP Ecuador** | `fuentes_rag` no contiene PII — son solo citas bibliográficas, sin datos del paciente |
| **XAI (Explicabilidad IA)** | `fuentes_rag` es la implementación directa del principio de explicabilidad requerido |

---

## 7. Instrucciones de Despliegue

### Paso 1 — Aplicar la migración

```bash
cd SAMRpg
python manage.py migrate core 0006_triagelog_fuentes_rag
```

### Paso 2 — Verificar la migración

```bash
python manage.py showmigrations core
# Esperado: [X] 0006_triagelog_fuentes_rag
```

### Paso 3 — Verificar el nuevo módulo RAG

```bash
python manage.py shell
>>> from core.rag_medical_kb import retrieve_medical_context
>>> r = retrieve_medical_context("tengo dolor de pecho y me irradia al brazo")
>>> r["encontrado"]
True
>>> r["citas_apa"]
["Braunwald's Heart Disease, 12ª Ed. (Elsevier, 2022) — Cap. 56: Chest Pain"]
```

### Paso 4 — Ejecutar tests

```bash
python manage.py test core
```

> [!NOTE]
> No se requieren cambios en variables de entorno (`.env`). El módulo `rag_medical_kb.py` opera en memoria, sin conexión a servicios externos. La clave `OPENAI_API_KEY` ya configurada es suficiente.

---

## 8. Resumen de Archivos Tocados

| Archivo | Acción | Descripción del cambio |
|---------|--------|------------------------|
| `core/rag_medical_kb.py` | **CREADO** | Motor RAG completo: Knowledge Base, Retriever, Context Builder |
| `core/models.py` | **MODIFICADO** | Campo `fuentes_rag` (JSONField) agregado a `TriageLog` |
| `core/views.py` | **MODIFICADO** | `chatbot_api`: import RAG, paso de recuperación, inyección en prompt, persistencia en `TriageLog` |
| `core/migrations/0006_triagelog_fuentes_rag.py` | **CREADO** | Migración Django que ejecuta el `ALTER TABLE` |

---

*Documentado por: Rol Base de Datos — SAMR-IA v1.0 | Historia SAMR-30 / US-2.2*
