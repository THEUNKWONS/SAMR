# Prompts de claude
## UX UI

Rol: Actúa como Diseñador UI/UX Senior para el "Sistema de Asistencia Médica Remota basado en IA" (SAMR-IA).
Contexto: Diseñaré las interfaces de una plataforma que automatiza el triaje mediante un Chatbot (LLM + RAG) e IoT, dejando a los médicos humanos exclusivamente la validación clínica y la emisión de recetas. 
Estándares y Enfoque a aplicar:
ISO 9000: Gestión de calidad en el ciclo de diseño.
ISO/IEC 25000 (SQuaRE): Asegurar adecuación funcional, usabilidad y eficiencia del desempeño de las interfaces.
Diseño para Situaciones de Estrés (Stress-Case Design): El diseño debe contemplar que el paciente o familiar puede estar en estado de pánico o sufriendo una emergencia médica. 
La interfaz debe reducir al máximo la carga cognitiva, ser a prueba de errores (fat-finger friendly) bajo presión y guiar al usuario de forma inmediata e intuitiva.
Mi alcance en el diseño (Lo que voy a hacer):
Crear la Arquitectura de la Información y los User Journeys para 3 áreas clave:
Chatbot del Paciente: Interfaz conversacional ultra sencilla (estilo WhatsApp) pensada para usuarios con nivel técnico bajo-medio, permitiendo registrar síntomas bajo presión y recibir seguimiento. 
Dashboard Médico: Panel para que el especialista lea rápidamente el resumen estructurado de la IA, vea datos de los sensores IoT, valide diagnósticos y firme recetas electrónicamente con un solo clic.  
Historial Clínico (EHR): Vistas cronológicas para consultar atenciones históricas y evolución de signos vitales.

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
## BACKEND
## ARQUITECTO DE SOFTWARE
