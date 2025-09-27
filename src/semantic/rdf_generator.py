

import logging
from typing import List, Dict, Any, Optional
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD
import pandas as pd
from pathlib import Path

from ..core.models import SchemaMapping, TableMapping, ColumnMapping, RDFTriple, SemanticGraph
from ..core.config import settings

logger = logging.getLogger(__name__)


class RDFGenerator:

    def __init__(self):
        self.graph = Graph()
        self.namespaces = self._setup_namespaces()
        self._bind_namespaces()
    
    def _setup_namespaces(self) -> Dict[str, Namespace]:
        return {
            "ex": Namespace(settings.DEFAULT_NAMESPACE),
            "schema": Namespace("https://schema.org/"),
            "dbo": Namespace("http://dbpedia.org/ontology/"),
            "dbp": Namespace("http://dbpedia.org/property/"),
            "foaf": Namespace("http://xmlns.com/foaf/0.1/"),
            "skos": Namespace("http://www.w3.org/2004/02/skos/core#"),
            "dc": Namespace("http://purl.org/dc/terms/")
        }
    
    def _bind_namespaces(self):
        for prefix, namespace in self.namespaces.items():
            self.graph.bind(prefix, namespace)
        
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)
    
    def generate_ontology(self, schema_mapping: SchemaMapping) -> Graph:
        try:
            self.graph = Graph()
            self._bind_namespaces()
            
            ontology_uri = self.namespaces["ex"]["ontology"]
            self.graph.add((ontology_uri, RDF.type, OWL.Ontology))
            self.graph.add((ontology_uri, RDFS.label, Literal(f"{schema_mapping.schema_info.name} Ontology")))
            self.graph.add((ontology_uri, RDFS.comment, Literal(f"Automatically generated ontology for {schema_mapping.schema_info.name}")))
            
            for table_mapping in schema_mapping.table_mappings:
                self._generate_table_ontology(table_mapping)
            
            logger.info(f"Generated ontology with {len(self.graph)} triples")
            return self.graph
            
        except Exception as e:
            logger.error(f"Error generating ontology: {e}")
            raise
    
    def _generate_table_ontology(self, table_mapping: TableMapping):
        try:
            if table_mapping.class_mapping:
                class_uri = self._get_uri_ref(table_mapping.class_mapping.uri)
                
                self.graph.add((class_uri, RDF.type, OWL.Class))
                self.graph.add((class_uri, RDFS.label, Literal(table_mapping.table_info.name)))
                
                if table_mapping.table_info.description:
                    self.graph.add((class_uri, RDFS.comment, Literal(table_mapping.table_info.description)))
            
            for column_mapping in table_mapping.column_mappings:
                self._generate_column_property(column_mapping, table_mapping)
                
        except Exception as e:
            logger.error(f"Error generating table ontology: {e}")
            raise
    
    def _generate_column_property(self, column_mapping: ColumnMapping, table_mapping: TableMapping):
        try:
            property_uri = self._get_uri_ref(column_mapping.selected_mapping.uri)
            
            if column_mapping.selected_mapping.type.lower() == "dataproperty":
                self.graph.add((property_uri, RDF.type, OWL.DatatypeProperty))
            else:
                self.graph.add((property_uri, RDF.type, OWL.ObjectProperty))
            
            self.graph.add((property_uri, RDFS.label, Literal(column_mapping.column_info.name)))
            
            if column_mapping.notes:
                self.graph.add((property_uri, RDFS.comment, Literal(column_mapping.notes)))
            
            if table_mapping.class_mapping:
                domain_uri = self._get_uri_ref(table_mapping.class_mapping.uri)
                self.graph.add((property_uri, RDFS.domain, domain_uri))
            
            range_uri = self._get_range_for_data_type(column_mapping.column_info.data_type.value)
            if range_uri:
                self.graph.add((property_uri, RDFS.range, range_uri))
            
        except Exception as e:
            logger.error(f"Error generating column property: {e}")
            raise
    
    def generate_data_rdf(self, schema_mapping: SchemaMapping, data_file: str) -> Graph:

        try:
            data_graph = Graph()
            
            for prefix, namespace in self.namespaces.items():
                data_graph.bind(prefix, namespace)
            
            if data_file.endswith('.csv'):
                self._generate_csv_data_rdf(data_graph, schema_mapping, data_file)
            else:
                logger.warning(f"Unsupported data file format: {data_file}")
            
            logger.info(f"Generated data RDF with {len(data_graph)} triples")
            return data_graph
            
        except Exception as e:
            logger.error(f"Error generating data RDF: {e}")
            raise
    
    def _generate_csv_data_rdf(self, data_graph: Graph, schema_mapping: SchemaMapping, csv_file: str):
        try:
            df = pd.read_csv(csv_file)
            
            for table_mapping in schema_mapping.table_mappings:
                class_uri = self._get_uri_ref(table_mapping.class_mapping.uri) if table_mapping.class_mapping else None
                
                for index, row in df.iterrows():
                    individual_uri = self.namespaces["ex"][f"{table_mapping.table_info.name}_{index}"]
                    
                    if class_uri:
                        data_graph.add((individual_uri, RDF.type, class_uri))
                    
                    for column_mapping in table_mapping.column_mappings:
                        column_name = column_mapping.column_info.name
                        
                        if column_name in row and pd.notna(row[column_name]):
                            property_uri = self._get_uri_ref(column_mapping.selected_mapping.uri)
                            value = row[column_name]
                            
                            rdf_value = self._convert_to_rdf_literal(value, column_mapping.column_info.data_type.value)
                            data_graph.add((individual_uri, property_uri, rdf_value))
            
        except Exception as e:
            logger.error(f"Error generating CSV data RDF: {e}")
            raise
    
    def _get_uri_ref(self, uri_string: str) -> URIRef:
        try:
            if uri_string.startswith("schema:"):
                return self.namespaces["schema"][uri_string[7:]]
            elif uri_string.startswith("dbo:"):
                return self.namespaces["dbo"][uri_string[4:]]
            elif uri_string.startswith("dbp:"):
                return self.namespaces["dbp"][uri_string[4:]]
            elif uri_string.startswith("http://") or uri_string.startswith("https://"):
                return URIRef(uri_string)
            else:
                return self.namespaces["ex"][uri_string]
                
        except Exception as e:
            logger.error(f"Error creating URI ref: {e}")
            return URIRef(uri_string)
    
    def _get_range_for_data_type(self, data_type: str) -> Optional[URIRef]:
        type_mapping = {
            "string": XSD.string,
            "integer": XSD.integer,
            "float": XSD.decimal,
            "boolean": XSD.boolean,
            "date": XSD.date,
            "datetime": XSD.dateTime,
            "text": XSD.string
        }
        
        return type_mapping.get(data_type)
    
    def _convert_to_rdf_literal(self, value: Any, data_type: str) -> Literal:
        try:
            if data_type == "integer":
                return Literal(int(value), datatype=XSD.integer)
            elif data_type == "float":
                return Literal(float(value), datatype=XSD.decimal)
            elif data_type == "boolean":
                return Literal(bool(value), datatype=XSD.boolean)
            elif data_type == "date":
                return Literal(str(value), datatype=XSD.date)
            elif data_type == "datetime":
                return Literal(str(value), datatype=XSD.dateTime)
            else:
                return Literal(str(value))
                
        except Exception as e:
            logger.error(f"Error converting to RDF literal: {e}")
            return Literal(str(value))
    
    def export_rdf(self, graph: Graph, output_file: str, format: str = "turtle") -> bool:

        try:
            graph.serialize(destination=output_file, format=format)
            logger.info(f"Exported RDF to {output_file} in {format} format")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting RDF: {e}")
            return False
    
    def create_semantic_graph_model(self, rdf_graph: Graph) -> SemanticGraph:
        try:
            triples = []
            ontology_classes = set()
            ontology_properties = set()
            namespaces = {}
            
            for subject, predicate, obj in rdf_graph:
                if isinstance(obj, Literal):
                    object_type = "literal"
                else:
                    object_type = "uri"
                
                triple = RDFTriple(
                    subject=str(subject),
                    predicate=str(predicate),
                    object=str(obj),
                    object_type=object_type
                )
                triples.append(triple)
                
                if predicate == RDF.type:
                    if obj == OWL.Class:
                        ontology_classes.add(str(subject))
                    elif obj in [OWL.ObjectProperty, OWL.DatatypeProperty]:
                        ontology_properties.add(str(subject))
            
            for prefix, namespace in rdf_graph.namespaces():
                namespaces[str(prefix)] = str(namespace)
            
            return SemanticGraph(
                triples=triples,
                namespaces=namespaces,
                ontology_classes=list(ontology_classes),
                ontology_properties=list(ontology_properties)
            )
            
        except Exception as e:
            logger.error(f"Error creating semantic graph model: {e}")
            raise
