
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

from ..src.core.models import SchemaMapping, ColumnMapping, TableMapping
from ..src.core.mapping_engine import MappingEngine

logger = logging.getLogger(__name__)


class MappingEvaluator:

    def __init__(self):
        self.ground_truth = {}
        self.evaluation_results = {}
    
    def load_ground_truth(self, ground_truth_file: str):
        try:
            with open(ground_truth_file, 'r') as f:
                self.ground_truth = json.load(f)
            logger.info(f"Loaded ground truth from {ground_truth_file}")
        except Exception as e:
            logger.error(f"Error loading ground truth: {e}")
    
    def evaluate_mapping_quality(self, schema_mapping: SchemaMapping, 
                                dataset_name: str = "unknown") -> Dict[str, Any]:

        try:
            evaluation = {
                "dataset": dataset_name,
                "timestamp": datetime.now().isoformat(),
                "overall_metrics": {},
                "table_metrics": [],
                "column_metrics": [],
                "vocabulary_distribution": {},
                "confidence_analysis": {}
            }
            
            evaluation["overall_metrics"] = self._calculate_overall_metrics(schema_mapping)
            
            for table_mapping in schema_mapping.table_mappings:
                table_metrics = self._evaluate_table_mapping(table_mapping)
                evaluation["table_metrics"].append(table_metrics)
            
            all_column_mappings = []
            for table_mapping in schema_mapping.table_mappings:
                all_column_mappings.extend(table_mapping.column_mappings)
            
            for col_mapping in all_column_mappings:
                col_metrics = self._evaluate_column_mapping(col_mapping)
                evaluation["column_metrics"].append(col_metrics)
            
            evaluation["vocabulary_distribution"] = self._analyze_vocabulary_distribution(all_column_mappings)
            
            evaluation["confidence_analysis"] = self._analyze_confidence_distribution(all_column_mappings)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating mapping quality: {e}")
            return {"error": str(e)}
    
    def _calculate_overall_metrics(self, schema_mapping: SchemaMapping) -> Dict[str, float]:
        """Calculate overall quality metrics"""
        try:
            metrics = {}
            
            total_tables = len(schema_mapping.table_mappings)
            total_columns = sum(len(tm.column_mappings) for tm in schema_mapping.table_mappings)
            
            all_confidences = []
            for table_mapping in schema_mapping.table_mappings:
                for col_mapping in table_mapping.column_mappings:
                    all_confidences.append(col_mapping.confidence_score)
            
            if all_confidences:
                metrics.update({
                    "total_tables": total_tables,
                    "total_columns": total_columns,
                    "average_confidence": np.mean(all_confidences),
                    "median_confidence": np.median(all_confidences),
                    "min_confidence": np.min(all_confidences),
                    "max_confidence": np.max(all_confidences),
                    "confidence_std": np.std(all_confidences)
                })
            
            high_confidence = sum(1 for c in all_confidences if c >= 0.8)
            medium_confidence = sum(1 for c in all_confidences if 0.5 <= c < 0.8)
            low_confidence = sum(1 for c in all_confidences if c < 0.5)
            
            metrics.update({
                "high_confidence_ratio": high_confidence / total_columns if total_columns > 0 else 0,
                "medium_confidence_ratio": medium_confidence / total_columns if total_columns > 0 else 0,
                "low_confidence_ratio": low_confidence / total_columns if total_columns > 0 else 0
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating overall metrics: {e}")
            return {}
    
    def _evaluate_table_mapping(self, table_mapping: TableMapping) -> Dict[str, Any]:
        """Evaluate a single table mapping"""
        try:
            metrics = {
                "table_name": table_mapping.table_info.name,
                "class_mapping": table_mapping.class_mapping.uri if table_mapping.class_mapping else None,
                "column_count": len(table_mapping.column_mappings),
                "table_confidence": table_mapping.confidence_score
            }
            
            col_confidences = [cm.confidence_score for cm in table_mapping.column_mappings]
            if col_confidences:
                metrics.update({
                    "avg_column_confidence": np.mean(col_confidences),
                    "min_column_confidence": np.min(col_confidences),
                    "max_column_confidence": np.max(col_confidences)
                })
            
            vocabularies = [cm.selected_mapping.vocabulary for cm in table_mapping.column_mappings]
            vocab_counts = {}
            for vocab in vocabularies:
                vocab_counts[vocab] = vocab_counts.get(vocab, 0) + 1
            
            metrics["vocabulary_usage"] = vocab_counts
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating table mapping: {e}")
            return {"error": str(e)}
    
    def _evaluate_column_mapping(self, col_mapping: ColumnMapping) -> Dict[str, Any]:
        """Evaluate a single column mapping"""
        try:
            metrics = {
                "column_name": col_mapping.column_info.name,
                "data_type": col_mapping.column_info.data_type.value,
                "mapped_uri": col_mapping.selected_mapping.uri,
                "vocabulary": col_mapping.selected_mapping.vocabulary,
                "confidence": col_mapping.confidence_score,
                "alternatives_count": len(col_mapping.alternatives),
                "is_nullable": col_mapping.column_info.nullable,
                "is_primary_key": col_mapping.column_info.primary_key,
                "has_foreign_key": col_mapping.column_info.foreign_key is not None
            }
            
            # Semantic analysis
            metrics["semantic_category"] = self._infer_semantic_category(col_mapping)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating column mapping: {e}")
            return {"error": str(e)}
    
    def _infer_semantic_category(self, col_mapping: ColumnMapping) -> str:
        """Infer semantic category from mapping"""
        try:
            uri = col_mapping.selected_mapping.uri.lower()
            name = col_mapping.column_info.name.lower()
            
            if any(term in uri or term in name for term in ["name", "label", "title"]):
                return "naming"
            elif any(term in uri or term in name for term in ["email", "phone", "contact"]):
                return "contact"
            elif any(term in uri or term in name for term in ["address", "city", "country"]):
                return "location"
            elif any(term in uri or term in name for term in ["date", "time", "created", "updated"]):
                return "temporal"
            elif any(term in uri or term in name for term in ["price", "cost", "amount"]):
                return "financial"
            elif any(term in uri or term in name for term in ["id", "key", "identifier"]):
                return "identifier"
            else:
                return "other"
                
        except Exception as e:
            logger.error(f"Error inferring semantic category: {e}")
            return "unknown"
    
    def _analyze_vocabulary_distribution(self, column_mappings: List[ColumnMapping]) -> Dict[str, Any]:
        """Analyze the distribution of vocabularies used"""
        try:
            vocab_counts = {}
            vocab_confidences = {}
            
            for col_mapping in column_mappings:
                vocab = col_mapping.selected_mapping.vocabulary
                confidence = col_mapping.confidence_score
                
                vocab_counts[vocab] = vocab_counts.get(vocab, 0) + 1
                
                if vocab not in vocab_confidences:
                    vocab_confidences[vocab] = []
                vocab_confidences[vocab].append(confidence)
            
            vocab_stats = {}
            for vocab, confidences in vocab_confidences.items():
                vocab_stats[vocab] = {
                    "count": vocab_counts[vocab],
                    "percentage": vocab_counts[vocab] / len(column_mappings) * 100,
                    "avg_confidence": np.mean(confidences),
                    "min_confidence": np.min(confidences),
                    "max_confidence": np.max(confidences)
                }
            
            return vocab_stats
            
        except Exception as e:
            logger.error(f"Error analyzing vocabulary distribution: {e}")
            return {}
    
    def _analyze_confidence_distribution(self, column_mappings: List[ColumnMapping]) -> Dict[str, Any]:
        """Analyze the distribution of confidence scores"""
        try:
            confidences = [cm.confidence_score for cm in column_mappings]
            
            if not confidences:
                return {}
            
            bins = [0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0]
            bin_labels = ["very_low", "low", "medium", "good", "high", "very_high"]
            
            hist, _ = np.histogram(confidences, bins=bins)
            
            distribution = {}
            for i, label in enumerate(bin_labels):
                distribution[label] = {
                    "count": int(hist[i]),
                    "percentage": float(hist[i] / len(confidences) * 100)
                }
            
            return {
                "distribution": distribution,
                "statistics": {
                    "mean": float(np.mean(confidences)),
                    "median": float(np.median(confidences)),
                    "std": float(np.std(confidences)),
                    "q25": float(np.percentile(confidences, 25)),
                    "q75": float(np.percentile(confidences, 75))
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing confidence distribution: {e}")
            return {}
    
    def benchmark_performance(self, test_files: List[str], num_runs: int = 3) -> Dict[str, Any]:

        try:
            mapping_engine = MappingEngine()
            
            benchmark_results = {
                "test_files": test_files,
                "num_runs": num_runs,
                "results": [],
                "summary": {}
            }
            
            all_times = []
            all_accuracies = []
            
            for test_file in test_files:
                if not Path(test_file).exists():
                    logger.warning(f"Test file not found: {test_file}")
                    continue
                
                file_results = {
                    "file": test_file,
                    "runs": [],
                    "avg_time": 0.0,
                    "avg_accuracy": 0.0
                }
                
                for run in range(num_runs):
                    start_time = time.time()
                    
                    job_id = await mapping_engine.create_mapping_job(test_file)
                    schema_mapping = await mapping_engine.process_mapping_job(job_id)
                    
                    processing_time = time.time() - start_time
                    
                    accuracy = schema_mapping.overall_confidence
                    
                    run_result = {
                        "run": run + 1,
                        "processing_time": processing_time,
                        "accuracy": accuracy,
                        "total_columns": sum(len(tm.column_mappings) for tm in schema_mapping.table_mappings)
                    }
                    
                    file_results["runs"].append(run_result)
                    all_times.append(processing_time)
                    all_accuracies.append(accuracy)
                
                file_results["avg_time"] = np.mean([r["processing_time"] for r in file_results["runs"]])
                file_results["avg_accuracy"] = np.mean([r["accuracy"] for r in file_results["runs"]])
                
                benchmark_results["results"].append(file_results)
            
            if all_times:
                benchmark_results["summary"] = {
                    "avg_processing_time": np.mean(all_times),
                    "min_processing_time": np.min(all_times),
                    "max_processing_time": np.max(all_times),
                    "avg_accuracy": np.mean(all_accuracies),
                    "min_accuracy": np.min(all_accuracies),
                    "max_accuracy": np.max(all_accuracies),
                    "total_files_processed": len([r for r in benchmark_results["results"] if r["runs"]])
                }
            
            return benchmark_results
            
        except Exception as e:
            logger.error(f"Error benchmarking performance: {e}")
            return {"error": str(e)}
    
    def generate_evaluation_report(self, evaluation_results: Dict[str, Any], 
                                 output_file: str = None) -> str:

        try:
            report_lines = []
            
            report_lines.append("=" * 60)
            report_lines.append("SEMANTIC MAPPING EVALUATION REPORT")
            report_lines.append("=" * 60)
            report_lines.append(f"Dataset: {evaluation_results.get('dataset', 'Unknown')}")
            report_lines.append(f"Timestamp: {evaluation_results.get('timestamp', 'Unknown')}")
            report_lines.append("")
            
            overall = evaluation_results.get("overall_metrics", {})
            if overall:
                report_lines.append("OVERALL METRICS")
                report_lines.append("-" * 20)
                report_lines.append(f"Total Tables: {overall.get('total_tables', 'N/A')}")
                report_lines.append(f"Total Columns: {overall.get('total_columns', 'N/A')}")
                report_lines.append(f"Average Confidence: {overall.get('average_confidence', 0):.3f}")
                report_lines.append(f"Median Confidence: {overall.get('median_confidence', 0):.3f}")
                report_lines.append(f"Confidence Range: {overall.get('min_confidence', 0):.3f} - {overall.get('max_confidence', 0):.3f}")
                report_lines.append("")
                
                report_lines.append("QUALITY DISTRIBUTION")
                report_lines.append("-" * 20)
                report_lines.append(f"High Confidence (≥0.8): {overall.get('high_confidence_ratio', 0)*100:.1f}%")
                report_lines.append(f"Medium Confidence (0.5-0.8): {overall.get('medium_confidence_ratio', 0)*100:.1f}%")
                report_lines.append(f"Low Confidence (<0.5): {overall.get('low_confidence_ratio', 0)*100:.1f}%")
                report_lines.append("")
            
            vocab_dist = evaluation_results.get("vocabulary_distribution", {})
            if vocab_dist:
                report_lines.append("VOCABULARY USAGE")
                report_lines.append("-" * 20)
                for vocab, stats in vocab_dist.items():
                    report_lines.append(f"{vocab}:")
                    report_lines.append(f"  Count: {stats.get('count', 0)}")
                    report_lines.append(f"  Percentage: {stats.get('percentage', 0):.1f}%")
                    report_lines.append(f"  Avg Confidence: {stats.get('avg_confidence', 0):.3f}")
                report_lines.append("")
            
            table_metrics = evaluation_results.get("table_metrics", [])
            if table_metrics:
                report_lines.append("TABLE ANALYSIS")
                report_lines.append("-" * 20)
                for table in table_metrics:
                    report_lines.append(f"Table: {table.get('table_name', 'Unknown')}")
                    report_lines.append(f"  Class: {table.get('class_mapping', 'None')}")
                    report_lines.append(f"  Columns: {table.get('column_count', 0)}")
                    report_lines.append(f"  Confidence: {table.get('table_confidence', 0):.3f}")
                    report_lines.append("")
            
            report_lines.append("=" * 60)
            
            report = "\n".join(report_lines)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(report)
                logger.info(f"Evaluation report saved to {output_file}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating evaluation report: {e}")
            return f"Error generating report: {e}"
    
    def export_results(self, results: Dict[str, Any], output_file: str):
        """Export evaluation results to JSON file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results exported to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
