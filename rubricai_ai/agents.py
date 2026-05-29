import json
import logging
import re
from typing import Dict, List, Tuple
from neo4j_client import get_neo4j_client
from llm import generate_completion

logger = logging.getLogger(__name__)

class PedagogicalHolisticAgent:
    """Agent in charge of assessing pedagogical alignment, Bloom taxonomy matching, and overall content coherence."""
    
    def evaluate(self, course_data: dict, rubric_data: dict) -> str:
        rubric_str = json.dumps(rubric_data, indent=2, ensure_ascii=False)
        course_str = json.dumps(course_data, indent=2, ensure_ascii=False)
        
        system_prompt = (
            "Eres el Agente Holístico Pedagógico. Tu tarea es analizar de forma profunda y educativa "
            "la alineación constructiva entre todos los recursos y actividades del curso frente a una rúbrica de referencia."
        )
        
        prompt = f"""
        Analiza el siguiente curso (con sus recursos y actividades) frente a la rúbrica pedagógica proporcionada:
        
        ### RÚBRICA DE EVALUACIÓN:
        {rubric_str}
        
        ### DATOS DEL CURSO (Estructura, Actividades, Temas):
        {course_str}
        
        ### TAREA:
        1. Evalúa si los contenidos teóricos provistos en los recursos y actividades cubren adecuadamente los criterios de la rúbrica.
        2. Analiza si el nivel cognitivo de los ítems o preguntas (especialmente en Cuestionarios o Tareas) corresponde al nivel de la Taxonomía de Bloom implícito en la rúbrica.
        3. Identifica vacíos temáticos (gaps) donde falte material o actividades para cumplir con algún criterio.
        4. Escribe un análisis sintético detallado en español. Estructúralo con viñetas claras.
        """
        
        res, _ = generate_completion(prompt, system_prompt)
        return res or "No se pudo generar la evaluación holística."

class FormatStructureAgent:
    """Agent in charge of auditing formatting, settings, technical consistency, and structure of Moodle course elements."""
    
    def evaluate(self, course_data: dict) -> str:
        course_str = json.dumps(course_data, indent=2, ensure_ascii=False)
        
        system_prompt = (
            "Eres el Agente de Formato y Estructura. Tu tarea es auditar las configuraciones técnicas, "
            "completitud, configuraciones de cuestionarios, fechas, ponderaciones y estructura general del aula virtual de Moodle."
        )
        
        prompt = f"""
        Analiza el formato y la configuración técnica del siguiente curso de Moodle:
        
        ### DATOS DE CONFIGURACIÓN DEL CURSO:
        {course_str}
        
        ### TAREA:
        1. Audita si las descripciones (intro) de las actividades están completas o si hay elementos vacíos/insuficientes.
        2. Revisa la coherencia técnica (ej: si hay cuestionarios sin preguntas, tareas sin fecha de entrega o en el pasado).
        3. Verifica si la escala o puntaje de calificación es consistente (ej: si hay pesos incoherentes).
        4. Escribe un análisis detallado en español sobre aspectos técnicos y estructurales del curso.
        """
        
        res, _ = generate_completion(prompt, system_prompt)
        return res or "No se pudo generar la evaluación de formato."

class OntologyAgent:
    """Agent representing the Neo4j ontology. Resolves semantic connections and writes evaluation graph structures."""
    
    def __init__(self):
        self.client = get_neo4j_client()
        
    def sync_course_structure(self, course_id: int, course_title: str, course_data: dict):
        """Syncs the raw course structure nodes into Neo4j."""
        if not self.client or not self.client.initialized:
            logger.warning("Neo4j client not initialized. Skipping course structure sync.")
            return
            
        sections = course_data.get("sections", [])
        activities = []
        resources = []
        
        for sec in sections:
            sec_name = sec.get("name", "Sección")
            for act in sec.get("activities", []):
                act_type = act.get("type", "unknown")
                # Classify into resource or activity
                if act_type in ["resource", "folder", "page", "url", "book", "label"]:
                    resources.append({
                        "id": act.get("name"),
                        "filename": act.get("name"),
                        "name": act.get("name"),
                        "type": act_type
                    })
                else:
                    activities.append({
                        "id": act.get("name"),
                        "name": act.get("name"),
                        "type": act_type,
                        "description": act.get("description", ""),
                        "duedate": act.get("duedate", 0)
                    })
                    
        self.client.sync_course_data(course_id, course_title, activities, resources)

    def log_evaluation_results(self, course_id: int, rubric_id: str, score: float, recommendations: List[dict]):
        """Logs the evaluation and links recommendations to the course node in Neo4j."""
        if not self.client or not self.client.initialized:
            return
            
        # 1. Create relation Course -> Rubric with score metadata
        self.query_cypher = """
        MATCH (c:Course {id: $course_id})
        MATCH (r:Rubric {id: $rubric_id})
        MERGE (c)-[rel:EVALUATED_WITH]->(r)
        SET rel.score = $score,
            rel.timestamp = timestamp()
        """
        self.client.query(self.query_cypher, {"course_id": course_id, "rubric_id": rubric_id, "score": score})
        
        # 2. Add Recommendation nodes
        # Detach old recommendations first
        self.client.query(
            """
            MATCH (c:Course {id: $course_id})-[rel:HAS_RECOMMENDATION]->(rec:Recommendation)
            DETACH DELETE rec
            """,
            {"course_id": course_id}
        )
        
        for idx, rec in enumerate(recommendations):
            self.client.query(
                """
                MATCH (c:Course {id: $course_id})
                CREATE (rec:Recommendation {
                    id: $rec_id,
                    element: $element,
                    type: $type,
                    issue: $issue,
                    change: $change
                })
                CREATE (c)-[:HAS_RECOMMENDATION {order: $order}]->(rec)
                """,
                {
                    "course_id": course_id,
                    "rec_id": f"c_{course_id}_rec_{idx}",
                    "element": rec.get("element", "General"),
                    "type": rec.get("type", "holistic"),
                    "issue": rec.get("issue", ""),
                    "change": rec.get("change", ""),
                    "order": idx
                }
            )

class SynthesisAgent:
    """Agent in charge of consolidating all reports and creating the structured EvaluateResponse."""
    
    def synthesize(self, course_id: int, rubric_id: str, holistic_report: str, format_report: str) -> dict:
        system_prompt = (
            "Eres el Agente Consolidador de RubricAI. Tu tarea es recibir las evaluaciones de formato "
            "y holísticas y generar una respuesta JSON final estrictamente estructurada que contenga el puntaje global, "
            "resúmenes de informes y una lista estructurada de recomendaciones accionables de cambio."
        )
        
        prompt = f"""
        Consolida los siguientes informes de evaluación de la calidad de un curso frente a la rúbrica de referencia.
        
        ### REPORTE HOLÍSTICO:
        {holistic_report}
        
        ### REPORTE DE FORMATO:
        {format_report}
        
        ### TAREA:
        1. Calcula una puntuación global de alineación (overall_score) de 0.0 a 100.0 basada en la severidad de los problemas detectados en ambos reportes.
        2. Redacta una lista estructurada de recomendaciones específicas para el docente. Cada recomendación debe tener:
           - `element`: la actividad/recurso específica (ej: "Foro N°1" o "General" si aplica a todo).
           - `type`: el tipo de problema, estrictamente uno de los siguientes: "holistic" o "format".
           - `issue`: explicación breve de qué está mal o falta.
           - `change`: instrucción exacta y detallada de qué cambiar en Moodle para solucionarlo.
        
        ### FORMATO DE SALIDA (Responde ÚNICAMENTE en JSON con esta estructura):
        {{
          "overall_score": 85.5,
          "holistic_evaluation": "Resumen consolidado de la alineación pedagógica...",
          "format_evaluation": "Resumen consolidado del estado técnico y estructural del curso...",
          "recommendations": [
            {{
              "element": "Nombre de la Actividad o Recurso",
              "type": "holistic|format",
              "issue": "Problema específico...",
              "change": "Acción recomendada detallada para cambiar en Moodle..."
            }}
          ]
        }}
        """
        
        res, _ = generate_completion(prompt, system_prompt)
        
        try:
            clean_json = re.sub(r'^```json|```$', '', res, flags=re.MULTILINE).strip()
            data = json.loads(clean_json)
            # Add identifiers
            data["course_id"] = course_id
            data["rubric_id"] = rubric_id
            return data
        except Exception as e:
            logger.error(f"Failed to parse consolidated JSON: {e}. Raw response: {res}")
            # Fallback structure
            return {
                "course_id": course_id,
                "rubric_id": rubric_id,
                "overall_score": 50.0,
                "holistic_evaluation": holistic_report,
                "format_evaluation": format_report,
                "recommendations": [
                    {
                        "element": "General",
                        "type": "holistic",
                        "issue": "No se pudo estructurar el JSON automáticamente.",
                        "change": "Por favor revisa los reportes holísticos y de formato adjuntos."
                    }
                ]
            }

class MultiAgentCoordinator:
    """Coordinator that orchestrates the entire evaluation workflow."""
    
    def __init__(self):
        self.holistic_agent = PedagogicalHolisticAgent()
        self.format_agent = FormatStructureAgent()
        self.ontology_agent = OntologyAgent()
        self.synthesis_agent = SynthesisAgent()
        
    def evaluate_course(self, course_id: int, rubric_id: str, course_data: dict) -> dict:
        # 1. Fetch rubric from Neo4j
        rubric_data = None
        if self.ontology_agent.client and self.ontology_agent.client.initialized:
            rubric_data = self.ontology_agent.client.get_rubric(rubric_id)
            
        if not rubric_data:
            logger.warning(f"Rubric {rubric_id} not found in Neo4j. Using generic mock rubric.")
            rubric_data = {
                "id": rubric_id,
                "title": "Rúbrica Genérica de Calidad",
                "criteria": [
                    {"name": "Alineación Pedagógica", "description": "Grado en que las actividades evalúan los objetivos de aprendizaje.", "weight": 50},
                    {"name": "Claridad y Completitud", "description": "Las instrucciones de las actividades son claras y no tienen campos vacíos.", "weight": 50}
                ]
            }
            
        # 2. Sync Course structure to Neo4j database
        logger.info(f"Syncing course structure in Neo4j for course {course_id}...")
        course_title = course_data.get("fullname", f"Curso {course_id}")
        self.ontology_agent.sync_course_structure(course_id, course_title, course_data)
        
        # 3. Run agents evaluations
        logger.info("Running holistic pedagogical agent evaluation...")
        holistic_report = self.holistic_agent.evaluate(course_data, rubric_data)
        
        logger.info("Running technical format agent evaluation...")
        format_report = self.format_agent.evaluate(course_data)
        
        # 4. Consolidate results via Synthesis Agent
        logger.info("Running synthesis agent to consolidate reports...")
        evaluation_result = self.synthesis_agent.synthesize(course_id, rubric_id, holistic_report, format_report)
        
        # 5. Log evaluation results and recommendations in Neo4j graph database
        logger.info("Logging evaluation results and recommendations in Neo4j graph...")
        self.ontology_agent.log_evaluation_results(
            course_id=course_id,
            rubric_id=rubric_id,
            score=evaluation_result.get("overall_score", 0.0),
            recommendations=evaluation_result.get("recommendations", [])
        )
        
        return evaluation_result
