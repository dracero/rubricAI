import os
import logging
from datetime import datetime
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Neo4jClient, cls).__new__(cls, *args, **kwargs)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        logger.info(f"Connecting to Neo4j at {self.uri} (Database: {self.database})")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Test connection
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j database!")
            self.initialized = True
            # Create constraints and seed default ontology
            self.init_database()
        except Exception as e:
            logger.error(f"Error connecting to Neo4j: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed.")

    def query(self, cypher, parameters=None):
        if not self.initialized or not self.driver:
            logger.error("Neo4j driver is not initialized.")
            return []
        
        with self.driver.session(database=self.database) as session:
            try:
                result = session.run(cypher, parameters)
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Error executing Cypher query: {e}\nQuery: {cypher}")
                raise e

    def init_database(self):
        """Create constraints, indexes and seed pedagogical ontology if empty."""
        try:
            # Create constraints
            self.query("CREATE CONSTRAINT unique_rubric_id IF NOT EXISTS FOR (r:Rubric) REQUIRE r.id IS UNIQUE")
            self.query("CREATE CONSTRAINT unique_course_id IF NOT EXISTS FOR (c:Course) REQUIRE c.id IS UNIQUE")
            self.query("CREATE CONSTRAINT unique_bloom_level IF NOT EXISTS FOR (b:BloomLevel) REQUIRE b.level IS UNIQUE")
            self.query("CREATE CONSTRAINT unique_dimension IF NOT EXISTS FOR (d:PedagogicalDimension) REQUIRE d.name IS UNIQUE")
            
            # Seed Bloom Taxonomy levels
            bloom_levels = [
                {"level": "Recordar", "desc": "Recordar hechos y conceptos básicos sin necesidad de entenderlos."},
                {"level": "Comprender", "desc": "Mostrar entendimiento básico de hechos e ideas al organizar y comparar."},
                {"level": "Aplicar", "desc": "Resolver problemas en situaciones nuevas aplicando el conocimiento adquirido."},
                {"level": "Analizar", "desc": "Examinar y descomponer la información en partes identificando causas."},
                {"level": "Evaluar", "desc": "Presentar y defender opiniones realizando juicios basados en criterios."},
                {"level": "Crear", "desc": "Compilar información de manera diferente combinando elementos en un nuevo patrón."}
            ]
            
            for b in bloom_levels:
                self.query(
                    "MERGE (b:BloomLevel {level: $level}) ON CREATE SET b.description = $desc",
                    {"level": b["level"], "desc": b["desc"]}
                )

            # Seed Pedagogical Dimensions
            dimensions = [
                {"name": "Contenidos", "desc": "Conceptos teóricos y prácticos del curso evaluados."},
                {"name": "Procedimiento", "desc": "Habilidades metodológicas e instrumentales aplicadas por el alumno."},
                {"name": "Actitud/Participación", "desc": "Compromiso, etiqueta en foros y calidad del debate interactivo."},
                {"name": "Formato/Estructura", "desc": "Cumplimiento de las reglas técnicas de Moodle (fechas, ponderaciones)."}
            ]
            
            for d in dimensions:
                self.query(
                    "MERGE (d:PedagogicalDimension {name: $name}) ON CREATE SET d.description = $desc",
                    {"name": d["name"], "desc": d["desc"]}
                )
                
            logger.info("Neo4j Database initialized with default constraints and seed ontology.")
        except Exception as e:
            logger.error(f"Failed to initialize database constraints: {e}")

    # --- Rubric Persistence Methods ---

    def save_rubric(self, rubric_data: dict) -> str:
        """Saves a rubric dictionary to Neo4j as a structured graph."""
        rubric_id = rubric_data.get("id") or f"rubric_{int(datetime.now().timestamp())}"
        title = rubric_data.get("title", "Sin título")
        description = rubric_data.get("description", "")
        criteria = rubric_data.get("criteria", [])
        
        # 0. Delete ALL existing rubrics, criteria, and levels to ensure only ONE active rubric exists
        self.query(
            """
            MATCH (r:Rubric)
            OPTIONAL MATCH (r)-[:HAS_CRITERION]->(c:Criterion)
            OPTIONAL MATCH (c)-[:HAS_LEVEL]->(l:Level)
            DETACH DELETE r, c, l
            """
        )
        
        # 1. Create Rubric Node
        self.query(
            """
            MERGE (r:Rubric {id: $id})
            SET r.title = $title,
                r.description = $description,
                r.updated_at = timestamp()
            """,
            {"id": rubric_id, "title": title, "description": description}
        )
        
        # 2. Clear old criteria for this rubric (if updating)
        self.query(
            """
            MATCH (r:Rubric {id: $id})-[rel:HAS_CRITERION]->(c:Criterion)
            OPTIONAL MATCH (c)-[lrel:HAS_LEVEL]->(l:Level)
            DETACH DELETE c, l
            """,
            {"id": rubric_id}
        )
        
        # 3. Create new criteria and levels
        for idx, crit in enumerate(criteria):
            crit_name = crit.get("name", f"Criterio {idx+1}")
            crit_desc = crit.get("description", "")
            crit_weight = crit.get("weight", 0)
            dimension = crit.get("dimension", "Contenidos")
            
            # Create Criterion node and link to Rubric
            self.query(
                """
                MATCH (r:Rubric {id: $rubric_id})
                CREATE (c:Criterion {
                    id: $crit_id,
                    name: $name,
                    description: $desc,
                    weight: $weight
                })
                CREATE (r)-[:HAS_CRITERION {order: $order}]->(c)
                WITH c
                MERGE (d:PedagogicalDimension {name: $dim})
                CREATE (c)-[:MAPS_TO]->(d)
                """,
                {
                    "rubric_id": rubric_id,
                    "crit_id": f"{rubric_id}_crit_{idx}",
                    "name": crit_name,
                    "desc": crit_desc,
                    "weight": crit_weight,
                    "order": idx,
                    "dim": dimension
                }
            )
            
            # Create Levels for this criterion
            levels = crit.get("levels", [])
            for l_idx, lvl in enumerate(levels):
                lvl_label = lvl.get("label", "")
                lvl_score = lvl.get("score", 0)
                lvl_desc = lvl.get("description", "")
                
                self.query(
                    """
                    MATCH (c:Criterion {id: $crit_id})
                    CREATE (l:Level {
                        id: $lvl_id,
                        label: $label,
                        score: $score,
                        description: $desc
                    })
                    CREATE (c)-[:HAS_LEVEL {order: $order}]->(l)
                    """,
                    {
                        "crit_id": f"{rubric_id}_crit_{idx}",
                        "lvl_id": f"{rubric_id}_crit_{idx}_lvl_{l_idx}",
                        "label": lvl_label,
                        "score": lvl_score,
                        "desc": lvl_desc,
                        "order": l_idx
                    }
                )
                
        return rubric_id

    def get_rubric(self, rubric_id: str) -> dict:
        """Retrieves a full rubric from Neo4j."""
        rubric_res = self.query("MATCH (r:Rubric {id: $id}) RETURN r", {"id": rubric_id})
        if not rubric_res:
            return None
            
        r_node = rubric_res[0]["r"]
        
        # Get criteria
        criteria_res = self.query(
            """
            MATCH (r:Rubric {id: $id})-[rel:HAS_CRITERION]->(c:Criterion)
            OPTIONAL MATCH (c)-[:MAPS_TO]->(d:PedagogicalDimension)
            RETURN c, d.name as dimension
            ORDER BY rel.order ASC
            """,
            {"id": rubric_id}
        )
        
        criteria = []
        for row in criteria_res:
            c_node = row["c"]
            dimension = row["dimension"] or "Contenidos"
            
            # Get levels for this criterion
            levels_res = self.query(
                """
                MATCH (c:Criterion {id: $crit_id})-[rel:HAS_LEVEL]->(l:Level)
                RETURN l
                ORDER BY rel.order ASC
                """,
                {"crit_id": c_node["id"]}
            )
            
            levels = [l_row["l"] for l_row in levels_res]
            
            criteria.append({
                "name": c_node["name"],
                "description": c_node["description"],
                "weight": c_node["weight"],
                "dimension": dimension,
                "levels": levels
            })
            
        return {
            "id": r_node["id"],
            "title": r_node["title"],
            "description": r_node.get("description", ""),
            "criteria": criteria
        }

    def list_rubrics(self) -> list:
        """Lists all rubrics in the database (summary mode)."""
        results = self.query("MATCH (r:Rubric) RETURN r.id as id, r.title as title, r.description as description")
        return results

    # --- Course Graphing Methods ---

    def sync_course_data(self, course_id: int, course_name: str, activities: list, resources: list):
        """Creates nodes for a Moodle Course, its activities, and its resources."""
        # 1. Merge Course
        self.query(
            "MERGE (c:Course {id: $id}) SET c.name = $name",
            {"id": course_id, "name": course_name}
        )
        
        # 2. Detach old activities and resources
        self.query(
            "MATCH (c:Course {id: $id})-[rel:HAS_ACTIVITY|HAS_RESOURCE]->(x) DETACH DELETE x",
            {"id": course_id}
        )
        
        # 3. Create Activities
        for act in activities:
            self.query(
                """
                MATCH (c:Course {id: $course_id})
                CREATE (a:Activity {
                    id: $id,
                    name: $name,
                    type: $type,
                    description: $desc,
                    duedate: $duedate
                })
                CREATE (c)-[:HAS_ACTIVITY]->(a)
                """,
                {
                    "course_id": course_id,
                    "id": f"c_{course_id}_act_{act.get('id')}",
                    "name": act.get("name", "Actividad"),
                    "type": act.get("type", "unknown"),
                    "desc": act.get("description", "") or act.get("intro", ""),
                    "duedate": act.get("duedate", 0)
                }
            )
            
        # 4. Create Resources
        for res in resources:
            self.query(
                """
                MATCH (c:Course {id: $course_id})
                CREATE (r:Resource {
                    id: $id,
                    name: $name,
                    type: $type,
                    filename: $filename
                })
                CREATE (c)-[:HAS_RESOURCE]->(r)
                """,
                {
                    "course_id": course_id,
                    "id": f"c_{course_id}_res_{res.get('id', res.get('filename'))}",
                    "name": res.get("name", res.get("filename")),
                    "type": res.get("type", "file"),
                    "filename": res.get("filename", "")
                }
            )

    # --- Ontology Export for Frontend Visualization ---

    def get_ontology_graph(self) -> dict:
        """Returns nodes and edges for visualizing the ontology/rubric space in Cytoscape/D3."""
        # Fetch all BloomLevels, PedagogicalDimensions, Rubrics, Criteria, and standard relationships
        nodes = []
        edges = []
        seen_nodes = set()
        
        # 1. Fetch BloomLevels
        bloom_res = self.query("MATCH (b:BloomLevel) RETURN b.level as name, 'bloom' as type, b.description as desc")
        # 2. Fetch Dimensions
        dim_res = self.query("MATCH (d:PedagogicalDimension) RETURN d.name as name, 'dimension' as type, d.description as desc")
        # 3. Fetch Rubrics
        rubric_res = self.query("MATCH (r:Rubric) RETURN r.id as id, r.title as name, 'rubric' as type, r.description as desc")
        # 4. Fetch Criteria
        criteria_res = self.query(
            """
            MATCH (r:Rubric)-[:HAS_CRITERION]->(c:Criterion)-[:MAPS_TO]->(d:PedagogicalDimension)
            RETURN c.id as id, c.name as name, 'criterion' as type, c.description as desc, r.id as rubric_id, d.name as dim_name
            """
        )
        
        # Add Bloom nodes
        for r in bloom_res:
            node_id = f"bloom_{r['name']}"
            nodes.append({"id": node_id, "label": r['name'], "type": "bloom", "description": r['desc']})
            
        # Add Dimension nodes
        for r in dim_res:
            node_id = f"dim_{r['name']}"
            nodes.append({"id": node_id, "label": r['name'], "type": "dimension", "description": r['desc']})
            
        # Add Rubric nodes
        for r in rubric_res:
            node_id = f"rubric_{r['id']}"
            nodes.append({"id": node_id, "label": r['name'], "type": "rubric", "description": r['desc']})
            
        # Add Criteria nodes and relationships
        for r in criteria_res:
            node_id = f"crit_{r['id']}"
            nodes.append({"id": node_id, "label": r['name'], "type": "criterion", "description": r['desc']})
            
            # Edges
            edges.append({"source": f"rubric_{r['rubric_id']}", "target": node_id, "relation": "HAS_CRITERION"})
            edges.append({"source": node_id, "target": f"dim_{r['dim_name']}", "relation": "MAPS_TO"})
            
        return {"nodes": nodes, "edges": edges}

# Instancia singleton
_neo4j_client_instance = None

def get_neo4j_client():
    global _neo4j_client_instance
    if _neo4j_client_instance is None:
        _neo4j_client_instance = Neo4jClient()
    return _neo4j_client_instance
