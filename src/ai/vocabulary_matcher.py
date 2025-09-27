
import requests
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import aiohttp
from urllib.parse import quote

from ..core.models import VocabularyTerm, MappingCandidate, ColumnInfo
from ..core.config import settings
from .semantic_analyzer import SemanticAnalyzer

logger = logging.getLogger(__name__)


class VocabularyMatcher:
    
    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        self.schema_org_cache = {}
        self.dbpedia_cache = {}
        self._load_schema_org_vocabulary()
    
    def _load_schema_org_vocabulary(self):
        try:
            self.schema_org_terms = {
                "name": "schema:name",
                "first_name": "schema:givenName",
                "last_name": "schema:familyName",
                "email": "schema:email",
                "phone": "schema:telephone",
                "address": "schema:address",
                "birthdate": "schema:birthDate",
                
                "company": "schema:Organization",
                "organization": "schema:Organization",
                "website": "schema:url",
                
                "city": "schema:addressLocality",
                "state": "schema:addressRegion",
                "country": "schema:addressCountry",
                "postal_code": "schema:postalCode",
                "latitude": "schema:latitude",
                "longitude": "schema:longitude",
                
                "product": "schema:Product",
                "price": "schema:price",
                "description": "schema:description",
                "category": "schema:category",
                "brand": "schema:brand",
                
                "date": "schema:date",
                "created_at": "schema:dateCreated",
                "updated_at": "schema:dateModified",
                
                "id": "schema:identifier",
                "uuid": "schema:identifier",
                "sku": "schema:sku",
                
                "title": "schema:headline",
                "content": "schema:text",
                "image": "schema:image",
                "url": "schema:url"
            }
            
            logger.info("Schema.org vocabulary loaded")
            
        except Exception as e:
            logger.error(f"Error loading Schema.org vocabulary: {e}")
    
    async def find_vocabulary_matches(self, column: ColumnInfo, 
                                    semantic_analysis: Dict[str, Any]) -> List[MappingCandidate]:
        try:
            candidates = []
            
            schema_candidates = await self._search_schema_org(column, semantic_analysis)
            candidates.extend(schema_candidates)
            
            dbpedia_candidates = await self._search_dbpedia(column, semantic_analysis)
            candidates.extend(dbpedia_candidates)
            
            candidates = self._rank_candidates(candidates, column, semantic_analysis)
            
            return candidates[:10]
            
        except Exception as e:
            logger.error(f"Error finding vocabulary matches: {e}")
            return []
    
    async def _search_schema_org(self, column: ColumnInfo, 
                               semantic_analysis: Dict[str, Any]) -> List[MappingCandidate]:
        try:
            candidates = []
            column_name_lower = column.name.lower()
            
            if column_name_lower in self.schema_org_terms:
                term_uri = self.schema_org_terms[column_name_lower]
                
                vocab_term = VocabularyTerm(
                    uri=term_uri,
                    label=column_name_lower,
                    vocabulary="schema.org",
                    type="Property"
                )
                
                candidate = MappingCandidate(
                    column_name=column.name,
                    vocabulary_term=vocab_term,
                    confidence_score=0.9,
                    semantic_similarity=0.95,
                    context_match=0.85,
                    reasoning="Direct name match with Schema.org vocabulary"
                )
                candidates.append(candidate)
            
            if semantic_analysis.get("inferred_concepts"):
                for concept in semantic_analysis["inferred_concepts"]:
                    concept_lower = concept.lower()
                    if concept_lower in self.schema_org_terms:
                        term_uri = self.schema_org_terms[concept_lower]
                        
                        vocab_term = VocabularyTerm(
                            uri=term_uri,
                            label=concept_lower,
                            vocabulary="schema.org",
                            type="Property"
                        )
                        
                        similarity = self.semantic_analyzer.calculate_semantic_similarity(
                            column.name, concept
                        )
                        
                        candidate = MappingCandidate(
                            column_name=column.name,
                            vocabulary_term=vocab_term,
                            confidence_score=0.7 + similarity * 0.2,
                            semantic_similarity=similarity,
                            context_match=0.7,
                            reasoning=f"Semantic concept match: {concept}"
                        )
                        candidates.append(candidate)
            
            if semantic_analysis.get("semantic_categories"):
                top_category = semantic_analysis["semantic_categories"][0]
                category_mappings = self._get_category_schema_mappings(top_category["category"])
                
                for mapping in category_mappings:
                    vocab_term = VocabularyTerm(
                        uri=mapping["uri"],
                        label=mapping["label"],
                        vocabulary="schema.org",
                        type=mapping["type"]
                    )
                    
                    candidate = MappingCandidate(
                        column_name=column.name,
                        vocabulary_term=vocab_term,
                        confidence_score=top_category["confidence"] * 0.6,
                        semantic_similarity=0.6,
                        context_match=top_category["confidence"],
                        reasoning=f"Category-based match: {top_category['category']}"
                    )
                    candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error searching Schema.org: {e}")
            return []
    
    async def _search_dbpedia(self, column: ColumnInfo, 
                            semantic_analysis: Dict[str, Any]) -> List[MappingCandidate]:
        try:
            candidates = []
            
            search_queries = [column.name]
            if semantic_analysis.get("inferred_concepts"):
                search_queries.extend(semantic_analysis["inferred_concepts"][:3])
            
            async with aiohttp.ClientSession() as session:
                for query in search_queries:
                    dbpedia_results = await self._query_dbpedia_lookup(session, query)
                    
                    for result in dbpedia_results[:5]:
                        vocab_term = VocabularyTerm(
                            uri=result["uri"],
                            label=result["label"],
                            description=result.get("description", ""),
                            vocabulary="dbpedia",
                            type=result.get("type", "Resource")
                        )
                        
                        similarity = self.semantic_analyzer.calculate_semantic_similarity(
                            column.name, result["label"]
                        )
                        
                        candidate = MappingCandidate(
                            column_name=column.name,
                            vocabulary_term=vocab_term,
                            confidence_score=similarity * 0.8,
                            semantic_similarity=similarity,
                            context_match=0.6,
                            reasoning=f"DBpedia lookup match for: {query}"
                        )
                        candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error searching DBpedia: {e}")
            return []
    
    async def _query_dbpedia_lookup(self, session: aiohttp.ClientSession, 
                                  query: str) -> List[Dict[str, Any]]:
        try:
            url = f"{settings.DBPEDIA_LOOKUP_URL}.json"
            params = {
                "query": query,
                "format": "json",
                "maxResults": 10
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    if "results" in data:
                        for item in data["results"]:
                            result = {
                                "uri": item.get("uri", ""),
                                "label": item.get("label", ""),
                                "description": item.get("description", ""),
                                "type": item.get("classes", [{}])[0].get("label", "Resource") if item.get("classes") else "Resource"
                            }
                            results.append(result)
                    
                    return results
                else:
                    logger.warning(f"DBpedia lookup failed with status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error querying DBpedia lookup: {e}")
            return []
    
    def _get_category_schema_mappings(self, category: str) -> List[Dict[str, str]]:
        category_mappings = {
            "Personal Information": [
                {"uri": "schema:Person", "label": "Person", "type": "Class"},
                {"uri": "schema:givenName", "label": "givenName", "type": "Property"},
                {"uri": "schema:familyName", "label": "familyName", "type": "Property"}
            ],
            "Contact Information": [
                {"uri": "schema:ContactPoint", "label": "ContactPoint", "type": "Class"},
                {"uri": "schema:email", "label": "email", "type": "Property"},
                {"uri": "schema:telephone", "label": "telephone", "type": "Property"}
            ],
            "Location Information": [
                {"uri": "schema:Place", "label": "Place", "type": "Class"},
                {"uri": "schema:PostalAddress", "label": "PostalAddress", "type": "Class"},
                {"uri": "schema:addressLocality", "label": "addressLocality", "type": "Property"}
            ],
            "Temporal Information": [
                {"uri": "schema:DateTime", "label": "DateTime", "type": "DataType"},
                {"uri": "schema:Date", "label": "Date", "type": "DataType"},
                {"uri": "schema:dateCreated", "label": "dateCreated", "type": "Property"}
            ],
            "Financial Information": [
                {"uri": "schema:MonetaryAmount", "label": "MonetaryAmount", "type": "Class"},
                {"uri": "schema:price", "label": "price", "type": "Property"},
                {"uri": "schema:priceCurrency", "label": "priceCurrency", "type": "Property"}
            ],
            "Product Information": [
                {"uri": "schema:Product", "label": "Product", "type": "Class"},
                {"uri": "schema:name", "label": "name", "type": "Property"},
                {"uri": "schema:description", "label": "description", "type": "Property"}
            ]
        }
        
        return category_mappings.get(category, [])
    
    def _rank_candidates(self, candidates: List[MappingCandidate], 
                        column: ColumnInfo, semantic_analysis: Dict[str, Any]) -> List[MappingCandidate]:
        try:
            unique_candidates = {}
            for candidate in candidates:
                uri = candidate.vocabulary_term.uri
                if uri not in unique_candidates or candidate.confidence_score > unique_candidates[uri].confidence_score:
                    unique_candidates[uri] = candidate
            
            candidates = list(unique_candidates.values())
            
            for candidate in candidates:
                if candidate.vocabulary_term.vocabulary == "schema.org":
                    candidate.confidence_score *= 1.1
                
                if candidate.vocabulary_term.label.lower() == column.name.lower():
                    candidate.confidence_score *= 1.2
                
                if self._is_data_type_compatible(column, candidate.vocabulary_term):
                    candidate.confidence_score *= 1.05
                
                candidate.confidence_score = min(candidate.confidence_score, 1.0)
            
            candidates.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error ranking candidates: {e}")
            return candidates
    
    def _is_data_type_compatible(self, column: ColumnInfo, vocab_term: VocabularyTerm) -> bool:
        try:
            if column.data_type.value in ["date", "datetime"] and "date" in vocab_term.label.lower():
                return True
            elif column.data_type.value in ["integer", "float"] and any(
                word in vocab_term.label.lower() for word in ["price", "amount", "number", "count"]
            ):
                return True
            elif column.data_type.value == "string" and "name" in vocab_term.label.lower():
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking data type compatibility: {e}")
            return True
