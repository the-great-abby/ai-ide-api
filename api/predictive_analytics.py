"""
Predictive Analytics Engine for AI-IDE API.
Part of Phase 4: Predictive Analytics implementation.
"""

import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Result of a predictive analysis."""
    predictions: List[Dict[str, Any]]
    confidence: float
    factors: List[str]
    recommendations: List[str]
    risk_level: str  # "low", "medium", "high", "critical"
    timestamp: str

@dataclass
class CodeMetrics:
    """Metrics extracted from code analysis."""
    complexity: float
    lines_of_code: int
    function_count: int
    class_count: int
    import_count: int
    comment_ratio: float
    test_coverage: Optional[float] = None
    bug_history: List[str] = field(default_factory=list)
    performance_issues: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)

@dataclass
class ProjectPatterns:
    """Patterns identified in the project."""
    common_bugs: List[str]
    performance_patterns: List[str]
    security_patterns: List[str]
    code_smells: List[str]
    refactoring_opportunities: List[str]

class PredictiveAnalyticsEngine:
    """Advanced predictive analytics engine for code analysis."""
    
    def __init__(self):
        self.bug_patterns = self._load_bug_patterns()
        self.performance_patterns = self._load_performance_patterns()
        self.security_patterns = self._load_security_patterns()
        self.code_smell_patterns = self._load_code_smell_patterns()
        self.historical_data = defaultdict(list)
        self.prediction_models = {}
        
    def _load_bug_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns that commonly lead to bugs."""
        return {
            "null_pointer": {
                "patterns": [
                    r"\.\w+\s*\([^)]*\)",  # Method calls without null checks
                    r"if\s+[^:]+:\s*\n\s*[^#\n]*\n\s*else:\s*\n\s*pass",  # Empty else blocks
                ],
                "risk_score": 0.8,
                "description": "Potential null pointer exceptions",
                "fix": "Add null checks before method calls"
            },
            "resource_leak": {
                "patterns": [
                    r"open\s*\([^)]+\)",  # File opens without context managers
                    r"try:\s*\n\s*[^\n]+\s*\nexcept[^:]*:\s*\n\s*pass",  # Silent exceptions
                ],
                "risk_score": 0.7,
                "description": "Potential resource leaks",
                "fix": "Use context managers or ensure proper cleanup"
            },
            "race_condition": {
                "patterns": [
                    r"global\s+\w+",  # Global variables in concurrent code
                    r"threading\.",  # Threading without proper synchronization
                ],
                "risk_score": 0.9,
                "description": "Potential race conditions",
                "fix": "Use proper synchronization mechanisms"
            },
            "memory_leak": {
                "patterns": [
                    r"while\s+True:",  # Infinite loops
                    r"\.append\s*\([^)]*\)\s*#\s*no\s*limit",  # Unbounded appends
                ],
                "risk_score": 0.6,
                "description": "Potential memory leaks",
                "fix": "Add bounds checking and cleanup"
            }
        }
    
    def _load_performance_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns that indicate performance issues."""
        return {
            "nested_loops": {
                "patterns": [
                    r"for\s+[^:]+:\s*\n\s*for\s+[^:]+:",  # Nested for loops
                    r"while\s+[^:]+:\s*\n\s*while\s+[^:]+:",  # Nested while loops
                ],
                "risk_score": 0.7,
                "description": "Nested loops can cause O(n²) complexity",
                "fix": "Consider using more efficient algorithms or data structures"
            },
            "inefficient_search": {
                "patterns": [
                    r"if\s+\w+\s+in\s+\[[^\]]+\]",  # List membership checks
                    r"\.index\s*\([^)]*\)",  # List index searches
                ],
                "risk_score": 0.6,
                "description": "Inefficient search operations",
                "fix": "Use sets or dictionaries for O(1) lookups"
            },
            "redundant_computation": {
                "patterns": [
                    r"len\s*\([^)]+\)\s*>\s*0\s*and\s*len\s*\([^)]+\)",  # Multiple len() calls
                    r"\.split\s*\([^)]*\)\s*\[[^\]]+\]\s*\.split",  # Chained splits
                ],
                "risk_score": 0.5,
                "description": "Redundant computations",
                "fix": "Cache results of expensive operations"
            },
            "large_data_structures": {
                "patterns": [
                    r"\[\s*\]\s*\*\s*\d+",  # Large list multiplication
                    r"range\s*\(\d{4,}\)",  # Large ranges
                ],
                "risk_score": 0.8,
                "description": "Large data structures in memory",
                "fix": "Use generators or streaming for large datasets"
            }
        }
    
    def _load_security_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns that indicate security vulnerabilities."""
        return {
            "sql_injection": {
                "patterns": [
                    r"f\"[^\"]*SELECT[^\"]*\{[^}]*\}",  # F-string SQL with variables
                    r"execute\s*\(\s*f\"[^\"]*\{[^}]*\}",  # SQL execution with f-strings
                ],
                "risk_score": 0.9,
                "description": "Potential SQL injection",
                "fix": "Use parameterized queries"
            },
            "command_injection": {
                "patterns": [
                    r"os\.system\s*\(\s*[^)]*\+\s*[^)]*\)",  # os.system with concatenation
                    r"subprocess\.run\s*\(\s*[^)]*\+\s*[^)]*\)",  # subprocess with concatenation
                ],
                "risk_score": 0.9,
                "description": "Potential command injection",
                "fix": "Use subprocess with argument lists"
            },
            "path_traversal": {
                "patterns": [
                    r"open\s*\(\s*[^)]*\+\s*[^)]*\)",  # File open with concatenation
                    r"\.read\s*\(\s*[^)]*\+\s*[^)]*\)",  # File read with concatenation
                ],
                "risk_score": 0.8,
                "description": "Potential path traversal",
                "fix": "Validate and sanitize file paths"
            },
            "hardcoded_secrets": {
                "patterns": [
                    r"password\s*=\s*['\"][^'\"]+['\"]",  # Hardcoded passwords
                    r"api_key\s*=\s*['\"][^'\"]+['\"]",  # Hardcoded API keys
                    r"secret\s*=\s*['\"][^'\"]+['\"]",  # Hardcoded secrets
                ],
                "risk_score": 0.7,
                "description": "Hardcoded secrets",
                "fix": "Use environment variables or secure secret management"
            }
        }
    
    def _load_code_smell_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns that indicate code smells."""
        return {
            "long_function": {
                "patterns": [
                    r"def\s+\w+[^:]*:\s*(?:\n\s*[^\n]*){50,}",  # Functions with 50+ lines
                ],
                "risk_score": 0.6,
                "description": "Long functions are hard to maintain",
                "fix": "Break down into smaller, focused functions"
            },
            "duplicate_code": {
                "patterns": [
                    r"(\w+\([^)]*\)[^;]*;?\s*){3,}",  # Repeated function calls
                ],
                "risk_score": 0.5,
                "description": "Duplicate code indicates refactoring opportunity",
                "fix": "Extract common functionality into reusable functions"
            },
            "magic_numbers": {
                "patterns": [
                    r"\b\d{3,}\b",  # Numbers >= 100 without context
                ],
                "risk_score": 0.4,
                "description": "Magic numbers make code hard to understand",
                "fix": "Define constants with meaningful names"
            },
            "deep_nesting": {
                "patterns": [
                    r"if[^:]*:\s*\n\s*if[^:]*:\s*\n\s*if[^:]*:",  # Deeply nested if statements
                ],
                "risk_score": 0.7,
                "description": "Deep nesting makes code hard to follow",
                "fix": "Use early returns or extract conditions"
            }
        }
    
    async def analyze_code_predictively(self, code: str, context: Dict[str, Any]) -> PredictionResult:
        """Perform comprehensive predictive analysis on code."""
        predictions = []
        factors = []
        recommendations = []
        
        try:
            # Extract code metrics
            metrics = self._extract_code_metrics(code)
            
            # Analyze for different types of issues
            bug_predictions = await self._predict_bugs(code, metrics, context)
            performance_predictions = await self._predict_performance_issues(code, metrics, context)
            security_predictions = await self._predict_security_issues(code, metrics, context)
            code_smell_predictions = await self._predict_code_smells(code, metrics, context)
            
            # Combine all predictions
            predictions.extend(bug_predictions)
            predictions.extend(performance_predictions)
            predictions.extend(security_predictions)
            predictions.extend(code_smell_predictions)
            
            # Generate factors and recommendations
            factors = self._generate_factors(metrics, predictions)
            recommendations = self._generate_recommendations(predictions, context)
            
            # Calculate overall confidence and risk level
            confidence = self._calculate_confidence(predictions)
            risk_level = self._calculate_risk_level(predictions)
            
            return PredictionResult(
                predictions=predictions,
                confidence=confidence,
                factors=factors,
                recommendations=recommendations,
                risk_level=risk_level,
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error in predictive analysis: {e}")
            return PredictionResult(
                predictions=[{
                    "type": "analysis_error",
                    "message": f"Predictive analysis failed: {str(e)}",
                    "severity": "error"
                }],
                confidence=0.0,
                factors=["Analysis failed"],
                recommendations=["Fix analysis engine"],
                risk_level="unknown",
                timestamp=datetime.utcnow().isoformat()
            )
    
    def _extract_code_metrics(self, code: str) -> CodeMetrics:
        """Extract metrics from code for analysis."""
        lines = code.split('\n')
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # Count functions and classes
        function_count = len(re.findall(r'def\s+\w+', code))
        class_count = len(re.findall(r'class\s+\w+', code))
        import_count = len(re.findall(r'import\s+|from\s+', code))
        
        # Calculate comment ratio
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        comment_ratio = comment_lines / max(lines_of_code, 1)
        
        # Calculate complexity (simplified)
        complexity = self._calculate_complexity(code)
        
        return CodeMetrics(
            complexity=complexity,
            lines_of_code=lines_of_code,
            function_count=function_count,
            class_count=class_count,
            import_count=import_count,
            comment_ratio=comment_ratio
        )
    
    def _calculate_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        # Count decision points
        complexity += len(re.findall(r'\bif\b', code))
        complexity += len(re.findall(r'\bfor\b', code))
        complexity += len(re.findall(r'\bwhile\b', code))
        complexity += len(re.findall(r'\band\b', code))
        complexity += len(re.findall(r'\bor\b', code))
        complexity += len(re.findall(r'\bexcept\b', code))
        
        return complexity
    
    async def _predict_bugs(self, code: str, metrics: CodeMetrics, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict potential bugs in the code."""
        predictions = []
        
        for bug_type, pattern_info in self.bug_patterns.items():
            for pattern in pattern_info["patterns"]:
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    line_number = code[:match.start()].count('\n') + 1
                    predictions.append({
                        "type": "bug_prediction",
                        "category": bug_type,
                        "message": pattern_info["description"],
                        "confidence": pattern_info["risk_score"],
                        "line": line_number,
                        "column": match.start() - code.rfind('\n', 0, match.start()) - 1,
                        "fix": pattern_info["fix"],
                        "matched_text": match.group(),
                        "severity": "high" if pattern_info["risk_score"] > 0.8 else "medium"
                    })
        
        # Additional bug predictions based on metrics
        if metrics.complexity > 10:
            predictions.append({
                "type": "bug_prediction",
                "category": "high_complexity",
                "message": f"High complexity ({metrics.complexity}) increases bug risk",
                "confidence": 0.7,
                "line": 1,
                "column": 1,
                "fix": "Break down complex functions into smaller, simpler ones",
                "severity": "medium"
            })
        
        if metrics.lines_of_code > 100 and metrics.function_count == 0:
            predictions.append({
                "type": "bug_prediction",
                "category": "monolithic_code",
                "message": "Large code block without functions increases maintenance risk",
                "confidence": 0.6,
                "line": 1,
                "column": 1,
                "fix": "Extract functionality into well-defined functions",
                "severity": "medium"
            })
        
        return predictions
    
    async def _predict_performance_issues(self, code: str, metrics: CodeMetrics, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict performance issues in the code."""
        predictions = []
        
        for perf_type, pattern_info in self.performance_patterns.items():
            for pattern in pattern_info["patterns"]:
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    line_number = code[:match.start()].count('\n') + 1
                    predictions.append({
                        "type": "performance_prediction",
                        "category": perf_type,
                        "message": pattern_info["description"],
                        "confidence": pattern_info["risk_score"],
                        "line": line_number,
                        "column": match.start() - code.rfind('\n', 0, match.start()) - 1,
                        "fix": pattern_info["fix"],
                        "matched_text": match.group(),
                        "severity": "medium"
                    })
        
        # Additional performance predictions based on metrics
        if metrics.complexity > 15:
            predictions.append({
                "type": "performance_prediction",
                "category": "high_complexity",
                "message": f"High complexity ({metrics.complexity}) may cause performance issues",
                "confidence": 0.6,
                "line": 1,
                "column": 1,
                "fix": "Optimize algorithms and reduce complexity",
                "severity": "medium"
            })
        
        return predictions
    
    async def _predict_security_issues(self, code: str, metrics: CodeMetrics, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict security vulnerabilities in the code."""
        predictions = []
        
        for sec_type, pattern_info in self.security_patterns.items():
            for pattern in pattern_info["patterns"]:
                matches = re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    line_number = code[:match.start()].count('\n') + 1
                    predictions.append({
                        "type": "security_prediction",
                        "category": sec_type,
                        "message": pattern_info["description"],
                        "confidence": pattern_info["risk_score"],
                        "line": line_number,
                        "column": match.start() - code.rfind('\n', 0, match.start()) - 1,
                        "fix": pattern_info["fix"],
                        "matched_text": match.group(),
                        "severity": "high" if pattern_info["risk_score"] > 0.8 else "medium"
                    })
        
        return predictions
    
    async def _predict_code_smells(self, code: str, metrics: CodeMetrics, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict code smells and maintenance issues."""
        predictions = []
        
        for smell_type, pattern_info in self.code_smell_patterns.items():
            for pattern in pattern_info["patterns"]:
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    line_number = code[:match.start()].count('\n') + 1
                    predictions.append({
                        "type": "code_smell_prediction",
                        "category": smell_type,
                        "message": pattern_info["description"],
                        "confidence": pattern_info["risk_score"],
                        "line": line_number,
                        "column": match.start() - code.rfind('\n', 0, match.start()) - 1,
                        "fix": pattern_info["fix"],
                        "matched_text": match.group(),
                        "severity": "low"
                    })
        
        # Additional code smell predictions based on metrics
        if metrics.comment_ratio < 0.1:
            predictions.append({
                "type": "code_smell_prediction",
                "category": "low_documentation",
                "message": "Low comment ratio may indicate poor documentation",
                "confidence": 0.5,
                "line": 1,
                "column": 1,
                "fix": "Add meaningful comments to complex logic",
                "severity": "low"
            })
        
        return predictions
    
    def _generate_factors(self, metrics: CodeMetrics, predictions: List[Dict[str, Any]]) -> List[str]:
        """Generate factors that influenced the predictions."""
        factors = []
        
        if metrics.complexity > 10:
            factors.append(f"High complexity ({metrics.complexity})")
        
        if metrics.lines_of_code > 100:
            factors.append(f"Large code size ({metrics.lines_of_code} lines)")
        
        if metrics.function_count == 0 and metrics.lines_of_code > 50:
            factors.append("Monolithic code structure")
        
        if metrics.comment_ratio < 0.1:
            factors.append("Low documentation")
        
        # Count prediction types
        prediction_types = Counter(pred["type"] for pred in predictions)
        for pred_type, count in prediction_types.items():
            factors.append(f"{count} {pred_type.replace('_', ' ')}")
        
        return factors
    
    def _generate_recommendations(self, predictions: List[Dict[str, Any]], context: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on predictions."""
        recommendations = []
        
        # Group predictions by category
        categories = defaultdict(list)
        for pred in predictions:
            categories[pred.get("category", "unknown")].append(pred)
        
        # Generate recommendations for each category
        for category, preds in categories.items():
            if category == "null_pointer":
                recommendations.append("Add comprehensive null checks throughout the codebase")
            elif category == "resource_leak":
                recommendations.append("Use context managers for all resource management")
            elif category == "nested_loops":
                recommendations.append("Consider refactoring nested loops for better performance")
            elif category == "sql_injection":
                recommendations.append("Implement parameterized queries for all database operations")
            elif category == "high_complexity":
                recommendations.append("Break down complex functions into smaller, focused functions")
            elif category == "duplicate_code":
                recommendations.append("Extract common functionality into reusable utilities")
        
        # Add general recommendations
        if len(predictions) > 5:
            recommendations.append("Consider implementing comprehensive code review practices")
        
        if any(pred.get("severity") == "high" for pred in predictions):
            recommendations.append("Prioritize fixing high-severity issues immediately")
        
        return recommendations
    
    def _calculate_confidence(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in predictions."""
        if not predictions:
            return 0.0
        
        # Weight by confidence and severity
        total_weight = 0
        weighted_sum = 0
        
        for pred in predictions:
            confidence = pred.get("confidence", 0.5)
            severity = pred.get("severity", "medium")
            
            # Weight by severity
            if severity == "high":
                weight = 1.0
            elif severity == "medium":
                weight = 0.7
            else:
                weight = 0.4
            
            weighted_sum += confidence * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _calculate_risk_level(self, predictions: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level based on predictions."""
        if not predictions:
            return "low"
        
        # Count high-severity predictions
        high_severity = sum(1 for pred in predictions if pred.get("severity") == "high")
        medium_severity = sum(1 for pred in predictions if pred.get("severity") == "medium")
        
        if high_severity >= 3:
            return "critical"
        elif high_severity >= 1 or medium_severity >= 5:
            return "high"
        elif medium_severity >= 2 or len(predictions) >= 5:
            return "medium"
        else:
            return "low"

# Global analytics engine instance
analytics_engine = PredictiveAnalyticsEngine()

async def predict_code_issues(code: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for predictive code analysis."""
    result = await analytics_engine.analyze_code_predictively(code, context)
    
    # Convert to dict for JSON serialization
    return {
        "predictions": result.predictions,
        "confidence": result.confidence,
        "factors": result.factors,
        "recommendations": result.recommendations,
        "risk_level": result.risk_level,
        "timestamp": result.timestamp
    } 