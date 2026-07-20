"""
SAMR-22: Interoperabilidad HL7 FHIR
Motor de conversión de entidades del sistema SAMR (Pacientes, Historial Clínico, Recetas) 
al estándar internacional HL7 FHIR v4.0.1 para garantizar la interoperabilidad con 
entidades gubernamentales (MSP, IESS) y otros sistemas de salud.
"""
from datetime import date
from django.utils import timezone
from .models import Paciente, TriageLog, Receta

class FHIREngine:
    
    @staticmethod
    def _format_date(d):
        if not d:
            return None
        if isinstance(d, date):
            return d.isoformat()
        return d

    @staticmethod
    def export_patient_to_fhir(paciente: Paciente) -> dict:
        """
        Convierte un objeto Paciente de SAMR al recurso 'Patient' de HL7 FHIR.
        """
        user = paciente.usuario
        
        # Mapeo de género a los valores estándar de FHIR
        gender_map = {
            'M': 'male',
            'F': 'female',
            'O': 'other'
        }
        fhir_gender = gender_map.get(user.sexo, 'unknown')

        fhir_patient = {
            "resourceType": "Patient",
            "id": str(user.dni or user.id),
            "identifier": [
                {
                    "system": "http://salud.gob.ec/identificadores/cedula",
                    "value": user.dni
                }
            ] if user.dni else [],
            "name": [
                {
                    "use": "official",
                    "family": user.last_name,
                    "given": [user.first_name]
                }
            ],
            "telecom": [
                {
                    "system": "phone",
                    "value": user.telefono_principal,
                    "use": "mobile"
                }
            ] if user.telefono_principal else [],
            "gender": fhir_gender,
            "birthDate": FHIREngine._format_date(user.fecha_nacimiento),
            "address": [
                {
                    "use": "home",
                    "text": user.direccion
                }
            ] if user.direccion else [],
            "extension": [
                {
                    "url": "http://samr.salud/fhir/StructureDefinition/historial-basico",
                    "valueString": paciente.historialClinicoBasico or "Sin registro"
                },
                {
                    "url": "http://samr.salud/fhir/StructureDefinition/alergias",
                    "valueString": paciente.alergias or "Sin alergias conocidas"
                }
            ]
        }
        
        return {k: v for k, v in fhir_patient.items() if v}

    @staticmethod
    def export_clinical_encounter_to_fhir(triaje: TriageLog) -> dict:
        """
        Convierte un triaje/consulta de SAMR al recurso 'Encounter' y 'Condition' de HL7 FHIR.
        """
        user_paciente = triaje.paciente.usuario
        paciente_ref = f"Patient/{user_paciente.dni or user_paciente.id}"
        
        medico_ref = None
        if triaje.medico_asignado:
            medico_ref = f"Practitioner/{triaje.medico_asignado.id}"

        # Recurso Encounter
        encounter = {
            "resourceType": "Encounter",
            "id": f"triaje-{triaje.id}",
            "status": "finished" if triaje.estado_asignacion == 'ATENDIDO' else "in-progress",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "VR",
                "display": "virtual"
            },
            "subject": {
                "reference": paciente_ref
            },
            "participant": [
                {
                    "type": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                    "code": "ATND",
                                    "display": "attender"
                                }
                            ]
                        }
                    ],
                    "individual": {
                        "reference": medico_ref
                    }
                }
            ] if medico_ref else [],
            "period": {
                "start": triaje.timestamp.isoformat()
            }
        }
        
        # Recurso ClinicalImpression (La evaluación de la IA y el médico)
        impression = {
            "resourceType": "ClinicalImpression",
            "id": f"impression-{triaje.id}",
            "status": "completed",
            "subject": {
                "reference": paciente_ref
            },
            "encounter": {
                "reference": f"Encounter/{encounter['id']}"
            },
            "summary": triaje.resumen_medico,
            "description": triaje.sintomas_reportados
        }
        
        # Envolver en un Bundle
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {"resource": encounter},
                {"resource": impression}
            ]
        }
        
        return bundle
