#!/usr/bin/env python3
"""
Sales Presentation Updater Worker

Automated system that monitors project changes and updates the sales presentation
to reflect current capabilities and features. Leverages the existing worker
infrastructure and memory system for change detection and analysis.
"""

import os
import json
import asyncio
import logging
import re
import difflib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import subprocess
import aiohttp
from dataclasses import dataclass
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SalesUpdate:
    """Represents a sales presentation update"""
    section: str
    change_type: str  # 'feature', 'improvement', 'fix', 'new_demo'
    content: str
    confidence: float
    source_change: str
    priority: str  # 'high', 'medium', 'low'

@dataclass
class PresentationSection:
    """Represents a section of the sales presentation"""
    name: str
    content: str
    start_line: int
    end_line: int
    last_updated: Optional[datetime] = None

class SalesPresentationUpdater:
    """
    Worker that monitors project changes and updates the sales presentation
    to reflect current capabilities and features.
    """
    
    def __init__(self):
        self.presentation_path = Path("docs/ai_ide_api_sales_presentation.md")
        self.backup_path = Path("docs/ai_ide_api_sales_presentation.backup.md")
        self.memory_api_url = os.getenv("MEMORY_API_URL", "http://localhost:9103/memory")
        self.memory_api_token = os.getenv("MEMORY_API_TOKEN", "")
        self.llm_service_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        # Sales-relevant keywords and patterns
        self.sales_keywords = [
            'feature', 'capability', 'performance', 'improvement', 'enhancement',
            'new', 'added', 'implemented', 'optimized', 'faster', 'better',
            'user experience', 'onboarding', 'workflow', 'automation',
            'memory system', 'ai', 'machine learning', 'integration'
        ]
        
        # Presentation sections to monitor
        self.presentation_sections = [
            'system_architecture', 'memory_system', 'ai_augmented_code_review',
            'frictionless_onboarding', 'seamless_test_environment',
            'error_handling_debugging', 'demo_examples'
        ]

    async def process_sales_update_job(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process a sales presentation update job"""
        logger.info(f"Processing sales presentation update job: {job_config}")
        
        try:
            # Step 1: Detect recent changes
            changes = await self.detect_recent_changes(job_config.get("since", "1 week ago"))
            
            # Step 2: Analyze changes for sales impact
            sales_updates = await self.analyze_sales_impact(changes)
            
            # Step 3: Generate presentation updates
            presentation_updates = await self.generate_presentation_updates(sales_updates)
            
            # Step 4: Apply updates (if not dry run)
            if not job_config.get("dry_run", False):
                await self.apply_presentation_updates(presentation_updates)
            
            # Step 5: Update memory system
            await self.update_memory_system(sales_updates, presentation_updates)
            
            return {
                "status": "success",
                "changes_analyzed": len(changes),
                "sales_updates": len(sales_updates),
                "presentation_updates": len(presentation_updates),
                "dry_run": job_config.get("dry_run", False)
            }
            
        except Exception as e:
            logger.error(f"Error processing sales update job: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def detect_recent_changes(self, since: str) -> List[Dict[str, Any]]:
        """Detect recent changes using git history analysis"""
        logger.info(f"Detecting changes since: {since}")
        
        # Use existing git history analysis
        cmd = [
            "make", "-f", "Makefile.ai", "misc-git-history-trigger",
            f"SINCE='{since}'",
            "CREATE_MEMORY=true",
            "MEMORY_NAMESPACE=sales_analysis",
            "MEMORY_TAGS='sales presentation'"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Git history analysis completed")
            
            # Parse the output to extract relevant changes
            changes = self.parse_git_changes(result.stdout)
            return changes
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git history analysis failed: {e}")
            return []

    def parse_git_changes(self, output: str) -> List[Dict[str, Any]]:
        """Parse git history output to extract relevant changes"""
        changes = []
        
        # Simple parsing - in practice, you'd want more sophisticated parsing
        lines = output.split('\n')
        current_change = None
        
        for line in lines:
            if line.startswith('commit '):
                if current_change:
                    changes.append(current_change)
                current_change = {
                    'commit': line.split()[1],
                    'message': '',
                    'files': [],
                    'sales_relevant': False
                }
            elif line.startswith('    ') and current_change:
                current_change['message'] = line.strip()
                # Check if change is sales-relevant
                current_change['sales_relevant'] = any(
                    keyword in line.lower() for keyword in self.sales_keywords
                )
            elif line.startswith(' ') and '|' in line and current_change:
                # File change line
                parts = line.strip().split('|')
                if len(parts) >= 2:
                    filename = parts[0].strip()
                    current_change['files'].append(filename)
        
        if current_change:
            changes.append(current_change)
        
        # Filter for sales-relevant changes
        sales_relevant_changes = [c for c in changes if c['sales_relevant']]
        logger.info(f"Found {len(sales_relevant_changes)} sales-relevant changes out of {len(changes)} total")
        
        return sales_relevant_changes

    async def analyze_sales_impact(self, changes: List[Dict[str, Any]]) -> List[SalesUpdate]:
        """Analyze changes for sales presentation impact"""
        logger.info(f"Analyzing sales impact of {len(changes)} changes")
        
        sales_updates = []
        
        for change in changes:
            # Use LLM to analyze the sales impact
            analysis = await self.analyze_change_with_llm(change)
            
            if analysis:
                sales_updates.append(analysis)
        
        logger.info(f"Generated {len(sales_updates)} sales updates")
        return sales_updates

    async def analyze_change_with_llm(self, change: Dict[str, Any]) -> Optional[SalesUpdate]:
        """Use LLM to analyze a change for sales impact"""
        try:
            prompt = f"""
            Analyze this code change for its impact on a sales presentation:
            
            Commit: {change.get('commit', '')}
            Message: {change.get('message', '')}
            Files: {', '.join(change.get('files', []))}
            
            Determine if this change should be reflected in the sales presentation.
            If yes, provide:
            1. Which section it affects (system_architecture, memory_system, ai_augmented_code_review, etc.)
            2. What type of change it is (feature, improvement, fix, new_demo)
            3. A brief description for the sales presentation
            4. Confidence level (0.0-1.0)
            5. Priority (high, medium, low)
            
            Respond in JSON format:
            {{
                "should_update": true/false,
                "section": "section_name",
                "change_type": "feature/improvement/fix/new_demo",
                "content": "description for sales presentation",
                "confidence": 0.85,
                "priority": "high/medium/low"
            }}
            """
            
            # Call LLM service
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_service_url}/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get('response', '')
                        
                        # Parse JSON response
                        try:
                            analysis = json.loads(response_text)
                            if analysis.get('should_update', False):
                                return SalesUpdate(
                                    section=analysis.get('section', ''),
                                    change_type=analysis.get('change_type', ''),
                                    content=analysis.get('content', ''),
                                    confidence=analysis.get('confidence', 0.5),
                                    source_change=change.get('commit', ''),
                                    priority=analysis.get('priority', 'medium')
                                )
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse LLM response: {response_text}")
            
        except Exception as e:
            logger.error(f"Error analyzing change with LLM: {e}")
        
        return None

    async def generate_presentation_updates(self, sales_updates: List[SalesUpdate]) -> List[Dict[str, Any]]:
        """Generate specific updates for the presentation"""
        logger.info(f"Generating presentation updates for {len(sales_updates)} sales updates")
        
        # Load current presentation
        current_presentation = self.load_presentation()
        presentation_sections = self.parse_presentation_sections(current_presentation)
        
        updates = []
        
        for update in sales_updates:
            if update.confidence > 0.7:  # Only apply high-confidence updates
                section_update = await self.generate_section_update(
                    update, presentation_sections.get(update.section)
                )
                if section_update:
                    updates.append(section_update)
        
        logger.info(f"Generated {len(updates)} presentation updates")
        return updates

    def load_presentation(self) -> str:
        """Load the current sales presentation"""
        try:
            with open(self.presentation_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Sales presentation not found: {self.presentation_path}")
            return ""

    def parse_presentation_sections(self, content: str) -> Dict[str, PresentationSection]:
        """Parse the presentation into sections"""
        sections = {}
        lines = content.split('\n')
        
        current_section = None
        current_content = []
        start_line = 0
        
        for i, line in enumerate(lines):
            if line.startswith('## ') and not line.startswith('### '):
                # Save previous section
                if current_section:
                    sections[current_section] = PresentationSection(
                        name=current_section,
                        content='\n'.join(current_content),
                        start_line=start_line,
                        end_line=i-1
                    )
                
                # Start new section
                current_section = line[3:].strip().lower().replace(' ', '_').replace(':', '')
                current_content = [line]
                start_line = i
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = PresentationSection(
                name=current_section,
                content='\n'.join(current_content),
                start_line=start_line,
                end_line=len(lines)-1
            )
        
        return sections

    async def generate_section_update(self, update: SalesUpdate, section: Optional[PresentationSection]) -> Optional[Dict[str, Any]]:
        """Generate a specific update for a presentation section"""
        if not section:
            logger.warning(f"Section not found: {update.section}")
            return None
        
        # Use LLM to generate the specific update
        prompt = f"""
        Update this sales presentation section to reflect the new change:
        
        Current section content:
        {section.content}
        
        New change to incorporate:
        - Type: {update.change_type}
        - Description: {update.content}
        - Source: {update.source_change}
        
        Generate an updated version of this section that incorporates the new information
        while maintaining the sales-focused tone and structure. Keep the existing content
        but add or modify relevant parts to highlight the new capability.
        
        Return only the updated section content, maintaining the same markdown formatting.
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.llm_service_url}/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        updated_content = result.get('response', '').strip()
                        
                        return {
                            "section": update.section,
                            "original_content": section.content,
                            "updated_content": updated_content,
                            "change_type": update.change_type,
                            "source_change": update.source_change,
                            "priority": update.priority
                        }
        
        except Exception as e:
            logger.error(f"Error generating section update: {e}")
        
        return None

    async def apply_presentation_updates(self, updates: List[Dict[str, Any]]) -> None:
        """Apply updates to the sales presentation"""
        logger.info(f"Applying {len(updates)} presentation updates")
        
        # Create backup
        self.create_backup()
        
        # Load current presentation
        content = self.load_presentation()
        lines = content.split('\n')
        
        # Apply updates in reverse order to maintain line numbers
        updates.sort(key=lambda u: u.get('priority', 'medium') == 'high', reverse=True)
        
        for update in updates:
            section_name = update['section']
            updated_content = update['updated_content']
            
            # Find and replace the section
            section_pattern = f"## {section_name.replace('_', ' ').title()}"
            
            for i, line in enumerate(lines):
                if line.startswith(section_pattern):
                    # Find the end of this section
                    end_line = i + 1
                    while end_line < len(lines) and not lines[end_line].startswith('## '):
                        end_line += 1
                    
                    # Replace the section content
                    lines[i:end_line] = [updated_content]
                    break
        
        # Write updated presentation
        updated_content = '\n'.join(lines)
        with open(self.presentation_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info("Presentation updates applied successfully")

    def create_backup(self) -> None:
        """Create a backup of the current presentation"""
        try:
            if self.presentation_path.exists():
                import shutil
                shutil.copy2(self.presentation_path, self.backup_path)
                logger.info(f"Backup created: {self.backup_path}")
        except Exception as e:
            logger.error(f"Error creating backup: {e}")

    async def update_memory_system(self, sales_updates: List[SalesUpdate], presentation_updates: List[Dict[str, Any]]) -> None:
        """Update the memory system with sales presentation changes"""
        logger.info("Updating memory system with sales presentation changes")
        
        # Create memory node for this update session
        content = f"Sales presentation updated with {len(presentation_updates)} changes based on {len(sales_updates)} sales-relevant updates"
        
        meta = {
            "type": "sales_presentation_update",
            "timestamp": datetime.now().isoformat(),
            "sales_updates_count": len(sales_updates),
            "presentation_updates_count": len(presentation_updates),
            "tags": ["sales", "presentation", "automation", "update"],
            "categories": ["documentation", "sales", "automation"]
        }
        
        try:
            await self.send_to_memory_api(content, meta)
            logger.info("Memory system updated successfully")
        except Exception as e:
            logger.error(f"Error updating memory system: {e}")

    async def send_to_memory_api(self, content: str, meta: Dict[str, Any]) -> None:
        """Send data to memory API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.memory_api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "content": content,
                "meta": json.dumps(meta)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.memory_api_url}/nodes",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Memory node created: {result.get('id')}")
                    else:
                        logger.error(f"Failed to create memory node: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending to memory API: {e}")

    async def validate_presentation(self) -> Dict[str, Any]:
        """Validate the sales presentation for quality and consistency"""
        logger.info("Validating sales presentation")
        
        content = self.load_presentation()
        
        validation_results = {
            "status": "ok",
            "issues": [],
            "warnings": []
        }
        
        # Check for broken links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)
        
        for link_text, link_url in links:
            if link_url.startswith('http'):
                # Check external links
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.head(link_url, timeout=5) as response:
                            if response.status >= 400:
                                validation_results["issues"].append(f"Broken external link: {link_url}")
                except Exception:
                    validation_results["warnings"].append(f"Could not verify external link: {link_url}")
        
        # Check for consistent formatting
        if not re.search(r'## .*', content):
            validation_results["issues"].append("Missing section headers")
        
        # Check for demo examples
        if not re.search(r'## DEMO:', content, re.IGNORECASE):
            validation_results["warnings"].append("No demo examples found")
        
        # Update status based on issues
        if validation_results["issues"]:
            validation_results["status"] = "error"
        elif validation_results["warnings"]:
            validation_results["status"] = "warning"
        
        return validation_results

async def main():
    """Main function for the sales presentation updater"""
    parser = argparse.ArgumentParser(description="Sales Presentation Updater")
    parser.add_argument("--analyze", action="store_true", help="Analyze changes for sales impact")
    parser.add_argument("--preview", action="store_true", help="Preview updates without applying")
    parser.add_argument("--apply", action="store_true", help="Apply updates to presentation")
    parser.add_argument("--validate", action="store_true", help="Validate presentation")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--generate-report", action="store_true", help="Generate report")
    parser.add_argument("--worker", action="store_true", help="Run as worker")
    parser.add_argument("--test", action="store_true", help="Run tests")
    
    parser.add_argument("--since", default="1 week ago", help="Time period to analyze")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    parser.add_argument("--review", action="store_true", help="Enable human review")
    parser.add_argument("--full-analysis", action="store_true", help="Run full analysis")
    parser.add_argument("--check-links", action="store_true", help="Check for broken links")
    parser.add_argument("--check-markdown", action="store_true", help="Validate markdown structure")
    parser.add_argument("--output-format", default="json", help="Output format for reports")
    parser.add_argument("--start", action="store_true", help="Start worker")
    parser.add_argument("--stop", action="store_true", help="Stop worker")
    parser.add_argument("--status", action="store_true", help="Check worker status")
    
    args = parser.parse_args()
    
    updater = SalesPresentationUpdater()
    
    try:
        if args.analyze:
            # Analyze changes for sales impact
            job_config = {
                "type": "sales_presentation_update",
                "since": args.since,
                "dry_run": args.dry_run,
                "analysis_focus": [
                    "new_features",
                    "capability_improvements",
                    "performance_enhancements",
                    "user_experience_updates"
                ]
            }
            
            if args.full_analysis:
                job_config["since"] = "1 month ago"
            
            result = await updater.process_sales_update_job(job_config)
            print(f"Analysis result: {result}")
            
        elif args.preview:
            # Preview updates without applying
            job_config = {
                "type": "sales_presentation_update",
                "since": args.since,
                "dry_run": True,
                "analysis_focus": [
                    "new_features",
                    "capability_improvements",
                    "performance_enhancements",
                    "user_experience_updates"
                ]
            }
            
            result = await updater.process_sales_update_job(job_config)
            print(f"Preview result: {result}")
            
        elif args.apply:
            # Apply updates to presentation
            job_config = {
                "type": "sales_presentation_update",
                "since": args.since,
                "dry_run": args.dry_run,
                "review": args.review,
                "analysis_focus": [
                    "new_features",
                    "capability_improvements",
                    "performance_enhancements",
                    "user_experience_updates"
                ]
            }
            
            result = await updater.process_sales_update_job(job_config)
            print(f"Apply result: {result}")
            
        elif args.validate:
            # Validate presentation
            validation = await updater.validate_presentation()
            
            if args.check_links:
                # Additional link checking
                print("Checking links...")
                # Link checking logic would go here
            
            if args.check_markdown:
                # Additional markdown validation
                print("Validating markdown...")
                # Markdown validation logic would go here
            
            print(f"Validation result: {validation}")
            
        elif args.health_check:
            # Run health check
            validation = await updater.validate_presentation()
            print(f"Health check result: {validation}")
            
        elif args.generate_report:
            # Generate report
            job_config = {
                "type": "sales_presentation_update",
                "since": args.since,
                "dry_run": True
            }
            
            result = await updater.process_sales_update_job(job_config)
            validation = await updater.validate_presentation()
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "analysis_result": result,
                "validation_result": validation,
                "format": args.output_format
            }
            
            if args.output_format == "json":
                print(json.dumps(report, indent=2))
            else:
                print(f"Report generated: {report}")
                
        elif args.worker:
            # Worker mode
            if args.start:
                print("Starting sales presentation worker...")
                # Worker start logic would go here
            elif args.stop:
                print("Stopping sales presentation worker...")
                # Worker stop logic would go here
            elif args.status:
                print("Checking worker status...")
                # Worker status logic would go here
            else:
                print("Worker mode requires --start, --stop, or --status")
                
        elif args.test:
            # Test mode
            print("Running sales presentation updater tests...")
            
            # Test analysis
            test_job_config = {
                "type": "sales_presentation_update",
                "since": "1 day ago",
                "dry_run": True,
                "analysis_focus": [
                    "new_features",
                    "capability_improvements"
                ]
            }
            
            result = await updater.process_sales_update_job(test_job_config)
            print(f"Test analysis result: {result}")
            
            # Test validation
            validation = await updater.validate_presentation()
            print(f"Test validation result: {validation}")
            
        else:
            # Default: run basic analysis
            job_config = {
                "type": "sales_presentation_update",
                "since": args.since,
                "dry_run": True,
                "analysis_focus": [
                    "new_features",
                    "capability_improvements",
                    "performance_enhancements",
                    "user_experience_updates"
                ]
            }
            
            result = await updater.process_sales_update_job(job_config)
            print(f"Default analysis result: {result}")
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 