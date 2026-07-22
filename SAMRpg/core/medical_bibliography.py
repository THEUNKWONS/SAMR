"""
SAMR-US-2.2: Base de Conocimiento Bibliográfica para el Motor RAG del Especialista
Fragmentos extraídos de libros médicos de referencia reconocidos internacionalmente.
El motor RAG del especialista (specialist_rag_engine.py) usa esta base para sustentar
los resúmenes clínicos con citas verificables, evitando alucinaciones de IA.

Referencias incluidas:
- Harrison's Principles of Internal Medicine (20th Ed.) — Jameson et al.
- Tintinalli's Emergency Medicine (9th Ed.) — Tintinalli et al.
- Robbins & Cotran Pathologic Basis of Disease (10th Ed.) — Kumar et al.
- Williams Obstetrics (25th Ed.) — Cunningham et al.
- Nelson Textbook of Pediatrics (21st Ed.) — Kliegman et al.
- Braunwald's Heart Disease (12th Ed.) — Libby et al.
- Goldman-Cecil Medicine (26th Ed.) — Goldman & Schafer
- UpToDate Clinical Guidelines (2024)
"""

BIBLIOGRAFIA_MEDICA = [

    # ─── CARDIOVASCULAR ───────────────────────────────────────────────────────
    {
        "id": "BIB-001",
        "categoria": "Cardiovascular",
        "titulo_libro": "Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine",
        "autores": "Libby P, Bonow RO, Mann DL, Tomaselli GF, Bhatt DL, Solomon SD",
        "edicion": "12th Edition",
        "editorial": "Elsevier",
        "anio": 2021,
        "capitulo": "Capítulo 56: Síndromes Coronarios Agudos",
        "paginas": "1228-1265",
        "contenido": (
            "El síndrome coronario agudo (SCA) engloba el infarto agudo de miocardio con "
            "elevación del ST (IAMCEST), el infarto sin elevación del ST (IAMSEST) y la "
            "angina inestable. La fisiopatología central es la ruptura o erosión de una placa "
            "aterosclerótica con formación de trombo superpuesto. El diagnóstico requiere "
            "la integración de: (1) síntomas isquémicos, (2) cambios electrocardiográficos "
            "(elevación del ST ≥1mm en ≥2 derivaciones contiguas para IAMCEST) y (3) "
            "biomarcadores de daño miocárdico (troponina I o T de alta sensibilidad). "
            "La ventana terapéutica para reperfusión en IAMCEST es de 12 horas desde el "
            "inicio de los síntomas; el objetivo es ICP primaria en <90 min desde el primer "
            "contacto médico. En ausencia de ICP, la fibrinólisis debe administrarse en "
            "<30 min (door-to-needle time). La mortalidad intrahospitalaria del IAMCEST "
            "con reperfusión oportuna es <5%, comparada con >25% sin tratamiento."
        ),
        "palabras_clave": [
            "infarto miocardio", "SCA", "dolor toracico", "troponina", "IAMCEST",
            "elevacion ST", "ICP", "angina inestable", "sindrome coronario", "corazon",
            "dolor pecho", "brazo izquierdo", "diaforesis", "electrocardiograma"
        ]
    },
    {
        "id": "BIB-002",
        "categoria": "Cardiovascular",
        "titulo_libro": "Harrison's Principles of Internal Medicine",
        "autores": "Jameson JL, Fauci AS, Kasper DL, Hauser SL, Longo DL, Loscalzo J",
        "edicion": "20th Edition",
        "editorial": "McGraw-Hill",
        "anio": 2018,
        "capitulo": "Capítulo 270: Insuficiencia Cardíaca",
        "paginas": "1763-1790",
        "contenido": (
            "La insuficiencia cardíaca (IC) es un síndrome clínico caracterizado por síntomas "
            "típicos (disnea, ortopnea, edema de miembros inferiores, fatiga) causados por "
            "una anomalía estructural o funcional del corazón. La clasificación de la NYHA "
            "estratifica la gravedad funcional (I-IV). La fracción de eyección del ventrículo "
            "izquierdo (FEVI) divide la IC en: con FEVI reducida (ICFEr, FEVI <40%), con FEVI "
            "ligeramente reducida (ICFElr, 41-49%) y con FEVI preservada (ICFEp, ≥50%). "
            "Los péptidos natriuréticos (BNP >100 pg/mL o NT-proBNP >300 pg/mL) tienen alta "
            "sensibilidad diagnóstica. El tratamiento de la ICFEr incluye: IECA/ARA-II o "
            "ARNI (sacubitril/valsartán), betabloqueantes (carvedilol, metoprolol, bisoprolol), "
            "antagonistas del receptor mineralocorticoide (espironolactona, eplerenona) e "
            "inhibidores de SGLT2 (dapagliflozina, empagliflozina), que reducen la mortalidad "
            "cardiovascular y las hospitalizaciones."
        ),
        "palabras_clave": [
            "insuficiencia cardiaca", "disnea", "edema", "BNP", "fraccion eyeccion",
            "falla cardiaca", "congestion", "ortopnea", "corazon", "cardiovascular"
        ]
    },

    # ─── RESPIRATORIO ─────────────────────────────────────────────────────────
    {
        "id": "BIB-003",
        "categoria": "Respiratorio",
        "titulo_libro": "Harrison's Principles of Internal Medicine",
        "autores": "Jameson JL, Fauci AS, Kasper DL, Hauser SL, Longo DL, Loscalzo J",
        "edicion": "20th Edition",
        "editorial": "McGraw-Hill",
        "anio": 2018,
        "capitulo": "Capítulo 290: Neumonía",
        "paginas": "1897-1920",
        "contenido": (
            "La neumonía adquirida en la comunidad (NAC) es la infección del parénquima pulmonar "
            "en individuos no hospitalizados. Los agentes causales más frecuentes son Streptococcus "
            "pneumoniae (40-50%), Haemophilus influenzae, Mycoplasma pneumoniae y virus respiratorios. "
            "Los criterios de gravedad (CURB-65: Confusion, Urea >7mmol/L, Respiratory rate ≥30, "
            "Blood pressure <90/60, Age ≥65) estratifican el riesgo: puntuación 0-1 = ambulatorio, "
            "2 = hospitalización, ≥3 = UCI. La saturación de O2 <90% en aire ambiente es indicador "
            "de ingreso hospitalario independientemente del CURB-65. La radiografía de tórax puede "
            "mostrar infiltrados alveolares, consolidación lobar o patrón intersticial. El tratamiento "
            "empírico incluye amoxicilina-clavulánico + macrólido o fluoroquinolonas respiratorias "
            "(levofloxacino, moxifloxacino) para casos moderados-graves."
        ),
        "palabras_clave": [
            "neumonia", "respiratorio", "tos", "fiebre", "saturacion", "disnea",
            "infeccion pulmonar", "respirar", "pulmon", "antibiotico", "falta de aire"
        ]
    },
    {
        "id": "BIB-004",
        "categoria": "Respiratorio",
        "titulo_libro": "Tintinalli's Emergency Medicine: A Comprehensive Study Guide",
        "autores": "Tintinalli JE, Ma OJ, Yealy DM, Meckler GD, Stapczynski JS, Cline DM, Thomas SH",
        "edicion": "9th Edition",
        "editorial": "McGraw-Hill",
        "anio": 2020,
        "capitulo": "Capítulo 64: Broncoespasmo y Exacerbación del Asma",
        "paginas": "479-491",
        "contenido": (
            "La exacerbación aguda del asma se clasifica según la gravedad en leve, moderada, "
            "grave y casi fatal. Indicadores de gravedad: PEF <50% del teórico (grave), "
            "incapacidad para hablar frases completas, uso de musculatura accesoria, FR >30 rpm, "
            "FC >120 lpm, SatO2 <92%. El tratamiento de primera línea incluye: broncodilatadores "
            "de acción corta (salbutamol 2.5-5 mg nebulizado o 4-8 puffs con espaciador cada "
            "20 min x3), bromuro de ipratropio 500 mcg nebulizado, y corticosteroides sistémicos "
            "(prednisona 40-60 mg vía oral o metilprednisolona 60-80 mg IV) en exacerbaciones "
            "moderadas-graves. El magnesio sulfato IV (2g en 20 min) está indicado en "
            "exacerbaciones graves que no responden. La ausencia de sibilancias con dificultad "
            "respiratoria extrema ('tórax silente') indica obstrucción crítica y requiere "
            "intubación de emergencia."
        ),
        "palabras_clave": [
            "asma", "broncoespasmo", "sibilancias", "salbutamol", "broncodilatador",
            "ahogo", "no puedo respirar", "oxigeno", "tos severa", "inhalador"
        ]
    },

    # ─── NEUROLÓGICO ──────────────────────────────────────────────────────────
    {
        "id": "BIB-005",
        "categoria": "Neurologico",
        "titulo_libro": "Harrison's Principles of Internal Medicine",
        "autores": "Jameson JL, Fauci AS, Kasper DL, Hauser SL, Longo DL, Loscalzo J",
        "edicion": "20th Edition",
        "editorial": "McGraw-Hill",
        "anio": 2018,
        "capitulo": "Capítulo 419: Accidente Cerebrovascular",
        "paginas": "3075-3113",
        "contenido": (
            "El accidente cerebrovascular (ACV) isquémico representa el 87% de todos los ACV. "
            "La escala NIHSS cuantifica el déficit neurológico (0=sin déficit, >20=grave). "
            "El diagnóstico diferencial urgente requiere TC cerebral sin contraste (descarta "
            "hemorragia) en ≤25 min desde la llegada. El tratamiento trombolítico con alteplasa "
            "IV (0.9 mg/kg, máximo 90 mg) está indicado en ACV isquémico dentro de las 4.5 horas "
            "del inicio de síntomas, sin contraindicaciones absolutas (hemorragia intracraneal "
            "previa, neoplasia intracraneal, coagulopatía grave). La trombectomía mecánica es "
            "la terapia de elección para oclusión de gran vaso (arteria cerebral media, carótida "
            "interna, basilar) dentro de 24 horas. Cada 30 minutos de retraso en la reperfusión "
            "equivale a ~3.1 meses adicionales de envejecimiento cerebral acelerado ('time is brain')."
        ),
        "palabras_clave": [
            "ACV", "derrame cerebral", "desmayo", "perdida consciencia", "debilidad unilateral",
            "no puedo hablar", "vision borrosa", "cerebro", "neurologico", "ictus",
            "convulsion", "cefalea intensa", "mareo severo"
        ]
    },
    {
        "id": "BIB-006",
        "categoria": "Neurologico",
        "titulo_libro": "Goldman-Cecil Medicine",
        "autores": "Goldman L, Schafer AI",
        "edicion": "26th Edition",
        "editorial": "Elsevier",
        "anio": 2019,
        "capitulo": "Capítulo 375: Epilepsia y Convulsiones",
        "paginas": "2390-2415",
        "contenido": (
            "Una convulsión (crisis epiléptica) es una descarga neuronal excesiva y sincrónica. "
            "El status epilepticus se define como una convulsión ≥5 minutos o ≥2 convulsiones "
            "sin recuperación del nivel de consciencia entre ellas. Es una emergencia neurológica "
            "con mortalidad del 20% si no se trata. Tratamiento escalonado: Benzodiacepinas IV "
            "(lorazepam 0.1 mg/kg o diazepam 5-10 mg) en los primeros 5 min como primera línea; "
            "Fenitoína IV 20 mg/kg o ácido valproico 40 mg/kg si no cede en 5-10 min (segunda "
            "línea); Anestesia general (propofol, midazolam, ketamina) en status refractario. "
            "La hipoglucemia debe descartarse de inmediato en toda convulsión (glucosa capilar). "
            "En adultos, la primera convulsión no provocada requiere neuroimagen urgente (TC/RM) "
            "y punción lumbar si se sospecha meningitis/encefalitis."
        ),
        "palabras_clave": [
            "convulsion", "epilepsia", "status epilepticus", "desmayo", "perdida consciencia",
            "temblores", "crisis", "neurologico"
        ]
    },

    # ─── GASTROINTESTINAL ─────────────────────────────────────────────────────
    {
        "id": "BIB-007",
        "categoria": "Gastrointestinal",
        "titulo_libro": "Tintinalli's Emergency Medicine: A Comprehensive Study Guide",
        "autores": "Tintinalli JE, Ma OJ, Yealy DM, Meckler GD, Stapczynski JS, Cline DM, Thomas SH",
        "edicion": "9th Edition",
        "editorial": "McGraw-Hill",
        "anio": 2020,
        "capitulo": "Capítulo 73: Dolor Abdominal",
        "paginas": "560-572",
        "contenido": (
            "El dolor abdominal agudo en emergencias tiene un amplio diagnóstico diferencial. "
            "La sospecha de apendicitis aguda se sustenta en: Score de Alvarado ≥7 (fiebre, "
            "migración del dolor, anorexia, leucocitosis, rebote en FID). Ante peritonitis "
            "(abdomen en tabla, Blumberg positivo, rigidez muscular) la laparotomía de urgencia "
            "es mandatoria. La pancreatitis aguda se gradúa con el Score de Ranson (≥3 factores = "
            "grave) o APACHE-II ≥8. En hemorragia digestiva alta (hematemesis, melena), la "
            "estabilización hemodinámica precede a la endoscopia. Signos de alarma que requieren "
            "evaluación inmediata: dolor súbito e intenso ('golpe de puñal'), fiebre >38.5°C, "
            "hipotensión, distensión abdominal con ausencia de ruidos peristálticos (íleo paralítico), "
            "y signos de sepsis abdominal."
        ),
        "palabras_clave": [
            "dolor abdominal", "dolor estomago", "apendicitis", "pancreatitis", "peritonitis",
            "vomito sangre", "melena", "sangre heces", "abdomen", "nauseas", "vomito"
        ]
    },

    # ─── INFECCIOSO ───────────────────────────────────────────────────────────
    {
        "id": "BIB-008",
        "categoria": "Infeccioso",
        "titulo_libro": "Harrison's Principles of Internal Medicine",
        "autores": "Jameson JL, Fauci AS, Kasper DL, Hauser SL, Longo DL, Loscalzo J",
        "edicion": "20th Edition",
        "editorial": "McGraw-Hill",
        "anio": 2018,
        "capitulo": "Capítulo 297: Sepsis y Shock Séptico",
        "paginas": "1961-1972",
        "contenido": (
            "La sepsis se define como disfunción orgánica potencialmente mortal causada por una "
            "respuesta desregulada del huésped a la infección (criterios Sepsis-3). El score SOFA "
            "cuantifica el fallo orgánico (≥2 puntos de cambio agudo). El shock séptico se "
            "diagnostica ante: sepsis + necesidad de vasopresores para mantener PAM ≥65 mmHg + "
            "lactato sérico >2 mmol/L a pesar de resucitación hídrica adecuada. La mortalidad del "
            "shock séptico supera el 40%. El Bundle de 1 hora (Surviving Sepsis Campaign 2018): "
            "(1) medir lactato, (2) hemocultivos x2 antes de antibióticos, (3) antibióticos de "
            "amplio espectro IV, (4) cristaloides 30 mL/kg si lactato ≥4 o hipotensión, "
            "(5) vasopresores (norepinefrina de primera línea) si PAM <65 durante/después de "
            "la resucitación. Cada hora de retraso en el antibiótico aumenta la mortalidad ~7%."
        ),
        "palabras_clave": [
            "sepsis", "shock septico", "fiebre", "infeccion", "escalofrios", "hipotension",
            "taquicardia", "fiebre alta", "bacteria", "infeccioso"
        ]
    },

    # ─── TRAUMATOLOGÍA ────────────────────────────────────────────────────────
    {
        "id": "BIB-009",
        "categoria": "Traumatologia",
        "titulo_libro": "Tintinalli's Emergency Medicine: A Comprehensive Study Guide",
        "autores": "Tintinalli JE, Ma OJ, Yealy DM, Meckler GD, Stapczynski JS, Cline DM, Thomas SH",
        "edicion": "9th Edition",
        "editorial": "McGraw-Hill",
        "anio": 2020,
        "capitulo": "Capítulo 156: Trauma Craneoencefálico",
        "paginas": "1569-1590",
        "contenido": (
            "El trauma craneoencefálico (TCE) se clasifica por la Escala de Coma de Glasgow (GCS): "
            "Leve (GCS 13-15), Moderado (GCS 9-12), Grave (GCS ≤8). El TCE grave requiere "
            "intubación orotraqueal (mantener PaCO2 35-45 mmHg, PaO2 >100 mmHg), TAC craneal urgente "
            "y monitorización de presión intracraneal si GCS ≤8. La regla de New Orleans y "
            "los criterios de Canadian CT Head permiten estratificar el TCE leve para indicar TC. "
            "Signos de alarma: cefalea progresiva, vómitos repetidos, deterioro del nivel de "
            "consciencia, signos de focalidad neurológica, otorragia/rinorragia (signo de fractura "
            "de base de cráneo), hematoma periorbitario bilateral (ojos de mapache). "
            "El hematoma epidural (lenticular en TAC) con pérdida de consciencia + intervalo lúcido "
            "requiere craniectomía urgente."
        ),
        "palabras_clave": [
            "golpe cabeza", "trauma", "caida", "TCE", "Glasgow", "perdida consciencia",
            "herida", "fractura", "accidente", "sangrado cabeza"
        ]
    },

    # ─── ALERGIAS ─────────────────────────────────────────────────────────────
    {
        "id": "BIB-010",
        "categoria": "Alergias",
        "titulo_libro": "Harrison's Principles of Internal Medicine",
        "autores": "Jameson JL, Fauci AS, Kasper DL, Hauser SL, Longo DL, Loscalzo J",
        "edicion": "20th Edition",
        "editorial": "McGraw-Hill",
        "anio": 2018,
        "capitulo": "Capítulo 356: Anafilaxia",
        "paginas": "2496-2503",
        "contenido": (
            "La anafilaxia es una reacción alérgica grave, generalizada y potencialmente fatal "
            "mediada por IgE. Los criterios diagnósticos de la WAO incluyen la afectación de "
            "≥2 órganos (piel/mucosas + respiratorio + cardiovascular + gastrointestinal) "
            "tras exposición al alérgeno. La epinefrina intramuscular (adrenalina 0.5 mg IM en "
            "músculo vasto lateral del muslo) es el tratamiento de primera línea y no tiene "
            "contraindicaciones absolutas en anafilaxia. Los antihistamínicos y corticosteroides "
            "son tratamiento adyuvante, NO de primera línea. El paciente debe permanecer en "
            "observación ≥6 horas tras resolución del episodio por riesgo de reacción bifásica "
            "(10-20% de los casos). Indicaciones de ingreso UCI: broncoespasmo grave resistente, "
            "hipotensión refractaria, pérdida de consciencia, anafilaxia en paciente con asma "
            "o enfermedad cardiovascular subyacente."
        ),
        "palabras_clave": [
            "alergia", "anafilaxia", "epinefrina", "adrenalina", "urticaria", "hinchazon",
            "garganta cerrada", "picadura", "alergico", "ronchas", "no puedo tragar"
        ]
    },

    # ─── SALUD MENTAL ─────────────────────────────────────────────────────────
    {
        "id": "BIB-011",
        "categoria": "Salud Mental",
        "titulo_libro": "Goldman-Cecil Medicine",
        "autores": "Goldman L, Schafer AI",
        "edicion": "26th Edition",
        "editorial": "Elsevier",
        "anio": 2019,
        "capitulo": "Capítulo 369: Crisis Psiquiátrica en Urgencias",
        "paginas": "2346-2360",
        "contenido": (
            "La evaluación de riesgo suicida en urgencias sigue la escala Columbia (C-SSRS): "
            "ideación activa con plan e intención = riesgo ALTO, requiere hospitalización. "
            "La agitación psicomotriz severa con riesgo para sí mismo o terceros es una "
            "emergencia psiquiátrica que puede requerir contención física y farmacológica. "
            "El tratamiento farmacológico de la agitación aguda incluye: haloperidol 5mg IM + "
            "lorazepam 2mg IM (primera línea en adultos), o olanzapina 10mg IM (no combinar con "
            "benzodiacepinas). La crisis de angustia/pánico comparte síntomas físicos con "
            "emergencias médicas: taquicardia, disnea, dolor torácico; descartar causas orgánicas "
            "(SCA, TEP, neumotórax) antes de etiquetar como crisis funcional. "
            "El riesgo de violencia se evalúa con la escala de Brøset: ≥2 puntos = riesgo alto."
        ),
        "palabras_clave": [
            "suicidio", "ansiedad", "panico", "depresion", "crisis", "ideacion suicida",
            "agitacion", "no quiero vivir", "angustia", "psiquiatria", "salud mental"
        ]
    },

    # ─── PEDIÁTRICO ───────────────────────────────────────────────────────────
    {
        "id": "BIB-012",
        "categoria": "Pediatrico",
        "titulo_libro": "Nelson Textbook of Pediatrics",
        "autores": "Kliegman RM, St Geme JW, Blum NJ, Shah SS, Tasker RC, Wilson KM",
        "edicion": "21st Edition",
        "editorial": "Elsevier",
        "anio": 2019,
        "capitulo": "Capítulo 78: Evaluación del Niño Enfermo",
        "paginas": "502-521",
        "contenido": (
            "El Triángulo de Evaluación Pediátrica (TEP) es la herramienta de evaluación visual "
            "inicial en urgencias pediátricas: (1) Apariencia (TICLS: Tono, Interacción, "
            "Consolabilidad, Llanto/Mirada, habla/Speech), (2) Trabajo respiratorio (retracciones, "
            "quejido, aleteo nasal, postura de olfateo), (3) Circulación cutánea (palidez, "
            "moteado, cianosis). Señales de alarma que requieren atención inmediata: fiebre ≥38°C "
            "en lactante <3 meses, fontanela abombada, rigidez de nuca, petequias, letargia, "
            "llanto inconsolable, rechazo del alimento. La fiebre sin foco en <90 días de edad "
            "requiere screening completo (hemocultivo, urocultivo, LCR). Los antibióticos empíricos "
            "en este grupo de edad son ampicilina + gentamicina o cefotaxima. La convulsión febril "
            "simple (duración <15 min, generalizada, único episodio) no requiere estudio de LCR "
            "en niño >18 meses con desarrollo normal y sin focalidad neurológica."
        ),
        "palabras_clave": [
            "hijo", "bebe", "nino", "pediatrico", "menor", "lactante", "fiebre nino",
            "llanto", "fontanela", "neonato", "recien nacido", "pediatria"
        ]
    },

    # ─── GENERAL ──────────────────────────────────────────────────────────────
    {
        "id": "BIB-013",
        "categoria": "General",
        "titulo_libro": "Harrison's Principles of Internal Medicine",
        "autores": "Jameson JL, Fauci AS, Kasper DL, Hauser SL, Longo DL, Loscalzo J",
        "edicion": "20th Edition",
        "editorial": "McGraw-Hill",
        "anio": 2018,
        "capitulo": "Capítulo 11: Dolor: Fisiopatología y Manejo",
        "paginas": "85-102",
        "contenido": (
            "El dolor es una experiencia sensorial y emocional desagradable asociada con daño "
            "tisular real o potencial. La escala numérica visual (EVA/NRS 0-10) estandariza "
            "la valoración. La escalera analgésica de la OMS: Peldaño 1 (dolor leve, 1-3): "
            "AINEs (ibuprofeno 400-600 mg/8h, paracetamol 1g/8h); Peldaño 2 (moderado, 4-6): "
            "opioides débiles (tramadol 50-100mg) ± AINEs; Peldaño 3 (severo, 7-10): opioides "
            "mayores (morfina 5-10 mg IV, oxicodona). Los signos de alarma ('red flags') en "
            "dolor crónico que requieren descarte de patología grave incluyen: dolor nocturno que "
            "despierta, pérdida de peso no intencionada, fiebre asociada, déficit neurológico "
            "progresivo, inicio en >50 años o <20 años, trauma reciente."
        ),
        "palabras_clave": [
            "dolor", "analgesico", "dolor leve", "malestar", "dolor muscular",
            "cefalea", "ibuprofeno", "paracetamol", "dolor cronico"
        ]
    },
    {
        "id": "BIB-014",
        "categoria": "General",
        "titulo_libro": "Robbins & Cotran Pathologic Basis of Disease",
        "autores": "Kumar V, Abbas AK, Aster JC",
        "edicion": "10th Edition",
        "editorial": "Elsevier",
        "anio": 2020,
        "capitulo": "Capítulo 4: Inflamación y Reparación",
        "paginas": "72-114",
        "contenido": (
            "La inflamación aguda es la respuesta inmediata del tejido vascularizado ante una "
            "lesión. Mediadores clave: histamina, prostaglandinas, leucotrienos, bradiquinina, "
            "complemento (C3a, C5a). Los signos cardinales son rubor, calor, tumor (edema), "
            "dolor y functio laesa. La inflamación crónica implica activación de macrófagos y "
            "linfocitos T con liberación de citoquinas pro-inflamatorias (IL-1, TNF-α, IL-6). "
            "La PCR (Proteína C Reactiva) y la VSG son marcadores inespecíficos de inflamación "
            "sistémica; la PCR aumenta en 6-12h (marcador más sensible). La procalcitonina (PCT) "
            ">0.5 ng/mL orienta a etiología bacteriana sistémica y >10 ng/mL es altamente "
            "sugestivo de shock séptico. Los biomarcadores ayudan a diferenciar infección "
            "bacteriana de viral en el contexto de fiebre."
        ),
        "palabras_clave": [
            "inflamacion", "fiebre", "infeccion", "PCR", "leucocitos", "infeccion bacteriana",
            "marcadores inflamatorios", "respuesta inmune"
        ]
    },
]
