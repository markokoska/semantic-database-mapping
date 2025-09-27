

import logging
from typing import List, Dict, Any, Optional
from SPARQLWrapper import SPARQLWrapper, JSON, XML, TURTLE
from rdflib import Graph
import json

from ..core.config import settings

logger = logging.getLogger(__name__)


class SPARQLInterface:
    def __init__(self, endpoint_url: Optional[str] = None):
        self.endpoint_url = endpoint_url or settings.DBPEDIA_ENDPOINT
        self.sparql = SPARQLWrapper(self.endpoint_url)
        self.local_graph = None
    
    def set_local_graph(self, graph: Graph):
        self.local_graph = graph
    
    def query_remote(self, query: str, return_format: str = "json") -> Dict[str, Any]:

        try:
            self.sparql.setQuery(query)
            
            if return_format.lower() == "json":
                self.sparql.setReturnFormat(JSON)
            elif return_format.lower() == "xml":
                self.sparql.setReturnFormat(XML)
            elif return_format.lower() == "turtle":
                self.sparql.setReturnFormat(TURTLE)
            
            results = self.sparql.query().convert()
            
            logger.info(f"SPARQL query executed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error executing SPARQL query: {e}")
            raise
    
    def query_local(self, query: str) -> List[Dict[str, Any]]:
        try:
            if not self.local_graph:
                raise ValueError("No local graph set. Use set_local_graph() first.")
            
            results = self.local_graph.query(query)
            
            result_list = []
            for row in results:
                row_dict = {}
                for i, var in enumerate(results.vars):
                    row_dict[str(var)] = str(row[i]) if row[i] else None
                result_list.append(row_dict)
            
            logger.info(f"Local SPARQL query executed, {len(result_list)} results")
            return result_list
            
        except Exception as e:
            logger.error(f"Error executing local SPARQL query: {e}")
            raise
    
    def find_dbpedia_resources(self, search_term: str, limit: int = 10) -> List[Dict[str, str]]:
        try:
            query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dbo: <http://dbpedia.org/ontology/>
            
            SELECT DISTINCT ?resource ?label ?comment WHERE {{
                ?resource rdfs:label ?label .
                OPTIONAL {{ ?resource rdfs:comment ?comment }}
                FILTER(LANG(?label) = "en")
                FILTER(CONTAINS(LCASE(?label), LCASE("{search_term}")))
            }}
            LIMIT {limit}
            """
            
            self.dbpedia_wrapper.setQuery(query)
            self.dbpedia_wrapper.setReturnFormat(JSON)
            results = self.dbpedia_wrapper.query().convert()
            
            resources = []
            for result in results["results"]["bindings"]:
                resource = {
                    "uri": result["resource"]["value"],
                    "label": result["label"]["value"],
                    "comment": result.get("comment", {}).get("value", "")
                }
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            logger.error(f"Error querying DBpedia: {e}")
            return []