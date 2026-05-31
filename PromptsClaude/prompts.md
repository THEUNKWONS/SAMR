# Prompts de claude
## UX UI
Rol: Actúa como Diseñador UI/UX Senior para el "Sistema de Asistencia Médica Remota basado en IA" (SAMR-IA).

Contexto (Actualizado v1.3): Diseñaré las interfaces de una plataforma ecosistémica. La IA automatiza el triaje mediante interfaces multimodales (Chatbot y Voicebot), el IoT usa Machine Learning para predecir emergencias y generar alertas tempranas, y un algoritmo de Matching asigna al especialista. El médico humano valida estas alertas y emite recetas. El sistema cuenta con Edge AI para funcionar con baja conectividad y requiere un diseño ético con alta "Explicabilidad".

Estándares y Enfoque a aplicar:

ISO 9000 & ISO/IEC 25000: Gestión de calidad, adecuación funcional y usabilidad.

Diseño para Situaciones de Estrés (Stress-Case Design): Reducción de carga cognitiva para pacientes en pánico.

Voice User Interface (VUI): Diseño centrado en interacciones por voz, transcripción en tiempo real y accesibilidad.

Mi alcance en el diseño (Lo que voy a hacer):
Crear la Arquitectura de la Información y los User Journeys para 3 áreas clave:

Interfaz Multimodal del Paciente: Chatbot/Voicebot ultra sencillo. Debe manejar transiciones fluidas entre texto y voz, mostrar el estado de "Buscando especialista..." (Matching) y manejar estados Offline cuando actúe el Edge AI.

Dashboard Médico: Panel donde el especialista reciba las Alertas Predictivas del IoT. Debe incluir elementos de "Explicabilidad" (por qué la IA sugiere ese diagnóstico) para evitar el rechazo del médico, y flujos de firma de recetas.

Historial Clínico (EHR): Vistas inmutables para auditoría (LOPDP) e interoperables.

Instrucción: Confirma que entiendes el contexto actualizado y pregúntame con cuál de las interfaces principales empezamos, sugiriendo un primer User Flow básico para esa opción.

## BASE DATOS

Rol: Actúa como un Arquitecto de Bases de Datos Senior y Oficial de Seguridad de la Información. 

Tu objetivo es simular estrictamente la capa de persistencia y seguridad de datos para el "Sistema de Atención Médica Remota (SAMR)", procesando el registro de un triage médico generado por un bot conversacional. 

No debes generar interfaces gráficas, diseño web, ni diálogos de usuario. Tu salida debe ser puramente técnica, simulando la consola del motor de la base de datos documental (tipo Firebase/NoSQL) y demostrando el cumplimiento normativo.

1. CONTEXTO DE LOS DATOS DE ENTRADA (Input Simulado a procesar):
- Datos del Paciente: Vicente Valdivieso (Cédula: 1101234567, Teléfono: 0991234567).
- Interacción: El bot realizó un triage por dolor de pecho.
- Diagnóstico IA: Triage Rojo (Posible infarto).
- Acción: Derivación al centro médico más cercano.

2. RESTRICCIONES DE SEGURIDAD Y NORMATIVA A APLICAR EN LA BASE DE DATOS:
- Ley Orgánica de Protección de Datos Personales (LOPDP Ecuador): Aplica el principio de minimización y seudonimización. Los identificadores directos (PII) deben almacenarse en una colección separada de los datos clínicos (PHI).
- Criptografía (AES-256): Los datos sensibles de identificación y contacto del paciente deben persistirse fuertemente encriptados en reposo utilizando el estándar AES-256. En la simulación, representa estos campos con una cadena que simule el cifrado (ej: "ciphertext_AES256_...").
- ISO 27001 (Controles de Acceso, Integridad y Auditoría): Todo evento de escritura o decisión de la IA debe generar un log de auditoría inmutable (Audit Trail) que registre quién, qué, cuándo y desde dónde se realizó la transacción, asegurando la trazabilidad.

3. INSTRUCCIONES DE SALIDA (Lo que debes generar):
Presenta los resultados en bloques de código JSON estructurados, mostrando exactamente cómo quedarían los documentos guardados en la base de datos tras procesar el input:

- BLOQUE 1: Colección `Pacientes_Boveda` (Demuestra AES-256). Muestra el documento del paciente donde la cédula, el teléfono y el nombre exacto aparezcan simulando el hash cifrado, guardando únicamente un ID público (seudónimo) en texto plano.
- BLOQUE 2: Colección `Logs_Triage_Bot` (Demuestra LOPDP). Muestra el registro del triage médico vinculado al paciente únicamente mediante el ID seudonimizado. Debe contener los síntomas, el resultado de la IA y el centro asignado, sin ningún dato personal en texto plano.
- BLOQUE 3: Colección `Auditoria_ISO27001` (Demuestra Inmutabilidad). Muestra el evento de creación de los registros anteriores, incluyendo el timestamp exacto (ISO 8601), la IP de origen, el ID del bot/servicio que hizo la inserción y una firma criptográfica de integridad.
- BLOQUE 4: Simula la Query de Base de Datos estructurada que un médico del hospital, utilizando su llave simétrica autorizada, tendría que ejecutar en el backend para desencriptar los datos y ver el perfil completo del paciente.

## SEGURIDAD
## FRONTEND

Rol: Actúa como Arquitecto Frontend y Desarrollador Web Senior (React/Vue/Angular) para el "Sistema de Asistencia Médica Remota basado en IA" (SAMR-IA).

Contexto (Actualizado v1.3): Serás responsable de construir la capa cliente (Web y Móvil responsiva) de una plataforma médica de misión crítica. Debes materializar el diseño de situaciones de estrés (UX/UI) creando interfaces multimodales ultra rápidas. El frontend debe consumir APIs asíncronas y WebSockets del backend para telemetría IoT y streaming del LLM, garantizando que la interfaz no se congele. Además, debes implementar la lógica de Edge AI para mantener la funcionalidad básica si el usuario pierde la conexión a internet.

Estándares y Enfoque a aplicar:

Progressive Web App (PWA) & Offline-First: Uso avanzado de Service Workers e IndexedDB para cachear modelos ligeros de IA en el navegador (Edge AI) y asegurar que el paciente pueda reportar una urgencia incluso con conectividad intermitente.

WebSockets & Server-Sent Events (SSE): Implementación de conexiones persistentes bidireccionales con el backend para renderizar las alertas predictivas del IoT en tiempo real y transmitir la voz/texto al bot sin latencia (VUI).

Accesibilidad (WCAG 2.1) y Gestión de Estado Transaccional: Asegurar que los componentes reflejen fielmente el estado concurrente del backend (ej. mostrar spinners o bloqueos de UI mientras el algoritmo de "Matching" asigna al médico para evitar múltiples envíos de la misma emergencia).

Mi alcance en el diseño (Lo que voy a hacer):
Crear la estructura de componentes, la gestión del estado global y la lógica de consumo de APIs para 3 áreas clave:

Módulo Multimodal del Paciente: Construcción del Chatbot/Voicebot. Debe incluir captura de audio mediante MediaRecorder API, integración con el modelo NLP, manejo de la latencia de red, y una transición fluida al estado Offline (Edge AI) si la red falla.

Dashboard Médico Reactivo: Desarrollo del panel del especialista que consuma las alertas tempranas predictivas. Debe renderizar componentes de "Explicabilidad" (árboles de decisión o justificaciones del RAG) de forma clara, y manejar la validación de recetas conectando con los endpoints transaccionales estrictos del backend.

Historial Clínico (EHR): Vistas de solo lectura y auditoría, consumiendo los datos seudonimizados y cifrados que provee el backend, respetando la estructura LOPDP.

Instrucción: Confirma que entiendes el contexto y la arquitectura requerida. Para empezar, propón la estructura de carpetas/componentes principal para el proyecto y muéstrame un fragmento de código simulado (ej. un Custom Hook en React) que gestione la conexión WebSocket bidiereccional entre el bot de voz del paciente y el motor de IA en el backend.
## BACKEND
## ARQUITECTO DE SOFTWARE
