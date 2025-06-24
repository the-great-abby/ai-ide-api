"""
Advanced Memory Management System

This module provides intelligent memory management features including:
- Confidence scoring based on multiple factors
- Memory lifecycle management
- Relationship inference
- Automatic cleanup suggestions
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import math

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session

from db import MemoryVector, MemoryEdge, MemorySessionLocal
from memory import get_embedding_ollama, call_ollama_llm

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfidenceFactors:
    """Factors that contribute to memory confidence scoring."""
    content_length: float = 0.0
    content_quality: float = 0.0
    age_factor: float = 0.0
    relationship_strength: float = 0.0
    usage_frequency: float = 0.0
    source_reliability: float = 0.0
    tag_completeness: float = 0.0
    category_alignment: float = 0.0


@dataclass
class MemoryLifecycleStatus:
    """Status information for memory lifecycle management."""
    age_days: int
    last_accessed: Optional[datetime]
    access_count: int
    confidence_score: float
    importance_score: float
    lifecycle_stage: str  # 'active', 'aging', 'archived', 'candidate_for_cleanup'
    cleanup_reason: Optional[str] = None


class MemoryConfidenceCalculator:
    """Calculate confidence scores for memories based on multiple factors."""
    
    def __init__(self):
        self.weights = {
            'content_length': 0.15,
            'content_quality': 0.25,
            'age_factor': 0.20,
            'relationship_strength': 0.15,
            'usage_frequency': 0.10,
            'source_reliability': 0.10,
            'tag_completeness': 0.03,
            'category_alignment': 0.02
        }
    
    def calculate_confidence(self, memory: MemoryVector, db: Session) -> Tuple[float, MemoryConfidenceFactors]:
        """Calculate overall confidence score for a memory."""
        factors = MemoryConfidenceFactors()
        
        # Content length factor (0-1)
        factors.content_length = self._calculate_content_length_factor(memory.content)
        
        # Content quality factor (0-1)
        factors.content_quality = self._calculate_content_quality_factor(memory.content)
        
        # Age factor (0-1, newer is better)
        factors.age_factor = self._calculate_age_factor(memory.created_at)
        
        # Relationship strength factor (0-1)
        factors.relationship_strength = self._calculate_relationship_strength(memory.id, db)
        
        # Usage frequency factor (0-1)
        factors.usage_frequency = self._calculate_usage_frequency(memory.id, db)
        
        # Source reliability factor (0-1)
        factors.source_reliability = self._calculate_source_reliability(memory.meta)
        
        # Tag completeness factor (0-1)
        factors.tag_completeness = self._calculate_tag_completeness(memory.tags)
        
        # Category alignment factor (0-1)
        factors.category_alignment = self._calculate_category_alignment(memory.categories)
        
        # Calculate weighted average
        total_score = sum(
            getattr(factors, factor) * weight 
            for factor, weight in self.weights.items()
        )
        
        return min(1.0, max(0.0, total_score)), factors
    
    def _calculate_content_length_factor(self, content: str) -> float:
        """Calculate factor based on content length."""
        if not content:
            return 0.0
        
        # Optimal length range: 50-500 characters
        length = len(content)
        if length < 10:
            return 0.1
        elif length < 50:
            return 0.3 + (length - 10) * 0.005
        elif length <= 500:
            return 1.0
        elif length <= 1000:
            return 1.0 - (length - 500) * 0.0005
        else:
            return 0.75
    
    def _calculate_content_quality_factor(self, content: str) -> float:
        """Calculate factor based on content quality indicators."""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Check for structured content (JSON, code blocks, etc.)
        if content.strip().startswith('{') and content.strip().endswith('}'):
            try:
                json.loads(content)
                score += 0.3
            except:
                pass
        
        # Check for code-like content
        if any(keyword in content.lower() for keyword in ['def ', 'function', 'class ', 'import ', 'export ']):
            score += 0.2
        
        # Check for descriptive content
        if len(content.split()) > 10:
            score += 0.2
        
        # Check for specific details (numbers, dates, etc.)
        if any(char.isdigit() for char in content):
            score += 0.1
        
        # Check for proper formatting
        if '\n' in content or '  ' in content:
            score += 0.1
        
        # Check for action-oriented content
        action_words = ['created', 'updated', 'fixed', 'added', 'removed', 'changed', 'implemented']
        if any(word in content.lower() for word in action_words):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_age_factor(self, created_at: datetime) -> float:
        """Calculate factor based on memory age."""
        age_days = (datetime.utcnow() - created_at).days
        
        # Newer memories get higher scores
        if age_days <= 7:
            return 1.0
        elif age_days <= 30:
            return 0.9
        elif age_days <= 90:
            return 0.8
        elif age_days <= 180:
            return 0.7
        elif age_days <= 365:
            return 0.6
        else:
            return 0.5
    
    def _calculate_relationship_strength(self, memory_id: str, db: Session) -> float:
        """Calculate factor based on relationship strength."""
        # Count incoming and outgoing edges
        incoming = db.query(MemoryEdge).filter(MemoryEdge.to_id == memory_id).count()
        outgoing = db.query(MemoryEdge).filter(MemoryEdge.from_id == memory_id).count()
        
        total_relationships = incoming + outgoing
        
        if total_relationships == 0:
            return 0.3  # Base score for isolated memories
        elif total_relationships <= 3:
            return 0.5
        elif total_relationships <= 10:
            return 0.8
        else:
            return 1.0
    
    def _calculate_usage_frequency(self, memory_id: str, db: Session) -> float:
        """Calculate factor based on usage frequency (placeholder for now)."""
        # TODO: Implement usage tracking
        # For now, return a base score
        return 0.5
    
    def _calculate_source_reliability(self, meta: Optional[str]) -> float:
        """Calculate factor based on source reliability."""
        if not meta:
            return 0.5
        
        try:
            meta_data = json.loads(meta) if isinstance(meta, str) else meta
            
            # Check for reliable source indicators
            reliable_sources = ['git_history', 'code_review', 'user_story', 'rule_proposal']
            source = meta_data.get('source', '').lower()
            
            if any(reliable in source for reliable in reliable_sources):
                return 0.9
            elif 'manual' in source or 'user' in source:
                return 0.7
            else:
                return 0.5
        except:
            return 0.5
    
    def _calculate_tag_completeness(self, tags: Optional[List[str]]) -> float:
        """Calculate factor based on tag completeness."""
        if not tags:
            return 0.0
        
        # More tags generally indicate better categorization
        tag_count = len(tags)
        if tag_count == 0:
            return 0.0
        elif tag_count == 1:
            return 0.3
        elif tag_count <= 3:
            return 0.7
        elif tag_count <= 5:
            return 0.9
        else:
            return 1.0
    
    def _calculate_category_alignment(self, categories: Optional[List[str]]) -> float:
        """Calculate factor based on category alignment."""
        if not categories:
            return 0.0
        
        # Check if categories are well-defined
        category_count = len(categories)
        if category_count == 0:
            return 0.0
        elif category_count == 1:
            return 0.5
        else:
            return 0.8


class MemoryLifecycleManager:
    """Manage memory lifecycle and cleanup suggestions."""
    
    def __init__(self):
        self.confidence_calculator = MemoryConfidenceCalculator()
        self.cleanup_thresholds = {
            'low_confidence': 0.3,
            'old_age_days': 365,
            'unused_days': 90,
            'duplicate_similarity': 0.9
        }
    
    def get_lifecycle_status(self, memory: MemoryVector, db: Session) -> MemoryLifecycleStatus:
        """Get comprehensive lifecycle status for a memory."""
        confidence_score, _ = self.confidence_calculator.calculate_confidence(memory, db)
        
        age_days = (datetime.utcnow() - memory.created_at).days
        last_accessed = self._get_last_access_time(memory.id, db)
        access_count = self._get_access_count(memory.id, db)
        importance_score = self._calculate_importance_score(memory, confidence_score, age_days)
        
        lifecycle_stage = self._determine_lifecycle_stage(
            confidence_score, age_days, last_accessed, importance_score
        )
        
        cleanup_reason = self._get_cleanup_reason(
            confidence_score, age_days, last_accessed, importance_score
        )
        
        return MemoryLifecycleStatus(
            age_days=age_days,
            last_accessed=last_accessed,
            access_count=access_count,
            confidence_score=confidence_score,
            importance_score=importance_score,
            lifecycle_stage=lifecycle_stage,
            cleanup_reason=cleanup_reason
        )
    
    def get_cleanup_candidates(self, db: Session, namespace: Optional[str] = None) -> List[Tuple[MemoryVector, MemoryLifecycleStatus]]:
        """Get memories that are candidates for cleanup."""
        query = db.query(MemoryVector)
        if namespace:
            query = query.filter(MemoryVector.namespace == namespace)
        
        memories = query.all()
        candidates = []
        
        for memory in memories:
            status = self.get_lifecycle_status(memory, db)
            if status.lifecycle_stage == 'candidate_for_cleanup':
                candidates.append((memory, status))
        
        # Sort by cleanup priority (lowest importance first)
        candidates.sort(key=lambda x: x[1].importance_score)
        return candidates
    
    def _get_last_access_time(self, memory_id: str, db: Session) -> Optional[datetime]:
        """Get the last time this memory was accessed (placeholder)."""
        # TODO: Implement access tracking
        return None
    
    def _get_access_count(self, memory_id: str, db: Session) -> int:
        """Get the number of times this memory was accessed (placeholder)."""
        # TODO: Implement access tracking
        return 0
    
    def _calculate_importance_score(self, memory: MemoryVector, confidence: float, age_days: int) -> float:
        """Calculate importance score based on multiple factors."""
        # Base importance from confidence
        importance = confidence * 0.6
        
        # Age factor (older memories might be more important)
        if age_days > 365:
            importance += 0.2
        elif age_days > 90:
            importance += 0.1
        
        # Content factor
        if memory.content and len(memory.content) > 200:
            importance += 0.1
        
        # Tag factor
        if memory.tags and len(memory.tags) > 2:
            importance += 0.1
        
        return min(1.0, importance)
    
    def _determine_lifecycle_stage(self, confidence: float, age_days: int, 
                                 last_accessed: Optional[datetime], importance: float) -> str:
        """Determine the current lifecycle stage of a memory."""
        if confidence < self.cleanup_thresholds['low_confidence'] and age_days > 30:
            return 'candidate_for_cleanup'
        elif age_days > self.cleanup_thresholds['old_age_days']:
            return 'aging'
        elif last_accessed and (datetime.utcnow() - last_accessed).days > self.cleanup_thresholds['unused_days']:
            return 'aging'
        elif importance < 0.3 and age_days > 180:
            return 'candidate_for_cleanup'
        else:
            return 'active'
    
    def _get_cleanup_reason(self, confidence: float, age_days: int,
                           last_accessed: Optional[datetime], importance: float) -> Optional[str]:
        """Get the reason why a memory is a cleanup candidate."""
        if confidence < self.cleanup_thresholds['low_confidence']:
            return f"Low confidence score ({confidence:.2f})"
        elif age_days > self.cleanup_thresholds['old_age_days']:
            return f"Very old memory ({age_days} days)"
        elif last_accessed and (datetime.utcnow() - last_accessed).days > self.cleanup_thresholds['unused_days']:
            return f"Unused for {(datetime.utcnow() - last_accessed).days} days"
        elif importance < 0.3:
            return f"Low importance score ({importance:.2f})"
        return None


class MemoryRelationshipInferrer:
    """Infer relationships between memories based on content similarity."""
    
    def __init__(self):
        self.similarity_threshold = 0.7
    
    def infer_relationships(self, db: Session, namespace: Optional[str] = None, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Infer new relationships between memories based on content similarity."""
        query = db.query(MemoryVector)
        if namespace:
            query = query.filter(MemoryVector.namespace == namespace)
        
        memories = query.limit(limit).all()
        new_relationships = []
        
        for i, memory1 in enumerate(memories):
            for memory2 in memories[i+1:]:
                # Skip if relationship already exists
                existing = db.query(MemoryEdge).filter(
                    or_(
                        and_(MemoryEdge.from_id == memory1.id, MemoryEdge.to_id == memory2.id),
                        and_(MemoryEdge.from_id == memory2.id, MemoryEdge.to_id == memory1.id)
                    )
                ).first()
                
                if existing:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_content_similarity(memory1.content, memory2.content)
                
                if similarity >= self.similarity_threshold:
                    relationship_type = self._determine_relationship_type(memory1, memory2, similarity)
                    
                    new_relationships.append({
                        'from_id': memory1.id,
                        'to_id': memory2.id,
                        'relation_type': relationship_type,
                        'similarity': similarity,
                        'meta': json.dumps({
                            'inferred': True,
                            'similarity_score': similarity,
                            'inference_method': 'content_similarity'
                        })
                    })
        
        return new_relationships
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings."""
        if not content1 or not content2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _determine_relationship_type(self, memory1: MemoryVector, memory2: MemoryVector, 
                                   similarity: float) -> str:
        """Determine the type of relationship between two memories."""
        # Check for common tags
        common_tags = set(memory1.tags or []).intersection(set(memory2.tags or []))
        
        if similarity > 0.9:
            return 'duplicate'
        elif similarity > 0.8:
            return 'very_similar'
        elif similarity > 0.7:
            if common_tags:
                return 'related_by_tags'
            else:
                return 'similar_content'
        else:
            return 'weakly_related'


class MemoryManagementService:
    """Main service for advanced memory management operations."""
    
    def __init__(self):
        self.confidence_calculator = MemoryConfidenceCalculator()
        self.lifecycle_manager = MemoryLifecycleManager()
        self.relationship_inferrer = MemoryRelationshipInferrer()
    
    def update_memory_confidence(self, memory_id: str, db: Session) -> float:
        """Update confidence score for a specific memory."""
        memory = db.query(MemoryVector).filter(MemoryVector.id == memory_id).first()
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")
        
        confidence_score, factors = self.confidence_calculator.calculate_confidence(memory, db)
        
        # Update the memory with new confidence score
        memory.confidence = confidence_score
        db.commit()
        
        logger.info(f"Updated confidence for memory {memory_id}: {confidence_score:.3f}")
        return confidence_score
    
    def batch_update_confidence(self, namespace: Optional[str] = None, db: Session = None) -> Dict[str, float]:
        """Update confidence scores for all memories in a namespace."""
        if db is None:
            db = MemorySessionLocal()
        
        query = db.query(MemoryVector)
        if namespace:
            query = query.filter(MemoryVector.namespace == namespace)
        
        memories = query.all()
        results = {}
        
        for memory in memories:
            try:
                confidence = self.update_memory_confidence(memory.id, db)
                results[memory.id] = confidence
            except Exception as e:
                logger.error(f"Failed to update confidence for memory {memory.id}: {e}")
                results[memory.id] = None
        
        return results
    
    def get_cleanup_report(self, namespace: Optional[str] = None, db: Session = None) -> Dict[str, Any]:
        """Generate a comprehensive cleanup report."""
        if db is None:
            db = MemorySessionLocal()
        
        candidates = self.lifecycle_manager.get_cleanup_candidates(db, namespace)
        
        report = {
            'total_candidates': len(candidates),
            'by_reason': {},
            'by_confidence': {'low': 0, 'medium': 0, 'high': 0},
            'by_age': {'recent': 0, 'old': 0, 'very_old': 0},
            'candidates': []
        }
        
        for memory, status in candidates:
            # Categorize by reason
            reason = status.cleanup_reason or 'unknown'
            report['by_reason'][reason] = report['by_reason'].get(reason, 0) + 1
            
            # Categorize by confidence
            if status.confidence_score < 0.3:
                report['by_confidence']['low'] += 1
            elif status.confidence_score < 0.7:
                report['by_confidence']['medium'] += 1
            else:
                report['by_confidence']['high'] += 1
            
            # Categorize by age
            if status.age_days < 30:
                report['by_age']['recent'] += 1
            elif status.age_days < 180:
                report['by_age']['old'] += 1
            else:
                report['by_age']['very_old'] += 1
            
            # Add candidate details
            report['candidates'].append({
                'id': memory.id,
                'namespace': memory.namespace,
                'content_preview': memory.content[:100] + '...' if len(memory.content) > 100 else memory.content,
                'confidence_score': status.confidence_score,
                'importance_score': status.importance_score,
                'age_days': status.age_days,
                'cleanup_reason': status.cleanup_reason
            })
        
        return report
    
    def infer_new_relationships(self, namespace: Optional[str] = None, db: Session = None) -> List[Dict[str, Any]]:
        """Infer new relationships between memories."""
        if db is None:
            db = MemorySessionLocal()
        
        new_relationships = self.relationship_inferrer.infer_relationships(db, namespace)
        
        # Create the new edges
        created_edges = []
        for rel in new_relationships:
            try:
                edge = MemoryEdge(
                    from_id=rel['from_id'],
                    to_id=rel['to_id'],
                    relation_type=rel['relation_type'],
                    meta=rel['meta']
                )
                db.add(edge)
                created_edges.append(rel)
            except Exception as e:
                logger.error(f"Failed to create relationship: {e}")
        
        db.commit()
        logger.info(f"Created {len(created_edges)} new relationships")
        return created_edges


# Global instance for easy access
memory_management_service = MemoryManagementService() 