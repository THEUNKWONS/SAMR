"""
SAMR-US-2.2: Motor RAG Bibliográfico para el Especialista Médico
Genera resúmenes clínicos sustentados en libros médicos de referencia para
evitar alucinaciones de IA, proporcionando citas verificables al especialista.

A diferencia del motor de triaje de pacientes (SAMR-13 / rag_engine.py),
este motor está orientado al clínico:
  - Consulta la base bibliográfica (medical_bibliography.py) en lugar de
    los protocolos de síntomas (medical_protocols.py)
  - Devuelve referencias completas (autor, libro, edición, páginas) junto
    al fragmento de contenido relevante
  - El contexto generado está redactado en lenguaje técnico clínico

Arquitectura RAG simplificada:
  1. Recibe síntomas + resumen_medico del triaje (query enriquecida)
  2. Tokeniza y calcula score de relevancia contra la bibliografía
  3. Rankea por relevancia descendente y devuelve top-K fragmentos
  4. Construye un contexto formateado con citas APA para el LLM
"""

from .medical_bibliography import BIBLIOGRAFIA_MEDICA


class SpecialistRAGEngine:
    """
    SAMR-US-2.2: Motor RAG bibliográfico para el especialista médico.
    Recupera fragmentos de libros médicos de referencia según los síntomas
    del paciente para fundamentar el resumen clínico con fuentes verificables.
    """

    def __init__(self, bibliografia=None):
        self.bibliografia = bibliografia or BIBLIOGRAFIA_MEDICA

    def recuperar_referencias(self, query, top_k=3):
        """
        SAMR-US-2.2: Recupera los top_k fragmentos bibliográficos más
        relevantes para la query (síntomas + resumen médico del triaje).

        Args:
            query (str): Texto con síntomas y/o resumen clínico del triaje.
            top_k (int): Número máximo de referencias a devolver.

        Returns:
            list[dict]: Lista de referencias ordenadas por relevancia, cada
                        una con un campo 'relevancia_score' agregado.
        """
        if not query or not query.strip():
            return []

        query_lower = query.lower()
        tokens_query = set(query_lower.split())

        resultados = []

        for referencia in self.bibliografia:
            score = self._calcular_relevancia(query_lower, tokens_query, referencia)
            if score > 0:
                resultado = referencia.copy()
                resultado['relevancia_score'] = score
                resultados.append(resultado)

        # Ordenar por relevancia descendente
        resultados.sort(key=lambda x: x['relevancia_score'], reverse=True)

        return resultados[:top_k]

    def _calcular_relevancia(self, query_lower, tokens_query, referencia):
        """
        SAMR-US-2.2: Calcula score de relevancia entre la query y una referencia.
        Sistema de pesos:
          - Coincidencia exacta de frase clave: +4 puntos
          - Coincidencia parcial por token: +1.5 puntos
          - Coincidencia en contenido del fragmento (tokens >3 chars): +0.5 puntos
          - Coincidencia de categoría en la query: +2 puntos bonus
        """
        score = 0

        # Coincidencia con palabras clave de la referencia
        for kw in referencia.get('palabras_clave', []):
            kw_lower = kw.lower()
            if kw_lower in query_lower:
                score += 4  # Coincidencia exacta de frase
            else:
                tokens_kw = set(kw_lower.split())
                coincidencias = tokens_kw.intersection(tokens_query)
                if coincidencias:
                    score += len(coincidencias) * 1.5

        # Coincidencia en el contenido del fragmento bibliográfico
        contenido_lower = referencia.get('contenido', '').lower()
        for token in tokens_query:
            if len(token) > 3 and token in contenido_lower:
                score += 0.5

        # Bonus si la categoría del libro coincide con algún término de la query
        categoria = referencia.get('categoria', '').lower()
        if categoria and categoria in query_lower:
            score += 2

        return score

    def construir_contexto_bibliografico(self, query, top_k=3):
        """
        SAMR-US-2.2: Construye el bloque de contexto bibliográfico listo
        para inyectar en el prompt del LLM orientado al especialista.

        Args:
            query (str): Síntomas y/o resumen clínico del triaje.
            top_k (int): Número máximo de referencias a incluir.

        Returns:
            str: Texto formateado con fragmentos y citas bibliográficas,
                 o mensaje por defecto si no hay referencias relevantes.
        """
        referencias = self.recuperar_referencias(query, top_k)

        if not referencias:
            return (
                "No se encontraron referencias bibliográficas específicas para este cuadro clínico. "
                "Se recomienda aplicar criterio clínico con guías de práctica actualizadas."
            )

        partes = [
            "=== REFERENCIAS BIBLIOGRÁFICAS RECUPERADAS (RAG — Libros Médicos) ==="
        ]

        for i, ref in enumerate(referencias, 1):
            cita_apa = (
                f"{ref['autores']} ({ref['anio']}). {ref['capitulo']}. "
                f"En {ref['titulo_libro']} ({ref['edicion']}, pp. {ref['paginas']}). "
                f"{ref['editorial']}."
            )
            partes.append(
                f"\n--- Referencia {i}: [{ref['id']}] "
                f"(Categoría: {ref['categoria']}, Relevancia: {ref['relevancia_score']:.1f}) ---\n"
                f"📚 Cita: {cita_apa}\n"
                f"Fragmento clínico:\n{ref['contenido']}\n"
            )

        partes.append(
            "\n=== FIN DE REFERENCIAS BIBLIOGRÁFICAS RAG ===\n"
            "IMPORTANTE: Usa estos fragmentos como sustento verificable. "
            "Cita las fuentes explícitamente en tu resumen clínico para el especialista."
        )

        return "\n".join(partes)

    def obtener_referencias_como_lista(self, query, top_k=3):
        """
        SAMR-US-2.2: Devuelve las referencias en formato de lista de diccionarios
        (para serializar como JSON en la respuesta API al frontend).

        Returns:
            list[dict]: Lista de dicts con titulo_libro, autores, edicion,
                        capitulo, paginas, anio, id y relevancia_score.
        """
        referencias = self.recuperar_referencias(query, top_k)
        return [
            {
                "id": r["id"],
                "titulo_libro": r["titulo_libro"],
                "autores": r["autores"],
                "edicion": r["edicion"],
                "editorial": r["editorial"],
                "anio": r["anio"],
                "capitulo": r["capitulo"],
                "paginas": r["paginas"],
                "categoria": r["categoria"],
                "relevancia_score": round(r["relevancia_score"], 1),
            }
            for r in referencias
        ]


# SAMR-US-2.2: Instancia singleton del motor RAG bibliográfico del especialista
specialist_rag_engine = SpecialistRAGEngine()
