"""
SAMR-13: Motor RAG (Retrieval-Augmented Generation) para Triaje Medico
Recupera protocolos medicos relevantes basandose en los sintomas del paciente
para enriquecer el contexto del modelo de IA antes de generar el triaje.

Arquitectura RAG simplificada:
1. Recibe los sintomas del paciente (query)
2. Tokeniza y busca coincidencias por palabras clave en la base de protocolos
3. Rankea protocolos por relevancia (score de coincidencia)
4. Devuelve los top-K protocolos mas relevantes como contexto adicional
"""

from .medical_protocols import PROTOCOLOS_MEDICOS


class RAGTriageEngine:
    """
    Motor de Recuperacion Aumentada (RAG) para triaje medico.
    Busca en la base de conocimiento de protocolos medicos los documentos
    mas relevantes para los sintomas reportados por el paciente.
    """

    def __init__(self, protocolos=None):
        self.protocolos = protocolos or PROTOCOLOS_MEDICOS

    def recuperar_protocolos(self, sintomas, top_k=3):
        """
        Recupera los top_k protocolos mas relevantes para los sintomas dados.

        Args:
            sintomas (str): Texto con los sintomas del paciente.
            top_k (int): Numero maximo de protocolos a devolver.

        Returns:
            list[dict]: Lista de protocolos ordenados por relevancia, cada uno con
                        un campo 'relevancia_score' agregado.
        """
        if not sintomas or not sintomas.strip():
            return []

        sintomas_lower = sintomas.lower()
        tokens_sintomas = set(sintomas_lower.split())

        resultados = []

        for protocolo in self.protocolos:
            score = self._calcular_relevancia(sintomas_lower, tokens_sintomas, protocolo)
            if score > 0:
                resultado = protocolo.copy()
                resultado['relevancia_score'] = score
                resultados.append(resultado)

        # Ordenar por relevancia descendente
        resultados.sort(key=lambda x: x['relevancia_score'], reverse=True)

        return resultados[:top_k]

    def _calcular_relevancia(self, sintomas_lower, tokens_sintomas, protocolo):
        """
        Calcula un score de relevancia entre los sintomas y un protocolo.
        Usa coincidencia de palabras clave con pesos diferenciados:
        - Coincidencia exacta de frase clave: +3 puntos
        - Coincidencia parcial de palabra clave: +1 punto
        - Coincidencia en contenido del protocolo: +0.5 puntos
        """
        score = 0

        # Buscar coincidencias en palabras clave del protocolo
        for palabra_clave in protocolo.get('palabras_clave', []):
            palabra_lower = palabra_clave.lower()
            # Coincidencia exacta de la frase completa en los sintomas
            if palabra_lower in sintomas_lower:
                score += 3
            else:
                # Coincidencia parcial: alguna palabra del keyword esta en los sintomas
                palabras_kw = set(palabra_lower.split())
                coincidencias = palabras_kw.intersection(tokens_sintomas)
                if coincidencias:
                    score += len(coincidencias)

        # Bonus por coincidencia en el contenido del protocolo
        contenido_lower = protocolo.get('contenido', '').lower()
        for token in tokens_sintomas:
            if len(token) > 3 and token in contenido_lower:
                score += 0.5

        return score

    def construir_contexto_rag(self, sintomas, top_k=3):
        """
        Construye el texto de contexto RAG listo para inyectar en el prompt del LLM.

        Args:
            sintomas (str): Texto con los sintomas del paciente.
            top_k (int): Numero maximo de protocolos a incluir.

        Returns:
            str: Texto formateado con los protocolos relevantes, o mensaje por defecto
                 si no se encontraron protocolos relevantes.
        """
        protocolos = self.recuperar_protocolos(sintomas, top_k)

        if not protocolos:
            return "No se encontraron protocolos clinicos especificos para estos sintomas. Aplicar evaluacion clinica general."

        contexto_partes = [
            "=== PROTOCOLOS CLINICOS RECUPERADOS (RAG) ==="
        ]

        for i, prot in enumerate(protocolos, 1):
            contexto_partes.append(
                f"\n--- Protocolo {i}: [{prot['id']}] {prot['titulo']} "
                f"(Categoria: {prot['categoria']}, Relevancia: {prot['relevancia_score']:.1f}) ---\n"
                f"{prot['contenido']}\n"
                f"Nivel sugerido por protocolo: {prot['nivel_sugerido'].upper()}"
            )

        contexto_partes.append(
            "\n=== FIN DE PROTOCOLOS RAG ==="
            "\nIMPORTANTE: Utiliza estos protocolos como referencia clinica para tu evaluacion. "
            "Ajusta el nivel de alerta segun la gravedad real de los sintomas del paciente."
        )

        return "\n".join(contexto_partes)

    def obtener_nivel_sugerido(self, sintomas):
        """
        Devuelve el nivel de alerta sugerido por el protocolo mas relevante.
        Util como referencia cruzada con la decision del LLM.

        Args:
            sintomas (str): Texto con los sintomas del paciente.

        Returns:
            str: Nivel sugerido ('critico', 'medio', 'bajo') o 'bajo' por defecto.
        """
        protocolos = self.recuperar_protocolos(sintomas, top_k=1)
        if protocolos:
            return protocolos[0].get('nivel_sugerido', 'bajo')
        return 'bajo'


# Instancia singleton del motor RAG para reutilizar en las vistas
rag_engine = RAGTriageEngine()
