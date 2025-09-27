
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import datetime


class DataType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    TEXT = "text"
    BINARY = "binary"


class ColumnInfo(BaseModel):
    name: str
    data_type: DataType
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    unique: bool = False
    default_value: Optional[Any] = None
    description: Optional[str] = None
    sample_values: List[Any] = Field(default_factory=list)
    
    
class TableInfo(BaseModel):
    name: str
    columns: List[ColumnInfo]
    row_count: Optional[int] = None
    description: Optional[str] = None
    relationships: List[str] = Field(default_factory=list)


class SchemaInfo(BaseModel):
    name: str
    tables: List[TableInfo]
    source_type: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class VocabularyTerm(BaseModel):
    uri: str
    label: str
    description: Optional[str] = None
    vocabulary: str
    type: str
    domain: Optional[str] = None
    range: Optional[str] = None


class MappingCandidate(BaseModel):
    column_name: str
    vocabulary_term: VocabularyTerm
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    semantic_similarity: float = Field(ge=0.0, le=1.0)
    context_match: float = Field(ge=0.0, le=1.0)


class ColumnMapping(BaseModel):
    column_info: ColumnInfo
    selected_mapping: VocabularyTerm
    confidence_score: float
    alternatives: List[MappingCandidate] = Field(default_factory=list)
    user_approved: bool = False
    notes: Optional[str] = None


class TableMapping(BaseModel):
    table_info: TableInfo
    class_mapping: Optional[VocabularyTerm] = None
    column_mappings: List[ColumnMapping]
    confidence_score: float
    
    
class SchemaMapping(BaseModel):
    schema_info: SchemaInfo
    table_mappings: List[TableMapping]
    overall_confidence: float
    mapping_statistics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    

class RDFTriple(BaseModel):
    subject: str
    predicate: str
    object: str
    object_type: str = "literal"


class SemanticGraph(BaseModel):
    triples: List[RDFTriple]
    namespaces: Dict[str, str] = Field(default_factory=dict)
    ontology_classes: List[str] = Field(default_factory=list)
    ontology_properties: List[str] = Field(default_factory=list)


class MappingJob(BaseModel):
    job_id: str
    schema_info: SchemaInfo
    status: str = "pending"
    progress: float = 0.0
    result: Optional[SchemaMapping] = None
    error_message: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    completed_at: Optional[datetime.datetime] = None
