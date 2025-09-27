
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .models import (
    SchemaInfo, TableInfo, ColumnInfo, SchemaMapping, TableMapping, 
    ColumnMapping, MappingJob, VocabularyTerm
)
from .schema_parser import SchemaParser
from ..ai.semantic_analyzer import SemanticAnalyzer
from ..ai.vocabulary_matcher import VocabularyMatcher
from ..semantic.rdf_generator import RDFGenerator

logger = logging.getLogger(__name__)


class MappingEngine:
    
    def __init__(self):
        self.schema_parser = SchemaParser()
        self.semantic_analyzer = SemanticAnalyzer()
        self.vocabulary_matcher = VocabularyMatcher()
        self.rdf_generator = RDFGenerator()
        self.active_jobs: Dict[str, MappingJob] = {}
    
    async def create_mapping_job(self, file_path: str) -> str:
        try:
            job_id = str(uuid.uuid4())
            
            schema_info = self.schema_parser.parse_file(file_path)
            
            job = MappingJob(
                job_id=job_id,
                schema_info=schema_info,
                status="created"
            )
            
            self.active_jobs[job_id] = job
            
            logger.info(f"Created mapping job {job_id} for file: {file_path}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating mapping job: {e}")
            raise
    
    async def process_mapping_job(self, job_id: str) -> SchemaMapping:
        try:
            if job_id not in self.active_jobs:
                raise ValueError(f"Job {job_id} not found")
            
            job = self.active_jobs[job_id]
            job.status = "processing"
            job.progress = 0.0
            
            logger.info(f"Starting processing for job {job_id}")
            
            table_mappings = []
            total_tables = len(job.schema_info.tables)
            
            for i, table in enumerate(job.schema_info.tables):
                logger.info(f"Processing table: {table.name}")
                
                table_mapping = await self._process_table(table)
                table_mappings.append(table_mapping)
                
                job.progress = (i + 1) / total_tables * 0.8
            
            schema_mapping = SchemaMapping(
                schema_info=job.schema_info,
                table_mappings=table_mappings,
                overall_confidence=self._calculate_overall_confidence(table_mappings),
                mapping_statistics=self._calculate_statistics(table_mappings)
            )
            
            job.result = schema_mapping
            job.status = "completed"
            job.progress = 1.0
            job.completed_at = datetime.now()
            
            logger.info(f"Completed processing for job {job_id}")
            return schema_mapping
            
        except Exception as e:
            logger.error(f"Error processing mapping job {job_id}: {e}")
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = "failed"
                self.active_jobs[job_id].error_message = str(e)
            raise
    
    async def _process_table(self, table: TableInfo) -> TableMapping:
        try:
            column_mappings = []
            
            tasks = []
            for column in table.columns:
                task = self._process_column(column, table)
                tasks.append(task)
            
            column_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(column_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing column {table.columns[i].name}: {result}")
                    fallback_mapping = ColumnMapping(
                        column_info=table.columns[i],
                        selected_mapping=VocabularyTerm(
                            uri=f"http://example.org/{table.columns[i].name}",
                            label=table.columns[i].name,
                            vocabulary="fallback",
                            type="Property"
                        ),
                        confidence_score=0.1,
                        alternatives=[],
                        notes=f"Error in processing: {result}"
                    )
                    column_mappings.append(fallback_mapping)
                else:
                    column_mappings.append(result)
            
            table_class = await self._infer_table_class(table, column_mappings)
            
            table_confidence = self._calculate_table_confidence(column_mappings)
            
            return TableMapping(
                table_info=table,
                class_mapping=table_class,
                column_mappings=column_mappings,
                confidence_score=table_confidence
            )
            
        except Exception as e:
            logger.error(f"Error processing table {table.name}: {e}")
            raise
    
    async def _process_column(self, column: ColumnInfo, table: TableInfo) -> ColumnMapping:
        try:
            semantic_analysis = self.semantic_analyzer.analyze_column_semantics(column, table)
            
            candidates = await self.vocabulary_matcher.find_vocabulary_matches(
                column, semantic_analysis
            )
            
            if candidates:
                best_candidate = candidates[0]
                selected_mapping = best_candidate.vocabulary_term
                confidence = best_candidate.confidence_score
                alternatives = candidates[1:5]
            else:
                selected_mapping = VocabularyTerm(
                    uri=f"http://example.org/property/{column.name}",
                    label=column.name,
                    vocabulary="fallback",
                    type="Property"
                )
                confidence = 0.2
                alternatives = []
            
            return ColumnMapping(
                column_info=column,
                selected_mapping=selected_mapping,
                confidence_score=confidence,
                alternatives=alternatives,
                notes=semantic_analysis.get("reasoning", "")
            )
            
        except Exception as e:
            logger.error(f"Error processing column {column.name}: {e}")
            raise
    
    async def _infer_table_class(self, table: TableInfo, 
                               column_mappings: List[ColumnMapping]) -> Optional[VocabularyTerm]:
        try:
            table_name_lower = table.name.lower()
            
            class_patterns = {
                "person": ["user", "customer", "person", "employee", "member", "contact"],
                "organization": ["company", "organization", "business", "institution"],
                "product": ["product", "item", "goods", "service", "catalog"],
                "event": ["event", "meeting", "appointment", "booking", "reservation"],
                "place": ["location", "place", "address", "venue"],
                "order": ["order", "purchase", "transaction", "sale"],
                "review": ["review", "comment", "feedback", "rating"]
            }
            
            for class_type, patterns in class_patterns.items():
                if any(pattern in table_name_lower for pattern in patterns):
                    return VocabularyTerm(
                        uri=f"schema:{class_type.capitalize()}",
                        label=class_type.capitalize(),
                        vocabulary="schema.org",
                        type="Class"
                    )
            
            column_types = [mapping.selected_mapping.label.lower() for mapping in column_mappings]
            
            if any("name" in col_type for col_type in column_types):
                if any("email" in col_type or "phone" in col_type for col_type in column_types):
                    return VocabularyTerm(
                        uri="schema:Person",
                        label="Person",
                        vocabulary="schema.org",
                        type="Class"
                    )
            
            return VocabularyTerm(
                uri=f"http://example.org/class/{table.name}",
                label=table.name,
                vocabulary="fallback",
                type="Class"
            )
            
        except Exception as e:
            logger.error(f"Error inferring table class: {e}")
            return None
    
    def _calculate_table_confidence(self, column_mappings: List[ColumnMapping]) -> float:
        try:
            if not column_mappings:
                return 0.0
            
            total_weight = 0
            weighted_sum = 0
            
            for mapping in column_mappings:
                weight = 1.0
                if mapping.column_info.primary_key:
                    weight = 2.0
                elif "name" in mapping.column_info.name.lower():
                    weight = 1.5
                
                weighted_sum += mapping.confidence_score * weight
                total_weight += weight
            
            return weighted_sum / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating table confidence: {e}")
            return 0.0
    
    def _calculate_overall_confidence(self, table_mappings: List[TableMapping]) -> float:
        try:
            if not table_mappings:
                return 0.0
            
            total_weight = 0
            weighted_sum = 0
            
            for table_mapping in table_mappings:
                weight = len(table_mapping.column_mappings)
                weighted_sum += table_mapping.confidence_score * weight
                total_weight += weight
            
            return weighted_sum / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating overall confidence: {e}")
            return 0.0
    
    def _calculate_statistics(self, table_mappings: List[TableMapping]) -> Dict[str, Any]:
        try:
            stats = {
                "total_tables": len(table_mappings),
                "total_columns": 0,
                "schema_org_mappings": 0,
                "dbpedia_mappings": 0,
                "fallback_mappings": 0,
                "high_confidence_mappings": 0,
                "medium_confidence_mappings": 0,
                "low_confidence_mappings": 0
            }
            
            for table_mapping in table_mappings:
                stats["total_columns"] += len(table_mapping.column_mappings)
                
                for column_mapping in table_mapping.column_mappings:
                    vocab = column_mapping.selected_mapping.vocabulary
                    if vocab == "schema.org":
                        stats["schema_org_mappings"] += 1
                    elif vocab == "dbpedia":
                        stats["dbpedia_mappings"] += 1
                    else:
                        stats["fallback_mappings"] += 1
                    
                    confidence = column_mapping.confidence_score
                    if confidence >= 0.8:
                        stats["high_confidence_mappings"] += 1
                    elif confidence >= 0.5:
                        stats["medium_confidence_mappings"] += 1
                    else:
                        stats["low_confidence_mappings"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def get_job_status(self, job_id: str) -> Optional[MappingJob]:
        return self.active_jobs.get(job_id)
    
    def list_active_jobs(self) -> List[str]:
        return list(self.active_jobs.keys())
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        try:
            current_time = datetime.now()
            jobs_to_remove = []
            
            for job_id, job in self.active_jobs.items():
                if job.status in ["completed", "failed"] and job.completed_at:
                    age = (current_time - job.completed_at).total_seconds() / 3600
                    if age > max_age_hours:
                        jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.active_jobs[job_id]
                logger.info(f"Cleaned up job {job_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up jobs: {e}")
