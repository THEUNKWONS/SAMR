"""
SAMR-15: Motor de Derivacion y Matching Inteligente
Asigna el mejor medico disponible a un paciente basado en el triaje generado por IA (nivel de alerta, especialidad requerida y carga de trabajo del medico).
"""

from .models import MedicoEspecialista, MedicoAsistente, Usuario

class MatchingEngine:
    @staticmethod
    def encontrar_mejor_medico(nivel_alerta, categoria_sugerida=None):
        """
        Encuentra el medico mas adecuado basado en su carga de trabajo y disponibilidad.
        Si es nivel critico o medio, prioriza especialistas. 
        Si hay categoria sugerida, prioriza la especialidad coincidente.
        """
        # 1. Intentar hacer match con Medico Especialista primero para casos medios/criticos
        if nivel_alerta in ['critico', 'medio']:
            especialistas = MedicoEspecialista.objects.filter(disponible=True)
            
            # Si hay una categoria (ej: 'Cardiovascular'), buscar esa especialidad
            if categoria_sugerida:
                especialistas_match = especialistas.filter(especialidad__icontains=categoria_sugerida)
                if especialistas_match.exists():
                    # Devolver el que tiene menos carga de trabajo
                    return especialistas_match.order_by('carga_trabajo').first().usuario
            
            # Si no hay match exacto o no hay categoria, devolver el de menor carga
            if especialistas.exists():
                return especialistas.order_by('carga_trabajo').first().usuario

        # 2. Para casos 'bajo' o si no hay especialistas, derivar a Medico Asistente
        asistentes = MedicoAsistente.objects.filter(disponible=True)
        if asistentes.exists():
            return asistentes.order_by('carga_trabajo').first().usuario
            
        # 3. Fallback: cualquier especialista si no hay asistentes
        especialistas = MedicoEspecialista.objects.filter(disponible=True)
        if especialistas.exists():
            return especialistas.order_by('carga_trabajo').first().usuario
            
        return None

    @staticmethod
    def asignar_medico_a_triaje(triaje_log, categoria_sugerida=None):
        """
        Encuentra el mejor medico y lo asigna al TriageLog, actualizando su carga de trabajo.
        """
        medico_asignado = MatchingEngine.encontrar_mejor_medico(
            triaje_log.nivel_alerta, 
            categoria_sugerida
        )
        
        if medico_asignado:
            triaje_log.medico_asignado = medico_asignado
            triaje_log.estado_asignacion = 'PENDIENTE'
            triaje_log.save()
            
            # Incrementar la carga de trabajo del medico
            if medico_asignado.tipoUsuario == 'MEDICO_ESPECIALISTA' and hasattr(medico_asignado, 'perfil_especialista'):
                perfil = medico_asignado.perfil_especialista
                perfil.carga_trabajo += 1
                perfil.save()
            elif medico_asignado.tipoUsuario == 'MEDICO_ASISTENTE' and hasattr(medico_asignado, 'perfil_asistente'):
                perfil = medico_asignado.perfil_asistente
                perfil.carga_trabajo += 1
                perfil.save()
                
            return medico_asignado
            
        return None
