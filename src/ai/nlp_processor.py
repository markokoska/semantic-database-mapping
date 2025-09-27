
import logging
from typing import List, Dict, Any, Optional
import spacy
from spacy.matcher import Matcher
import re

from ..core.config import settings

logger = logging.getLogger(__name__)


class NLPProcessor:
    
    def __init__(self):
        self.nlp = None
        self.matcher = None
        self._initialize_nlp()
    
    def _initialize_nlp(self):
        try:
            try:
                self.nlp = spacy.load(settings.SPACY_MODEL)
            except OSError:
                logger.warning(f"spaCy model {settings.SPACY_MODEL} not found. Using basic English model.")
                self.nlp = spacy.load("en_core_web_sm")
            
            self.matcher = Matcher(self.nlp.vocab)
            self._add_semantic_patterns()
            
            logger.info("NLP processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing NLP processor: {e}")
            raise
    
    def _add_semantic_patterns(self):
        try:
            patterns = {
                "PERSON_NAME": [
                    [{"LOWER": {"IN": ["first", "given", "fname"]}}],
                    [{"LOWER": {"IN": ["last", "family", "surname", "lname"]}}, {"LOWER": "name"}],
                    [{"LOWER": "full"}, {"LOWER": "name"}],
                    [{"LOWER": {"IN": ["name", "username", "user_name"]}}]
                ],
                "CONTACT_INFO": [
                    [{"LOWER": {"IN": ["email", "e_mail", "mail"]}}],
                    [{"LOWER": {"IN": ["phone", "telephone", "tel", "mobile"]}}],
                    [{"LOWER": {"IN": ["address", "addr"]}}],
                    [{"LOWER": "contact"}, {"LOWER": {"IN": ["info", "information"]}}]
                ],
                "LOCATION": [
                    [{"LOWER": {"IN": ["city", "town", "municipality"]}}],
                    [{"LOWER": {"IN": ["state", "province", "region"]}}],
                    [{"LOWER": {"IN": ["country", "nation"]}}],
                    [{"LOWER": {"IN": ["zip", "postal"]}}], 
                    [{"LOWER": {"IN": ["latitude", "lat", "longitude", "lng", "lon"]}}]
                ],
                "TEMPORAL": [
                    [{"LOWER": {"IN": ["date", "time", "datetime", "timestamp"]}}],
                    [{"LOWER": {"IN": ["created", "updated", "modified"]}}, {"LOWER": {"IN": ["at", "on", "date", "time"]}}],
                    [{"LOWER": {"IN": ["birth", "dob"]}}, {"LOWER": "date"}]
                ],
                "IDENTIFIER": [
                    [{"LOWER": {"IN": ["id", "identifier", "key"]}}],
                    [{"LOWER": {"IN": ["uuid", "guid"]}}],
                    [{"LOWER": {"IN": ["sku", "code", "number"]}}]
                ],
                "FINANCIAL": [
                    [{"LOWER": {"IN": ["price", "cost", "amount", "fee"]}}],
                    [{"LOWER": {"IN": ["currency", "money", "payment"]}}],
                    [{"LOWER": {"IN": ["discount", "tax", "total"]}}]
                ]
            }
            
            for pattern_name, pattern_list in patterns.items():
                self.matcher.add(pattern_name, pattern_list)
            
        except Exception as e:
            logger.error(f"Error adding semantic patterns: {e}")
    
    def analyze_column_name(self, column_name: str) -> Dict[str, Any]:
        try:
            clean_name = self._clean_column_name(column_name)
            
            doc = self.nlp(clean_name)
            
            analysis = {
                "original_name": column_name,
                "clean_name": clean_name,
                "tokens": [],
                "entities": [],
                "patterns": [],
                "semantic_type": None,
                "confidence": 0.0
            }
            
            for token in doc:
                token_info = {
                    "text": token.text,
                    "lemma": token.lemma_,
                    "pos": token.pos_,
                    "tag": token.tag_,
                    "is_alpha": token.is_alpha,
                    "is_stop": token.is_stop
                }
                analysis["tokens"].append(token_info)
            
            for ent in doc.ents:
                entity_info = {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start,
                    "end": ent.end
                }
                analysis["entities"].append(entity_info)
            
            matches = self.matcher(doc)
            for match_id, start, end in matches:
                pattern_name = self.nlp.vocab.strings[match_id]
                matched_span = doc[start:end]
                
                pattern_info = {
                    "pattern": pattern_name,
                    "text": matched_span.text,
                    "start": start,
                    "end": end
                }
                analysis["patterns"].append(pattern_info)
            
            analysis["semantic_type"] = self._determine_semantic_type(analysis)
            analysis["confidence"] = self._calculate_confidence(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing column name: {e}")
            return {"error": str(e)}
    
    def _clean_column_name(self, column_name: str) -> str:
        try:
            clean_name = column_name.lower()
            
            clean_name = re.sub(r'[_-]+', ' ', clean_name)
            
            clean_name = re.sub(r'[^\w\s]', '', clean_name)
            
            clean_name = ' '.join(clean_name.split())
            
            return clean_name
            
        except Exception as e:
            logger.error(f"Error cleaning column name: {e}")
            return column_name
    
    def _determine_semantic_type(self, analysis: Dict[str, Any]) -> Optional[str]:
        try:
            pattern_priorities = {
                "IDENTIFIER": 1,
                "PERSON_NAME": 2,
                "CONTACT_INFO": 3,
                "LOCATION": 4,
                "TEMPORAL": 5,
                "FINANCIAL": 6
            }
            
            best_pattern = None
            best_priority = float('inf')
            
            for pattern_info in analysis["patterns"]:
                pattern_name = pattern_info["pattern"]
                priority = pattern_priorities.get(pattern_name, 999)
                
                if priority < best_priority:
                    best_priority = priority
                    best_pattern = pattern_name
            
            return best_pattern
            
        except Exception as e:
            logger.error(f"Error determining semantic type: {e}")
            return None
    
    def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        try:
            confidence_factors = []
            
            if analysis["patterns"]:
                confidence_factors.append(0.8)
            
            if analysis["entities"]:
                confidence_factors.append(0.6)
            
            meaningful_tokens = [
                t for t in analysis["tokens"] 
                if t["is_alpha"] and not t["is_stop"]
            ]
            if meaningful_tokens:
                token_score = len(meaningful_tokens) / len(analysis["tokens"])
                confidence_factors.append(token_score * 0.4)
            
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            else:
                return 0.3
                
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def extract_semantic_features(self, text: str) -> List[str]:
        try:
            doc = self.nlp(text.lower())
            features = []
            
            for token in doc:
                if not token.is_stop and not token.is_punct and token.is_alpha:
                    features.append(token.lemma_)
            
            for chunk in doc.noun_chunks:
                features.append(chunk.text)
            
            return list(set(features))
            
        except Exception as e:
            logger.error(f"Error extracting semantic features: {e}")
            return []
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        try:
            doc1 = self.nlp(text1)
            doc2 = self.nlp(text2)
            
            return doc1.similarity(doc2)
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0
