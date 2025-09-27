

import logging
from typing import List, Dict, Any, Optional, Set
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
from owlready2 import get_ontology, Thing, ObjectProperty, DataProperty, FunctionalProperty
import tempfile
import os

from ..core.models import SchemaMapping, VocabularyTerm
from ..core.config import settings

logger = logging.getLogger(__name__)


class OntologyManager:
    
    def __init__(self):
        self.ontology = None
        self.graph = Graph()
        self.namespaces = self._setup_namespaces()
        self._bind_namespaces()
    
    def _setup_namespaces(self) -> Dict[str, Namespace]:
        return {
            "ex": Namespace(settings.DEFAULT_NAMESPACE),
            "schema": Namespace("https://schema.org/"),
            "dbo": Namespace("http://dbpedia.org/ontology/"),
            "foaf": Namespace("http://xmlns.com/foaf/0.1/"),
            "skos": Namespace("http://www.w3.org/2004/02/skos/core#")
        }
    
    def _bind_namespaces(self):
        for prefix, namespace in self.namespaces.items():
            self.graph.bind(prefix, namespace)
        
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
    
    def create_ontology_from_mapping(self, schema_mapping: SchemaMapping) -> Graph:
        try:
            self.graph = Graph()
            self._bind_namespaces()
            
            ontology_uri = self.namespaces["ex"][""]
            self.graph.add((ontology_uri, RDF.type, OWL.Ontology))
            self.graph.add((ontology_uri, RDFS.label, 
                          Literal(f"{schema_mapping.schema_info.name} Ontology")))
            self.graph.add((ontology_uri, RDFS.comment, 
                          Literal("Automatically generated ontology from database schema")))
            
            for table_mapping in schema_mapping.table_mappings:
                self._create_class_definition(table_mapping)
                self._create_property_definitions(table_mapping)
                self._add_constraints(table_mapping)
            
            self._add_relationships(schema_mapping)
            
            logger.info(f"Created ontology with {len(self.graph)} triples")
            return self.graph
            
        except Exception as e:
            logger.error(f"Error creating ontology: {e}")
            raise
    
    def _create_class_definition(self, table_mapping):
        try:
            if not table_mapping.class_mapping:
                return
            
            class_uri = self._get_uri_ref(table_mapping.class_mapping.uri)
            
            self.graph.add((class_uri, RDF.type, OWL.Class))
            self.graph.add((class_uri, RDFS.label, Literal(table_mapping.table_info.name)))
            
            if table_mapping.table_info.description:
                self.graph.add((class_uri, RDFS.comment, Literal(table_mapping.table_info.description)))
            
            if table_mapping.class_mapping.vocabulary == "schema.org":
                superclass_mappings = {
                    "Person": "schema:Person",
                    "Organization": "schema:Organization", 
                    "Product": "schema:Product",
                    "Place": "schema:Place",
                    "Event": "schema:Event"
                }
                
                for pattern, superclass in superclass_mappings.items():
                    if pattern.lower() in table_mapping.table_info.name.lower():
                        superclass_uri = self._get_uri_ref(superclass)
                        self.graph.add((class_uri, RDFS.subClassOf, superclass_uri))
                        break
            
        except Exception as e:
            logger.error(f"Error creating class definition: {e}")
    
    def _create_property_definitions(self, table_mapping):
        try:
            for column_mapping in table_mapping.column_mappings:
                property_uri = self._get_uri_ref(column_mapping.selected_mapping.uri)
                
                if self._is_object_property(column_mapping):
                    self.graph.add((property_uri, RDF.type, OWL.ObjectProperty))
                else:
                    self.graph.add((property_uri, RDF.type, OWL.DatatypeProperty))
                
                self.graph.add((property_uri, RDFS.label, Literal(column_mapping.column_info.name)))
                
                if column_mapping.notes:
                    self.graph.add((property_uri, RDFS.comment, Literal(column_mapping.notes)))
                
                if table_mapping.class_mapping:
                    domain_uri = self._get_uri_ref(table_mapping.class_mapping.uri)
                    self.graph.add((property_uri, RDFS.domain, domain_uri))
                
                range_uri = self._get_property_range(column_mapping)
                if range_uri:
                    self.graph.add((property_uri, RDFS.range, range_uri))
                
                if column_mapping.column_info.unique or column_mapping.column_info.primary_key:
                    self.graph.add((property_uri, RDF.type, OWL.FunctionalProperty))
                
        except Exception as e:
            logger.error(f"Error creating property definitions: {e}")
    
    def _add_constraints(self, table_mapping):
        try:
            if not table_mapping.class_mapping:
                return
            
            class_uri = self._get_uri_ref(table_mapping.class_mapping.uri)
            
            required_properties = [
                mapping for mapping in table_mapping.column_mappings 
                if not mapping.column_info.nullable
            ]
            
            for prop_mapping in required_properties:
                property_uri = self._get_uri_ref(prop_mapping.selected_mapping.uri)
                
                restriction_node = self.graph.value(predicate=RDF.type, object=OWL.Restriction, any=False)
                if not restriction_node:
                    restriction_node = self.namespaces["ex"][f"restriction_{len(list(self.graph.subjects()))}"]
                
                self.graph.add((restriction_node, RDF.type, OWL.Restriction))
                self.graph.add((restriction_node, OWL.onProperty, property_uri))
                self.graph.add((restriction_node, OWL.minCardinality, Literal(1)))
                self.graph.add((class_uri, RDFS.subClassOf, restriction_node))
            
        except Exception as e:
            logger.error(f"Error adding constraints: {e}")
    
    def _add_relationships(self, schema_mapping: SchemaMapping):
        try:
            for table_mapping in schema_mapping.table_mappings:
                for column_mapping in table_mapping.column_mappings:
                    if column_mapping.column_info.foreign_key:
                        fk_info = column_mapping.column_info.foreign_key
                        
                        property_uri = self.namespaces["ex"][f"relatedTo{fk_info}"]
                        self.graph.add((property_uri, RDF.type, OWL.ObjectProperty))
                        self.graph.add((property_uri, RDFS.label, Literal(f"related to {fk_info}")))
                        
                        if table_mapping.class_mapping:
                            domain_uri = self._get_uri_ref(table_mapping.class_mapping.uri)
                            self.graph.add((property_uri, RDFS.domain, domain_uri))
            
        except Exception as e:
            logger.error(f"Error adding relationships: {e}")
    
    def _is_object_property(self, column_mapping) -> bool:
        try:
            column = column_mapping.column_info
            
            if column.foreign_key:
                return True
            
            reference_patterns = ["_id", "_ref", "_key", "reference"]
            column_name_lower = column.name.lower()
            
            if any(pattern in column_name_lower for pattern in reference_patterns):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining property type: {e}")
            return False
    
    def _get_property_range(self, column_mapping) -> Optional[URIRef]:
        try:
            data_type = column_mapping.column_info.data_type.value
            
            from rdflib.namespace import XSD
            
            type_mappings = {
                "string": XSD.string,
                "integer": XSD.integer,
                "float": XSD.decimal,
                "boolean": XSD.boolean,
                "date": XSD.date,
                "datetime": XSD.dateTime,
                "text": XSD.string
            }
            
            return type_mappings.get(data_type)
            
        except Exception as e:
            logger.error(f"Error getting property range: {e}")
            return None
    
    def _get_uri_ref(self, uri_string: str) -> URIRef:
        try:
            if uri_string.startswith("schema:"):
                return self.namespaces["schema"][uri_string[7:]]
            elif uri_string.startswith("dbo:"):
                return self.namespaces["dbo"][uri_string[4:]]
            elif uri_string.startswith("http://") or uri_string.startswith("https://"):
                return URIRef(uri_string)
            else:
                return self.namespaces["ex"][uri_string]
        except Exception as e:
            logger.error(f"Error creating URI ref: {e}")
            return URIRef(uri_string)
    
    def validate_ontology(self) -> Dict[str, Any]:
        try:
            validation_results = {
                "is_valid": True,
                "warnings": [],
                "errors": [],
                "statistics": {}
            }
            
            classes = list(self.graph.subjects(RDF.type, OWL.Class))
            properties = list(self.graph.subjects(RDF.type, OWL.ObjectProperty)) + \
                        list(self.graph.subjects(RDF.type, OWL.DatatypeProperty))
            
            validation_results["statistics"] = {
                "total_triples": len(self.graph),
                "classes": len(classes),
                "properties": len(properties)
            }
            
            for class_uri in classes:
                if not list(self.graph.objects(class_uri, RDFS.label)):
                    validation_results["warnings"].append(f"Class {class_uri} has no label")
            
            for prop_uri in properties:
                if not list(self.graph.objects(prop_uri, RDFS.domain)):
                    validation_results["warnings"].append(f"Property {prop_uri} has no domain")
                if not list(self.graph.objects(prop_uri, RDFS.range)):
                    validation_results["warnings"].append(f"Property {prop_uri} has no range")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating ontology: {e}")
            return {"is_valid": False, "errors": [str(e)]}
    
    def export_ontology(self, output_file: str, format: str = "turtle") -> bool:
        try:
            self.graph.serialize(destination=output_file, format=format)
            logger.info(f"Exported ontology to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting ontology: {e}")
            return False
    
    def load_external_ontology(self, ontology_url: str) -> bool:
        try:
            external_graph = Graph()
            external_graph.parse(ontology_url)
            
            self.graph += external_graph
            
            logger.info(f"Loaded external ontology from {ontology_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading external ontology: {e}")
            return False
    
    def find_similar_concepts(self, concept_uri: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        try:
            similar_concepts = []
            
            concept_labels = list(self.graph.objects(URIRef(concept_uri), RDFS.label))
            if not concept_labels:
                return similar_concepts
            
            concept_label = str(concept_labels[0])
            
            all_concepts = list(self.graph.subjects(RDF.type, OWL.Class))
            
            for other_concept in all_concepts:
                if str(other_concept) == concept_uri:
                    continue
                
                other_labels = list(self.graph.objects(other_concept, RDFS.label))
                if other_labels:
                    other_label = str(other_labels[0])
                    
                    similarity = self._calculate_string_similarity(concept_label, other_label)
                    
                    if similarity >= threshold:
                        similar_concepts.append({
                            "uri": str(other_concept),
                            "label": other_label,
                            "similarity": similarity
                        })
            
            similar_concepts.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similar_concepts
            
        except Exception as e:
            logger.error(f"Error finding similar concepts: {e}")
            return []
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        try:
            words1 = set(str1.lower().split())
            words2 = set(str2.lower().split())
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if not union:
                return 0.0
            
            return len(intersection) / len(union)
            
        except Exception as e:
            logger.error(f"Error calculating string similarity: {e}")
            return 0.0
