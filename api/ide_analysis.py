"""
Real-time code analysis engine for IDE integration.
Part of Phase 2: Real-Time IDE Integration implementation.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from misc_endpoints import analyze_python_code

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Result of code analysis."""
    suggestions: List[Dict[str, Any]]
    predictions: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    timestamp: str
    confidence: float = 0.0

@dataclass
class CodeContext:
    """Context information for code analysis."""
    language: str
    file_path: str
    line_number: int
    column: int
    project_name: Optional[str] = None
    namespace: Optional[str] = None
    framework: Optional[str] = None
    recent_changes: Optional[List[str]] = None

class RealTimeCodeAnalyzer:
    """Real-time code analysis engine for IDE integration."""
    
    def __init__(self):
        self.memory_manager = None  # Will be initialized when needed
        self.rule_patterns = self._load_rule_patterns()
        self.code_patterns = self._load_code_patterns()
        self.security_patterns = self._load_security_patterns()
    
    def _load_rule_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load common rule violation patterns."""
        return {
            "python": [
                {
                    "pattern": r"print\s*\(",
                    "rule_type": "no_print_statements",
                    "message": "Use logger instead of print statements",
                    "severity": "warning",
                    "fix": "Replace print() with logger.debug() or logger.info()",
                    "reason": "Project rule requires structured logging"
                },
                {
                    "pattern": r"import \*",
                    "rule_type": "no_wildcard_imports",
                    "message": "Avoid wildcard imports",
                    "severity": "warning",
                    "fix": "Import specific modules instead of using *",
                    "reason": "Wildcard imports can cause namespace pollution"
                },
                {
                    "pattern": r"except:",
                    "rule_type": "bare_except",
                    "message": "Avoid bare except clauses",
                    "severity": "error",
                    "fix": "Specify exception types to catch",
                    "reason": "Bare except can mask unexpected errors"
                },
                {
                    "pattern": r"def \w+\([^)]*\):\s*\n\s*pass",
                    "rule_type": "empty_function",
                    "message": "Empty function detected",
                    "severity": "info",
                    "fix": "Add implementation or remove function",
                    "reason": "Empty functions indicate incomplete implementation"
                }
            ],
            "javascript": [
                {
                    "pattern": r"console\.log\s*\(",
                    "rule_type": "no_console_log",
                    "message": "Use proper logging instead of console.log",
                    "severity": "warning",
                    "fix": "Replace console.log() with structured logging",
                    "reason": "Project rule requires structured logging"
                },
                {
                    "pattern": r"var\s+\w+",
                    "rule_type": "no_var",
                    "message": "Use const or let instead of var",
                    "severity": "warning",
                    "fix": "Replace var with const or let",
                    "reason": "var has function scope, prefer block scope"
                },
                {
                    "pattern": r"==\s*[^=]",
                    "rule_type": "loose_equality",
                    "message": "Use strict equality (===) instead of loose equality",
                    "severity": "warning",
                    "fix": "Replace == with === for strict comparison",
                    "reason": "Loose equality can cause unexpected type coercion"
                }
            ]
        }
    
    def _load_code_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load common code patterns for suggestions."""
        return {
            "python": [
                {
                    "pattern": r"if\s+[^:]+:\s*\n\s*return\s+True",
                    "pattern_type": "simplified_boolean",
                    "message": "Consider simplifying boolean return",
                    "suggestion": "Return the condition directly instead of if/return True",
                    "example": "return condition  # instead of if condition: return True"
                },
                {
                    "pattern": r"for\s+\w+\s+in\s+range\(len\([^)]+\)\)",
                    "pattern_type": "enumerate_pattern",
                    "message": "Consider using enumerate for index and value",
                    "suggestion": "Use enumerate() to get both index and value",
                    "example": "for i, item in enumerate(items):"
                },
                {
                    "pattern": r"try:\s*\n\s*[^\n]+\s*\nexcept\s+Exception\s+as\s+e:\s*\n\s*pass",
                    "pattern_type": "silent_exception",
                    "message": "Silent exception handling detected",
                    "suggestion": "Log or handle the exception properly",
                    "example": "except Exception as e: logger.error(f'Error: {e}')"
                }
            ],
            "javascript": [
                {
                    "pattern": r"if\s*\([^)]+\)\s*{\s*return\s+true\s*}",
                    "pattern_type": "simplified_boolean",
                    "message": "Consider simplifying boolean return",
                    "suggestion": "Return the condition directly",
                    "example": "return condition;  // instead of if (condition) return true;"
                },
                {
                    "pattern": r"for\s*\(\s*let\s*i\s*=\s*0;\s*i\s*<\s*[^;]+\.length;\s*i\+\+\)",
                    "pattern_type": "for_of_pattern",
                    "message": "Consider using for...of for array iteration",
                    "suggestion": "Use for...of for cleaner array iteration",
                    "example": "for (const item of items) {"
                }
            ]
        }
    
    def _load_security_patterns(self) -> List[Dict[str, Any]]:
        """Load security-related patterns for alerts."""
        return [
            {
                "pattern": r"password\s*=\s*['\"][^'\"]+['\"]",
                "alert_type": "hardcoded_credentials",
                "message": "Hardcoded credentials detected",
                "severity": "high",
                "fix": "Use environment variables or secure credential management"
            },
            {
                "pattern": r"eval\s*\(",
                "alert_type": "eval_usage",
                "message": "eval() usage detected - security risk",
                "severity": "high",
                "fix": "Avoid eval() - use safer alternatives"
            },
            {
                "pattern": r"exec\s*\(",
                "alert_type": "exec_usage",
                "message": "exec() usage detected - security risk",
                "severity": "high",
                "fix": "Avoid exec() - use safer alternatives"
            },
            {
                "pattern": r"sql\s*=\s*f?['\"].*WHERE.*\{[^}]*\}",
                "alert_type": "sql_injection_risk",
                "message": "Potential SQL injection risk",
                "severity": "high",
                "fix": "Use parameterized queries or ORM"
            }
        ]
    
    async def analyze_code_context(self, code: str, context: CodeContext) -> AnalysisResult:
        """Analyze code in real-time and provide suggestions."""
        suggestions = []
        predictions = []
        alerts = []
        
        try:
            # 1. Check against project rules
            rule_violations = await self._check_rule_violations(code, context)
            suggestions.extend(rule_violations)
            
            # 2. Find relevant patterns
            pattern_suggestions = await self._find_relevant_patterns(code, context)
            suggestions.extend(pattern_suggestions)
            
            # 3. Query memory system for similar code
            memory_suggestions = await self._query_memory_system(code, context)
            suggestions.extend(memory_suggestions)
            
            # 4. Check for security issues
            security_alerts = await self._check_security_issues(code, context)
            alerts.extend(security_alerts)
            
            # 5. Generate predictions
            predictions = await self._generate_predictions(code, context)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(suggestions, predictions, alerts)
            
            return AnalysisResult(
                suggestions=suggestions,
                predictions=predictions,
                alerts=alerts,
                timestamp=datetime.utcnow().isoformat(),
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error in code analysis: {e}")
            return AnalysisResult(
                suggestions=[{
                    "type": "analysis_error",
                    "message": f"Analysis failed: {str(e)}",
                    "severity": "error"
                }],
                predictions=[],
                alerts=[],
                timestamp=datetime.utcnow().isoformat(),
                confidence=0.0
            )
    
    async def _check_rule_violations(self, code: str, context: CodeContext) -> List[Dict[str, Any]]:
        """Check code against project rules and common patterns."""
        violations = []
        
        # Get language-specific patterns
        patterns = self.rule_patterns.get(context.language, [])
        
        # Check each pattern
        for pattern_info in patterns:
            matches = re.finditer(pattern_info["pattern"], code, re.MULTILINE)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                violations.append({
                    "type": "rule_violation",
                    "rule_type": pattern_info["rule_type"],
                    "message": pattern_info["message"],
                    "severity": pattern_info["severity"],
                    "line": line_number,
                    "column": match.start() - code.rfind('\n', 0, match.start()) - 1,
                    "fix": pattern_info["fix"],
                    "reason": pattern_info["reason"],
                    "matched_text": match.group()
                })
        
        # Use existing Python analysis for more detailed checks
        if context.language == "python":
            try:
                python_suggestions = analyze_python_code(code)
                for suggestion in python_suggestions:
                    violations.append({
                        "type": "rule_violation",
                        "rule_type": suggestion.get("rule_type", "python_analysis"),
                        "message": suggestion.get("description", "Python code analysis suggestion"),
                        "severity": "warning",
                        "line": 1,  # Will be refined with better line detection
                        "column": 1,
                        "fix": suggestion.get("diff", ""),
                        "reason": "Python code analysis",
                        "matched_text": ""
                    })
            except Exception as e:
                logger.warning(f"Python analysis failed: {e}")
        
        return violations
    
    async def _find_relevant_patterns(self, code: str, context: CodeContext) -> List[Dict[str, Any]]:
        """Find relevant code patterns for suggestions."""
        patterns = []
        
        # Get language-specific patterns
        code_patterns = self.code_patterns.get(context.language, [])
        
        # Check each pattern
        for pattern_info in code_patterns:
            matches = re.finditer(pattern_info["pattern"], code, re.MULTILINE)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                patterns.append({
                    "type": "pattern_suggestion",
                    "pattern_type": pattern_info["pattern_type"],
                    "message": pattern_info["message"],
                    "severity": "info",
                    "line": line_number,
                    "column": match.start() - code.rfind('\n', 0, match.start()) - 1,
                    "suggestion": pattern_info["suggestion"],
                    "example": pattern_info["example"],
                    "matched_text": match.group()
                })
        
        return patterns
    
    async def _query_memory_system(self, code: str, context: CodeContext) -> List[Dict[str, Any]]:
        """Query memory system for similar code and patterns."""
        suggestions = []
        
        # Skip memory query if memory manager is not available
        if self.memory_manager is None:
            return suggestions
        
        try:
            # For now, return empty suggestions since memory manager is not fully integrated
            # TODO: Implement proper memory search when memory manager is available
            logger.debug("Memory system query skipped - memory manager not fully integrated")
        
        except Exception as e:
            logger.warning(f"Memory query failed: {e}")
        
        return suggestions
    
    def _is_memory_relevant(self, memory: Dict[str, Any], code: str, context: CodeContext) -> bool:
        """Check if a memory is relevant to the current code."""
        # Check similarity score
        similarity = memory.get("similarity_score", 0.0)
        if similarity < 0.7:  # Only consider high similarity
            return False
        
        # Check if memory is related to current language/framework
        memory_tags = memory.get("tags", [])
        if context.language and context.language not in memory_tags:
            return False
        
        if context.framework and context.framework not in memory_tags:
            return False
        
        return True
    
    async def _check_security_issues(self, code: str, context: CodeContext) -> List[Dict[str, Any]]:
        """Check for security-related issues."""
        alerts = []
        
        # Check security patterns
        for pattern_info in self.security_patterns:
            matches = re.finditer(pattern_info["pattern"], code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                alerts.append({
                    "type": "security_alert",
                    "alert_type": pattern_info["alert_type"],
                    "message": pattern_info["message"],
                    "severity": pattern_info["severity"],
                    "line": line_number,
                    "column": match.start() - code.rfind('\n', 0, match.start()) - 1,
                    "fix": pattern_info["fix"],
                    "matched_text": match.group()
                })
        
        return alerts
    
    async def _generate_predictions(self, code: str, context: CodeContext) -> List[Dict[str, Any]]:
        """Generate predictions about potential issues."""
        predictions = []
        
        # Predict potential bugs based on patterns
        if "try:" in code and "except:" in code and "finally:" not in code:
            predictions.append({
                "type": "bug_prediction",
                "message": "Potential resource leak - consider using finally block",
                "confidence": 0.8,
                "line": context.line_number,
                "column": context.column,
                "category": "resource_management"
            })
        
        # Predict performance issues
        if code.count("for") > 2 and code.count("if") > 3:
            predictions.append({
                "type": "performance_prediction",
                "message": "Complex nested loops detected - consider optimization",
                "confidence": 0.7,
                "line": context.line_number,
                "column": context.column,
                "category": "performance"
            })
        
        # Predict maintainability issues
        if len(code.split('\n')) > 50:
            predictions.append({
                "type": "maintainability_prediction",
                "message": "Large code block detected - consider refactoring",
                "confidence": 0.6,
                "line": context.line_number,
                "column": context.column,
                "category": "maintainability"
            })
        
        return predictions
    
    def _calculate_confidence(self, suggestions: List[Dict], predictions: List[Dict], alerts: List[Dict]) -> float:
        """Calculate overall confidence in the analysis."""
        if not suggestions and not predictions and not alerts:
            return 0.0
        
        # Weight different types of findings
        suggestion_weight = 0.3
        prediction_weight = 0.4
        alert_weight = 0.3
        
        # Calculate weighted average
        total_weight = 0
        weighted_sum = 0
        
        if suggestions:
            avg_suggestion_confidence = sum(s.get("confidence", 0.8) for s in suggestions) / len(suggestions)
            weighted_sum += avg_suggestion_confidence * suggestion_weight
            total_weight += suggestion_weight
        
        if predictions:
            avg_prediction_confidence = sum(p.get("confidence", 0.7) for p in predictions) / len(predictions)
            weighted_sum += avg_prediction_confidence * prediction_weight
            total_weight += prediction_weight
        
        if alerts:
            avg_alert_confidence = sum(a.get("confidence", 0.9) for a in alerts) / len(alerts)
            weighted_sum += avg_alert_confidence * alert_weight
            total_weight += alert_weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0

# Global analyzer instance
analyzer = RealTimeCodeAnalyzer()

async def analyze_code_for_ide(code: str, context_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for IDE code analysis."""
    # Convert context dict to CodeContext
    context = CodeContext(
        language=context_dict.get("language", "python"),
        file_path=context_dict.get("file_path", ""),
        line_number=context_dict.get("line_number", 1),
        column=context_dict.get("column", 1),
        project_name=context_dict.get("project_name"),
        namespace=context_dict.get("namespace"),
        framework=context_dict.get("framework"),
        recent_changes=context_dict.get("recent_changes")
    )
    
    # Perform analysis
    result = await analyzer.analyze_code_context(code, context)
    
    # Convert to dict for JSON serialization
    return {
        "suggestions": result.suggestions,
        "predictions": result.predictions,
        "alerts": result.alerts,
        "timestamp": result.timestamp,
        "confidence": result.confidence
    } 