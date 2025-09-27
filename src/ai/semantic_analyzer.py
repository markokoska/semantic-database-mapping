
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import spacy
from transformers import pipeline

from ..core.models import ColumnInfo, TableInfo, VocabularyTerm, MappingCandidate
from ..core.config import settings

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    
    def __init__(self):
        self.sentence_transformer = None
        self.nlp = None
        self.classifier = None
        self._initialize_models()
    
    def _initialize_models(self):
        try:
            logger.info("Loading sentence transformer model...")
            self.sentence_transformer = SentenceTransformer(
                settings.SENTENCE_TRANSFORMER_MODEL,
                cache_folder=settings.TRANSFORMERS_CACHE
            )
            
            logger.info("Loading spaCy model...")
            try:
                self.nlp = spacy.load(settings.SPACY_MODEL)
            except OSError:
                logger.warning(f"spaCy model {settings.SPACY_MODEL} not found. Using basic English model.")
                self.nlp = spacy.load("en_core_web_sm")
            
            logger.info("Loading classification pipeline...")
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                cache_dir=settings.TRANSFORMERS_CACHE
            )
            
            logger.info("All AI models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
            raise
    
    def analyze_column_semantics(self, column: ColumnInfo, 
                                table_context: Optional[TableInfo] = None) -> Dict[str, Any]:
        try:
            analysis = {
                "column_name": column.name,
                "inferred_concepts": [],
                "semantic_categories": [],
                "entity_types": [],
                "confidence_score": 0.0,
                "reasoning": ""
            }
            
            name_concepts = self._analyze_column_name(column.name)
            analysis["inferred_concepts"].extend(name_concepts)
            
            if column.sample_values:
                value_concepts = self._analyze_sample_values(column.sample_values)
                analysis["inferred_concepts"].extend(value_concepts)
            
            semantic_categories = self._classify_semantic_category(column, table_context)
            analysis["semantic_categories"] = semantic_categories
            
            entity_types = self._extract_entity_types(column)
            analysis["entity_types"] = entity_types
            
            analysis["confidence_score"] = self._calculate_confidence(analysis)
            
            analysis["reasoning"] = self._generate_reasoning(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing column semantics: {e}")
            return {"error": str(e)}
    
    def _analyze_column_name(self, column_name: str) -> List[str]:
        try:
            doc = self.nlp(column_name.lower().replace("_", " ").replace("-", " "))
            
            concepts = []
            
            for token in doc:
                if not token.is_stop and not token.is_punct and len(token.text) > 2:
                    concepts.append(token.lemma_)
            
            for ent in doc.ents:
                concepts.append(ent.label_.lower())
            
            semantic_patterns = {
                "id": ["identifier", "key", "reference"],
                "name": ["label", "title", "designation"],
                "email": ["contact", "communication", "address"],
                "phone": ["contact", "communication", "telephone"],
                "address": ["location", "place", "residence"],
                "date": ["temporal", "time", "chronological"],
                "price": ["monetary", "cost", "financial"],
                "description": ["text", "narrative", "explanation"]
            }
            
            for pattern, related_concepts in semantic_patterns.items():
                if pattern in column_name.lower():
                    concepts.extend(related_concepts)
            
            return list(set(concepts))
            
        except Exception as e:
            logger.error(f"Error analyzing column name: {e}")
            return []
    
    def _analyze_sample_values(self, sample_values: List[Any]) -> List[str]:
        try:
            concepts = []
            
            for value in sample_values[:5]:
                if value is None:
                    continue
                
                value_str = str(value)
                doc = self.nlp(value_str)
                
                for ent in doc.ents:
                    concepts.append(ent.label_.lower())
                
                if "@" in value_str:
                    concepts.append("email")
                elif value_str.isdigit() and len(value_str) >= 10:
                    concepts.append("phone_number")
                elif any(word in value_str.lower() for word in ["street", "avenue", "road", "drive"]):
                    concepts.append("address")
                elif value_str.replace(".", "").replace("-", "").isdigit():
                    concepts.append("numeric_code")
            
            return list(set(concepts))
            
        except Exception as e:
            logger.error(f"Error analyzing sample values: {e}")
            return []
    
    def _classify_semantic_category(self, column: ColumnInfo, 
                                  table_context: Optional[TableInfo] = None) -> List[Dict[str, float]]:
        try:
            categories = [
                "Personal Information",
                "Contact Information", 
                "Location Information",
                "Temporal Information",
                "Financial Information",
                "Product Information",
                "Organizational Information",
                "Technical Information",
                "Descriptive Information"
            ]
            
            context_text = f"Column name: {column.name}"
            if column.sample_values:
                sample_text = ", ".join(str(v) for v in column.sample_values[:3] if v is not None)
                context_text += f". Sample values: {sample_text}"
            
            if table_context:
                context_text += f". Table: {table_context.name}"
            
            result = self.classifier(context_text, categories)
            
            classified_categories = []
            for label, score in zip(result['labels'], result['scores']):
                classified_categories.append({
                    "category": label,
                    "confidence": float(score)
                })
            
            return classified_categories[:3]
            
        except Exception as e:
            logger.error(f"Error classifying semantic category: {e}")
            return []
    
    def _extract_entity_types(self, column: ColumnInfo) -> List[str]:
        try:
            entity_types = []
            
            name_lower = column.name.lower()
            
            entity_patterns = {
                "person": ["name", "first_name", "last_name", "full_name", "author", "customer"],
                "organization": ["company", "organization", "business", "institution"],
                "place": ["city", "country", "address", "location", "place"],
                "event": ["event", "meeting", "conference", "appointment"],
                "product": ["product", "item", "goods", "service"],
                "concept": ["category", "type", "classification", "genre"]
            }
            
            for entity_type, patterns in entity_patterns.items():
                if any(pattern in name_lower for pattern in patterns):
                    entity_types.append(entity_type)
            
            if column.data_type.value in ["date", "datetime"]:
                entity_types.append("temporal_entity")
            elif column.data_type.value in ["integer", "float"] and "price" in name_lower:
                entity_types.append("monetary_value")
            
            return list(set(entity_types))
            
        except Exception as e:
            logger.error(f"Error extracting entity types: {e}")
            return []
    
    def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        try:
            confidence_factors = []
            
            if analysis.get("inferred_concepts"):
                confidence_factors.append(min(len(analysis["inferred_concepts"]) / 5, 1.0))
            
            if analysis.get("semantic_categories"):
                top_category_confidence = analysis["semantic_categories"][0].get("confidence", 0.0)
                confidence_factors.append(top_category_confidence)
            
            if analysis.get("entity_types"):
                confidence_factors.append(min(len(analysis["entity_types"]) / 3, 1.0))
            
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def _generate_reasoning(self, analysis: Dict[str, Any]) -> str:
        try:
            reasoning_parts = []
            
            if analysis.get("inferred_concepts"):
                concepts = ", ".join(analysis["inferred_concepts"][:3])
                reasoning_parts.append(f"Inferred concepts: {concepts}")
            
            if analysis.get("semantic_categories"):
                top_category = analysis["semantic_categories"][0]
                reasoning_parts.append(
                    f"Primary category: {top_category['category']} "
                    f"(confidence: {top_category['confidence']:.2f})"
                )
            
            if analysis.get("entity_types"):
                entity_types = ", ".join(analysis["entity_types"])
                reasoning_parts.append(f"Entity types: {entity_types}")
            
            return ". ".join(reasoning_parts) if reasoning_parts else "Limited semantic information available"
            
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return "Error in semantic analysis"
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        try:
            if not self.sentence_transformer:
                return 0.0
            
            embeddings = self.sentence_transformer.encode([text1, text2])
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
