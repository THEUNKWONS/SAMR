# SAMR-30 · US-2.2 — Resumen RAG con Literatura Médica para el Especialista

> **Rama:** `SAMR-30-US-2.2-Como-especialista-quiero-recibir-un-resumen-generado-por-RAG-sustentado-en-libros-médicos-para-no-enfrentar-alucinaciones-de-IA`  
> **Épica:** SAMR-2 — Motor de Triaje IA con Explicabilidad (XAI)  
> **Rol:** Capa de Base de Datos, Backend & UI  
> **Fecha de actualización:** 2026-07-21  
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
| CA-1 | El resumen para el especialista debe incluir referencias de libros médicos verificables. | Se devuelven citas formateadas y los fragmentos exactos usados. |
| CA-2 | El motor RAG debe ser independiente del triaje inicial del paciente. | Se implementa `specialist_rag_engine.py` y una ruta dedicada. |
| CA-3 | El especialista debe poder solicitar este resumen explícitamente desde su panel. | Botón "Resumen Bibliográfico" en `panel_medico.html`. |
| CA-4 | Las consultas y resultados RAG quedan registrados para trazabilidad. | Se guarda en el nuevo modelo `ResumenEspecialistaRAG`. |
| CA-5 | Toda la operación es registrada para cumplir con ISO 27001. | Se genera un registro inmutable en `AuditLog`. |

---

## 2. Problema que Resuelve

Los **Modelos de Lenguaje (LLM)** tienen tendencia a generar información médica plausible pero incorrecta, conocido como **alucinación**. Para un especialista, un resumen de triaje sin sustento técnico puede llevar a:

- Dudas sobre la validez del pre-diagnóstico.
- Toma de decisiones con información fabricada por la IA.
- Pérdida de confianza en el sistema SAMR-IA.

La técnica **RAG (Retrieval-Augmented Generation)** resuelve esto:
1. **Antes** de consultar a la IA para generar el resumen final, recuperamos fragmentos reales de libros médicos.
2. Esos fragmentos se inyectan en el prompt como "contexto verificable".
3. El LLM es forzado a redactar su resumen técnico **citando exclusivamente** esas fuentes bibliográficas.

---

## 3. Archivos Creados y Modificados

### 3.1 Archivos Creados (NUEVOS)

| Archivo | Descripción |
|---|---|
| [`core/medical_bibliography.py`](../SAMRpg/core/medical_bibliography.py) | **Base de Conocimiento Bibliográfica:** Diccionario con 14 fragmentos de libros médicos reales (Harrison's, Tintinalli's, Braunwald's, Nelson, etc.). Cada entrada tiene `titulo_libro`, `autores`, `paginas`, `contenido` y `palabras_clave`. |
| [`core/specialist_rag_engine.py`](../SAMRpg/core/specialist_rag_engine.py) | **Motor RAG Especialista:** Algoritmo que recibe síntomas, tokeniza, calcula el score de relevancia contra la bibliografía y extrae el "Top 3" de fragmentos. Construye el contexto APA para OpenAI. |
| [`core/migrations/0007_samr_us22_resumen_especialista_rag.py`](../SAMRpg/core/migrations/0007_samr_us22_resumen_especialista_rag.py) | **Migración BD:** Crea la tabla para el modelo `ResumenEspecialistaRAG`. |

### 3.2 Archivos Modificados (EXISTENTES)

| Archivo | Acción | Descripción del cambio |
|---|---|---|
| [`core/models.py`](../SAMRpg/core/models.py) | **AGREGADO** | Se agregó el modelo `ResumenEspecialistaRAG` relacionado (OneToOne) con `TriageLog`. Guarda el `resumen_generado` y las `referencias_bibliograficas` en formato JSON. |
| [`core/urls.py`](../SAMRpg/core/urls.py) | **AGREGADO** | Nueva ruta `/api/triaje/<int:triaje_id>/resumen_especialista/` que expone la función al Frontend. |
| [`core/views.py`](../SAMRpg/core/views.py) | **AGREGADO** | Nueva vista `resumen_especialista_rag`. Protegida por RBAC (solo especialistas). Oculta PII (US-4.1). Llama al RAG bibliográfico y luego a `gpt-4o-mini`. Persiste en BD y genera `AuditLog`. |
| [`templates/panel_medico.html`](../SAMRpg/templates/panel_medico.html) | **MODIFICADO** | UI: Se agregó el botón **"📚 Resumen Bibliográfico (RAG)"** y un contenedor colapsable que renderiza el resumen técnico y *badges* dinámicos con las citas de los libros y sus páginas. |

---

## 4. Esquema de Base de Datos — Nuevo Modelo

### Tabla `core_resumenespecialistarag`

El nuevo modelo almacena cada resumen generado para garantizar trazabilidad.

```python
class ResumenEspecialistaRAG(models.Model):
    triaje = models.OneToOneField(TriageLog, on_delete=models.CASCADE, related_name='resumen_especialista')
    resumen_generado = models.TextField()
    referencias_bibliograficas = models.TextField() # JSON serializado con las fuentes
    ids_referencias_usadas = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
```

**Ejemplo de referencias guardadas (JSON):**
```json
[
  {
    "id": "BIB-001",
    "titulo_libro": "Braunwald's Heart Disease",
    "autores": "Libby P, Bonow RO...",
    "edicion": "12th Edition",
    "paginas": "1228-1265",
    "relevancia_score": 12.5
  }
]
```

---

## 5. Arquitectura RAG Implementada

```
┌──────────────────────────────────────────────────────────────────────┐
│             PIPELINE RAG ESPECIALISTA — SAMR-IA US-2.2               │
└──────────────────────────────────────────────────────────────────────┘

  [1] FRONTEND (panel_medico)   [2] RETRIEVAL (specialist_rag_engine)
  ─────────────────────────     ────────────────────────────────────
  Clic en "Resumen RAG"     →   Extrae síntomas + resumen inicial
                                Busca en medical_bibliography.py
                                Retorna top-K libros médicos

  [3] AUGMENTATION (views.py)   [4] GENERATION (OpenAI GPT-4o-mini)
  ─────────────────────────     ───────────────────────────────────
  System Prompt + PII oculto →  Genera resumen clínico TÉCNICO
  + Contexto bibliográfico      citando explícitamente (Autor, Año, pp.)

  [5] PERSISTENCE (models.py)   [6] FRONTEND (UI)
  ─────────────────────────     ───────────────────────────────────
  Guarda en ResumenEspecialistaRAG  Muestra resumen técnico +
  Genera AuditLog (WORM)        →   Badges con referencias bibliográficas
```

---

## 6. Relación con Otros Requisitos

| Historia relacionada | Conexión |
|---|---|
| **US-2.1** — Triaje IA básico | Este RAG es un **segundo nivel** de análisis, más profundo y exclusivo para el médico, sin alterar el flujo original del paciente. |
| **SAMR-9** — Gestión de Identidad | La vista requiere `@login_required` y `@rol_requerido(['MEDICO_ESPECIALISTA', 'MEDICO_ASISTENTE'])`. |
| **US-4.1** — Privacidad PII | Antes de enviar el contexto clínico a OpenAI y al RAG, se usa `ofuscar_pii(sintomas)`. |
| **ISO 27001 Audit Trail** | Cada vez que un médico pide el resumen bibliográfico, se crea un hash criptográfico en `AuditLog`. |
| **XAI (Explicabilidad IA)** | Es la materialización definitiva de XAI para el cuerpo médico: la IA ya no opina, sino que procesa, cita y resume libros médicos de la KB. |

---

## 7. Instrucciones de Despliegue

### Paso 1 — Aplicar la migración

Al actualizar desde el repositorio, el servidor requiere que se aplique la nueva migración:

```bash
cd SAMRpg
# Activar entorno virtual
.\venv\Scripts\Activate.ps1
# Aplicar la migración 0007_samr_us22_resumen_especialista_rag
python manage.py migrate
```

### Paso 2 — Ejecutar el servidor y probar

1. Iniciar servidor: `python manage.py runserver`
2. Entrar a `/login/` con credenciales de especialista (ej. `doctor@samria.com`) e ingresar el OTP.
3. Ir al Panel Médico, aceptar un triaje pendiente.
4. En el panel de acciones, presionar **"📚 Resumen Bibliográfico (RAG)"**.
5. Verificar que se despliega el resumen clínico con los "badges" celestes de las fuentes.

---

*Documentado por: Rol Base de Datos — SAMR-IA v1.0 | Historia SAMR-30 / US-2.2*
