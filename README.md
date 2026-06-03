# 🏥 SAMR - Sistema de Asistencia Médica Remota

![Status](https://img.shields.io/badge/Status-Prototipo%20Activo-orange)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![Architecture](https://img.shields.io/badge/Architecture-Microservices-success)

> **"La atención va hacia el paciente, no el paciente hacia la atención."**

El **Sistema de Asistencia Médica Remota (SAMR)** es una plataforma transaccional distribuida de misión crítica. Está diseñada para resolver la falta de acceso oportuno a atención médica domiciliaria, evitando la saturación de las salas de emergencia y mitigando el riesgo de complicaciones vitales a través del monitoreo continuo con biosensores IoT.

---

## 🚀 Prototipo Funcional (MVP)

Actualmente, el diseño de la interfaz de usuario (UX/UI) y la validación de los flujos de interacción descritos en el Documento de Visión se encuentran desplegados para acceso público. 

Puedes interactuar con el prototipo del sistema aquí:
🔗 **[Prototipo SAMR en Netlify](https://ai.studio/apps/eaa29832-9c77-4881-a00e-0473d00d1b65?fullscreenApplet=true)**

Este despliegue permite a los *Stakeholders* (Pacientes, Médicos, y Administración) validar la usabilidad de las pantallas de teleconsulta, el dashboard de alertas y el ecosistema de ofertas concurrentes.

---

## 🎯 Visión del Proyecto

A diferencia de los sistemas de salud tradicionales que dependen de citas estáticas, SAMR despliega un **ecosistema competitivo y concurrente**. Las alertas de anomalías vitales detectadas en los domicilios se publican como "ofertas abiertas", permitiendo que múltiples centros de asistencia médica de la red compitan en tiempo real para aceptar y atender la emergencia, garantizando la menor latencia de respuesta posible.

---

## 🏗️ Arquitectura y Stack Tecnológico (Backend)

El ecosistema está diseñado bajo patrones de alta concurrencia, segregación de bases de datos y normativas estrictas de salud pública.

### ⚙️ Backend & Orquestación
* **API Gateway (.NET 8.0):** Orquestación centralizada y enrutamiento seguro de peticiones implementando *Ocelot* como middleware principal para la gestión precisa de rutas.
* **Microservicios Core (Java):** Implementación de *Virtual Threads* para soportar la ingesta paralela masiva de biosensores IoT (EKG/EEG) sin bloquear los hilos de I/O del servidor.
* **Infraestructura (Docker):** Servicios totalmente contenerizados con gestión de volúmenes persistentes para garantizar aislamiento y escalabilidad horizontal (SLA 99.99%).

### 💾 Bases de Datos (Segregación de Responsabilidades)
* **Transaccional / ACID (MySQL):** Motor central para el registro jerárquico (Pacientes, Médicos, Centros) y la resolución de concurrencia mediante bloqueos (locks) para la asignación única de ofertas médicas.
* **Telemetría y Analítica (MariaDB):** Entorno de base de datos aislado y optimizado para el análisis de datos de R, la persistencia de series de tiempo de dispositivos IoT y logs de auditoría inmutables.

### 🔒 Cumplimiento Normativo (Compliance by Design)
* **ISO 27799 / ISO 27001:** Encriptación de datos sensibles en tránsito (TLS 1.3) y en reposo.
* **Interoperabilidad:** Adopción del estándar **HL7 FHIR** para la integración del historial clínico con entidades gubernamentales (MSP, IESS).
* **ISO/IEC 25010:** Atributos de Fiabilidad y Eficiencia de desempeño testeados bajo estrés.

---

## 📋 Características Principales (Core Features)

1. **Motor de Ofertas Concurrentes:** Publicación en tiempo real de emergencias médicas con algoritmos anticolisión.
2. **Telemetría IoT en Tiempo Real:** Detección automática de anomalías y evaluación de umbrales clínicos.
3. **Teleconsulta Integrada:** Soporte para diagnóstico remoto mediante infraestructura de video y chat clínico seguro.
4. **Facturación Electrónica Automática:** Integración con flujos ERP de los centros para ejecución de cobros tras la confirmación de la asistencia.
5. **Audit Trail Inmutable:** Registro persistente e inalterable de cada evento para auditorías de las Agencias Reguladoras.

---

## 👥 Stakeholders Principales

Este sistema modela los procesos de negocio de:
* **Pacientes y Familiares:** Usuarios finales y portadores de biosensores.
* **Cuerpo Médico y Centros de Asistencia:** Proveedores de salud y receptores de alertas.
* **Ministerio de Salud Pública (MSP) y Sup. de Protección de Datos:** Reguladores y auditores del sistema.

---

## 📚 Documentación Adjunta

* [Tablero Kanban / Jira](https://utpl-team-requisitos.atlassian.net/jira/software/projects/SAMR/boards/1/backlog?atlOrigin=eyJpIjoiM2VjYzA5OGQ2YmVkNDIzMDkxYmRlNzg2NTVhMzY1N2MiLCJwIjoiaiJ9)

---
*Desarrollado como Proyecto de Identificación y Especificación de Requisitos a Nivel de Empresa.*
