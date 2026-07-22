"""
SAMR-13: Base de Conocimiento de Protocolos Medicos para Triaje RAG
Contiene guias clinicas estructuradas que el motor RAG utiliza para
enriquecer el contexto del triaje automatizado con IA.
Basado en protocolos MTS (Manchester Triage System) y ESI (Emergency Severity Index).
"""

# Cada protocolo tiene: id, categoria, titulo, contenido clinico, nivel_alerta sugerido y palabras clave
PROTOCOLOS_MEDICOS = [
    {
        "id": "PROT-001",
        "categoria": "Cardiovascular",
        "titulo": "Protocolo de Dolor Toracico Agudo",
        "contenido": (
            "Ante dolor toracico agudo, considerar sindrome coronario agudo (SCA). "
            "Signos de alarma: dolor opresivo retroesternal irradiado a brazo izquierdo o mandibula, "
            "diaforesis, disnea, nauseas. En pacientes con factores de riesgo (hipertension, diabetes, "
            "tabaquismo, antecedentes familiares), elevar nivel de alerta a CRITICO. "
            "Accion inmediata: ECG en menos de 10 minutos, troponinas sericas, oximetria de pulso. "
            "Derivacion urgente a cardiologia si ST elevado."
        ),
        "nivel_sugerido": "critico",
        "palabras_clave": ["dolor pecho", "dolor toracico", "opresion pecho", "infarto", "corazon",
                           "brazo izquierdo", "mandibula", "diaforesis", "taquicardia"]
    },
    {
        "id": "PROT-002",
        "categoria": "Respiratorio",
        "titulo": "Protocolo de Dificultad Respiratoria",
        "contenido": (
            "La disnea aguda requiere evaluacion inmediata. Clasificar segun escala de gravedad: "
            "saturacion O2 < 90% = CRITICO, 90-94% = MEDIO, > 94% = vigilancia. "
            "Causas comunes: asma exacerbada, EPOC, neumonia, embolia pulmonar, insuficiencia cardiaca. "
            "Signos de alarma: uso de musculatura accesoria, cianosis, alteracion del nivel de consciencia, "
            "frecuencia respiratoria > 30 rpm. En pacientes con antecedentes de asma, verificar adherencia "
            "al tratamiento y uso reciente de broncodilatadores."
        ),
        "nivel_sugerido": "critico",
        "palabras_clave": ["no puedo respirar", "falta de aire", "ahogo", "disnea", "asma",
                           "respirar", "oxigeno", "tos severa", "cianosis"]
    },
    {
        "id": "PROT-003",
        "categoria": "Neurologico",
        "titulo": "Protocolo de Evaluacion Neurologica de Emergencia",
        "contenido": (
            "Ante sospecha de evento cerebrovascular (ECV), aplicar escala FAST: Face (asimetria facial), "
            "Arms (debilidad de brazos), Speech (alteracion del habla), Time (tiempo de inicio). "
            "Ventana terapeutica para trombolisis: 4.5 horas desde el inicio de los sintomas. "
            "Signos de alarma: cefalea subita intensa ('la peor de mi vida'), perdida de consciencia, "
            "convulsiones, debilidad unilateral, confusion aguda, vision borrosa subita. "
            "Nivel CRITICO si hay alteracion de consciencia o deficit neurologico focal."
        ),
        "nivel_sugerido": "critico",
        "palabras_clave": ["desmayo", "convulsion", "perdida consciencia", "dolor cabeza intenso",
                           "no siento brazo", "no puedo hablar", "vision borrosa", "mareo severo",
                           "cerebro", "derrame"]
    },
    {
        "id": "PROT-004",
        "categoria": "Alergias",
        "titulo": "Protocolo de Reaccion Alergica y Anafilaxia",
        "contenido": (
            "La anafilaxia es una emergencia medica que requiere atencion inmediata. "
            "Criterios diagnosticos: compromiso de dos o mas sistemas (cutaneo, respiratorio, "
            "cardiovascular, gastrointestinal) tras exposicion a alergeno conocido o sospechado. "
            "Signos de alarma: edema de garganta/lengua, sibilancias, hipotension, urticaria generalizada, "
            "dificultad para tragar. Tratamiento de primera linea: epinefrina intramuscular 0.3-0.5 mg. "
            "CRITICO si hay compromiso de via aerea o hipotension. MEDIO si solo presenta urticaria localizada."
        ),
        "nivel_sugerido": "critico",
        "palabras_clave": ["alergia", "alergico", "hinchazon", "urticaria", "ronchas",
                           "garganta cerrada", "no puedo tragar", "picadura", "anafilaxia"]
    },
    {
        "id": "PROT-005",
        "categoria": "Gastrointestinal",
        "titulo": "Protocolo de Dolor Abdominal Agudo",
        "contenido": (
            "El dolor abdominal agudo tiene un amplio diagnostico diferencial. "
            "Localizacion y caracteristicas orientan el diagnostico: "
            "Fosa iliaca derecha + fiebre + rebote = sospecha de apendicitis (MEDIO-CRITICO). "
            "Epigastrio + irradiacion a espalda = pancreatitis (MEDIO). "
            "Hipocondrio derecho + signo de Murphy = colecistitis (MEDIO). "
            "Abdomen rigido 'en tabla' = peritonitis (CRITICO). "
            "Signos de alarma: fiebre alta, vomitos con sangre, melena, defensa abdominal, "
            "signos de shock (taquicardia, hipotension)."
        ),
        "nivel_sugerido": "medio",
        "palabras_clave": ["dolor estomago", "dolor abdominal", "vomito", "nauseas", "diarrea",
                           "sangre en heces", "abdomen", "apendice", "fiebre alta"]
    },
    {
        "id": "PROT-006",
        "categoria": "Traumatologia",
        "titulo": "Protocolo de Evaluacion de Trauma",
        "contenido": (
            "Evaluacion primaria ABCDE: Airway, Breathing, Circulation, Disability, Exposure. "
            "Trauma craneoencefalico: escala de Glasgow < 13 = CRITICO, 13-15 con mecanismo de alta "
            "energia = MEDIO. Signos de alarma: perdida de consciencia > 5 minutos, amnesia del evento, "
            "vomitos repetidos post-trauma, otorragia/rinorragia, deformidad evidente de extremidades. "
            "Fracturas abiertas y hemorragias no controlables son CRITICO. "
            "Esguinces y contusiones menores sin signos de alarma son BAJO."
        ),
        "nivel_sugerido": "medio",
        "palabras_clave": ["caida", "golpe", "fractura", "hueso roto", "sangrado", "herida",
                           "accidente", "trauma", "corte profundo", "golpe cabeza"]
    },
    {
        "id": "PROT-007",
        "categoria": "Infeccioso",
        "titulo": "Protocolo de Fiebre y Proceso Infeccioso",
        "contenido": (
            "Fiebre > 38.5C en adultos requiere evaluacion del foco infeccioso. "
            "CRITICO si: fiebre + rigidez de nuca (meningitis), fiebre + hipotension + taquicardia (sepsis), "
            "fiebre en paciente inmunodeprimido, fiebre + petequias (meningococcemia). "
            "MEDIO si: fiebre + sintomas urinarios, fiebre + tos productiva (neumonia), "
            "fiebre + odinofagia (faringitis/amigdalitis). "
            "BAJO si: fiebre leve + sintomas catarrales sin signos de alarma. "
            "En todos los casos, evaluar estado de hidratacion y nivel de consciencia."
        ),
        "nivel_sugerido": "medio",
        "palabras_clave": ["fiebre", "temperatura alta", "infeccion", "escalofrios", "sudoracion",
                           "tos", "gripe", "resfriado", "dolor garganta"]
    },
    {
        "id": "PROT-008",
        "categoria": "Salud Mental",
        "titulo": "Protocolo de Crisis de Salud Mental",
        "contenido": (
            "Evaluacion de riesgo inmediato: ideacion suicida activa con plan = CRITICO. "
            "Agitacion psicomotriz severa con riesgo de auto/heteroagresion = CRITICO. "
            "Crisis de ansiedad/panico sin ideacion suicida = MEDIO. "
            "Insomnio, tristeza persistente, ansiedad leve = BAJO con derivacion a salud mental. "
            "En todos los casos: escucha activa, entorno seguro, no dejar solo al paciente en crisis. "
            "Preguntar directamente sobre pensamientos de hacerse dano de forma empatetica y sin juicio."
        ),
        "nivel_sugerido": "medio",
        "palabras_clave": ["ansiedad", "panico", "depresion", "no quiero vivir", "suicidio",
                           "crisis", "angustia", "insomnio", "estres", "desesperacion"]
    },
    {
        "id": "PROT-009",
        "categoria": "Pediatrico",
        "titulo": "Protocolo de Triaje Pediatrico",
        "contenido": (
            "En pacientes pediatricos, los signos vitales normales varian segun la edad. "
            "Triangulo de evaluacion pediatrica (TEP): apariencia, trabajo respiratorio, circulacion cutanea. "
            "CRITICO si: letargia, quejido respiratorio, cianosis, fontanela abombada en lactantes, "
            "fiebre > 38C en menores de 3 meses, convulsion febril prolongada (> 15 min). "
            "MEDIO si: fiebre > 39C en mayores de 3 meses, vomitos persistentes, deshidratacion moderada. "
            "BAJO si: cuadro catarral, fiebre baja controlada, erupciones cutaneas no petequiales."
        ),
        "nivel_sugerido": "medio",
        "palabras_clave": ["hijo", "bebe", "nino", "pediatrico", "menor", "lactante",
                           "fiebre nino", "llanto", "no come"]
    },
    {
        "id": "PROT-010",
        "categoria": "General",
        "titulo": "Protocolo de Consulta General y Sintomas Leves",
        "contenido": (
            "Sintomas que no presentan signos de alarma y son de baja complejidad. "
            "Incluye: cefalea leve sin signos neurologicos, dolor muscular post-ejercicio, "
            "resfriado comun, dolor de garganta leve, molestias digestivas menores. "
            "Recomendacion: hidratacion, reposo, analgesicos de venta libre si aplica. "
            "Derivar a consulta externa programada si los sintomas persisten mas de 72 horas. "
            "Nivel BAJO. Monitorear y reevaluar si hay cambio en la presentacion clinica."
        ),
        "nivel_sugerido": "bajo",
        "palabras_clave": ["dolor leve", "malestar", "cansancio", "dolor muscular", "consulta",
                           "revision", "chequeo", "pregunta medica"]
    },
]
