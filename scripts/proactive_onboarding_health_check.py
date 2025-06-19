#!/usr/bin/env python3
"""
Proactive Onboarding Health Check System

This script provides continuous monitoring and proactive health checks for the AI-IDE system.
It can run in the background and provide detailed user information, system status, and recommendations.
"""

import os
import re
import sys
import json
import time
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import argparse

# Configuration
CHECK_INTERVAL = 300  # 5 minutes
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
LOG_FILE = "onboarding_health.log"


@dataclass
class HealthCheckResult:
    """Result of a health check"""

    name: str
    status: str  # "OK", "WARNING", "ERROR", "INFO"
    message: str
    details: Optional[Dict] = None
    recommendations: Optional[List[str]] = None
    timestamp: Optional[datetime] = None


class ProactiveOnboardingHealthCheck:
    def __init__(self, continuous: bool = False, verbose: bool = False):
        self.continuous = continuous
        self.verbose = verbose
        self.results: List[HealthCheckResult] = []
        self.start_time = datetime.now()

    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"

        if self.verbose:
            print(log_entry)

        # Always write to log file
        with open(LOG_FILE, "a") as f:
            f.write(log_entry + "\n")

    def check_file_exists(self, path: str, required: bool = True) -> HealthCheckResult:
        """Check if a file exists"""
        exists = os.path.exists(path)
        if exists:
            return HealthCheckResult(
                name=f"File: {path}", status="OK", message=f"File {path} exists"
            )
        elif required:
            return HealthCheckResult(
                name=f"File: {path}",
                status="ERROR",
                message=f"Required file {path} not found",
                recommendations=[f"Create or restore {path}"],
            )
        else:
            return HealthCheckResult(
                name=f"File: {path}",
                status="WARNING",
                message=f"Optional file {path} not found",
            )

    def check_env_variables(self) -> HealthCheckResult:
        """Check required environment variables"""
        required_vars = [
            "ENVIRONMENT",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "REDIS_HOST",
            "REDIS_PORT",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if not missing_vars:
            return HealthCheckResult(
                name="Environment Variables",
                status="OK",
                message="All required environment variables are set",
                details={"checked_vars": required_vars},
            )
        else:
            return HealthCheckResult(
                name="Environment Variables",
                status="ERROR",
                message=f"Missing environment variables: {', '.join(missing_vars)}",
                recommendations=[
                    "Create or update .env file",
                    "Set required environment variables",
                    "Check docker-compose.yml for proper environment configuration",
                ],
                details={"missing_vars": missing_vars},
            )

    def check_docker_services(self) -> HealthCheckResult:
        """Check if Docker services are running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return HealthCheckResult(
                    name="Docker Services",
                    status="ERROR",
                    message="Docker is not running or accessible",
                    recommendations=["Start Docker", "Check Docker permissions"],
                )

            services = result.stdout.strip().split("\n")
            running_services = [s.split("\t")[0] for s in services if s.strip()]

            required_services = ["api", "db-test", "frontend"]
            missing_services = [
                s
                for s in required_services
                if not any(s in rs for rs in running_services)
            ]

            if not missing_services:
                return HealthCheckResult(
                    name="Docker Services",
                    status="OK",
                    message="All required Docker services are running",
                    details={"running_services": running_services},
                )
            else:
                return HealthCheckResult(
                    name="Docker Services",
                    status="WARNING",
                    message=f"Missing services: {', '.join(missing_services)}",
                    recommendations=[
                        "Run: make -f Makefile.ai ai-up",
                        "Check docker-compose.yml configuration",
                        "Verify Docker has sufficient resources",
                    ],
                    details={
                        "missing_services": missing_services,
                        "running_services": running_services,
                    },
                )

        except subprocess.TimeoutExpired:
            return HealthCheckResult(
                name="Docker Services",
                status="ERROR",
                message="Docker command timed out",
                recommendations=[
                    "Check Docker daemon status",
                    "Restart Docker if needed",
                ],
            )
        except Exception as e:
            return HealthCheckResult(
                name="Docker Services",
                status="ERROR",
                message=f"Docker check failed: {str(e)}",
                recommendations=["Install Docker", "Check Docker installation"],
            )

    def check_api_connectivity(self) -> HealthCheckResult:
        """Check API connectivity and health"""
        try:
            # Check basic connectivity
            response = requests.get(f"{API_BASE_URL}/env", timeout=5)
            if response.status_code == 200:
                env_data = response.json()

                # Check specific endpoints
                endpoints_to_check = [
                    "/rules",
                    "/memory/nodes",
                    "/enhancements",
                    "/bug-reports",
                ]

                working_endpoints = []
                failed_endpoints = []

                for endpoint in endpoints_to_check:
                    try:
                        ep_response = requests.get(
                            f"{API_BASE_URL}{endpoint}", timeout=3
                        )
                        if ep_response.status_code == 200:
                            working_endpoints.append(endpoint)
                        else:
                            failed_endpoints.append(
                                f"{endpoint} (status: {ep_response.status_code})"
                            )
                    except:
                        failed_endpoints.append(f"{endpoint} (connection failed)")

                if not failed_endpoints:
                    return HealthCheckResult(
                        name="API Connectivity",
                        status="OK",
                        message="API is fully operational",
                        details={
                            "environment": env_data.get("environment", "unknown"),
                            "working_endpoints": working_endpoints,
                        },
                    )
                else:
                    return HealthCheckResult(
                        name="API Connectivity",
                        status="WARNING",
                        message=f"API partially operational. Failed endpoints: {', '.join(failed_endpoints)}",
                        recommendations=[
                            "Check API logs: make -f Makefile.ai logs-api",
                            "Restart API: make -f Makefile.ai ai-api-restart-wait",
                            "Check database connectivity",
                        ],
                        details={
                            "working_endpoints": working_endpoints,
                            "failed_endpoints": failed_endpoints,
                        },
                    )
            else:
                return HealthCheckResult(
                    name="API Connectivity",
                    status="ERROR",
                    message=f"API returned status {response.status_code}",
                    recommendations=[
                        "Start API service: make -f Makefile.ai ai-up",
                        "Check API logs for errors",
                        "Verify database is running",
                    ],
                )

        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                name="API Connectivity",
                status="ERROR",
                message="Cannot connect to API",
                recommendations=[
                    "Start API service: make -f Makefile.ai ai-up",
                    "Check if API is running on correct port",
                    "Verify firewall settings",
                ],
            )
        except Exception as e:
            return HealthCheckResult(
                name="API Connectivity",
                status="ERROR",
                message=f"API check failed: {str(e)}",
                recommendations=["Check API configuration", "Review error logs"],
            )

    def check_ollama_service(self) -> HealthCheckResult:
        """Check Ollama LLM service"""
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]

                if model_names:
                    return HealthCheckResult(
                        name="Ollama Service",
                        status="OK",
                        message=f"Ollama is running with {len(models)} models",
                        details={"available_models": model_names},
                    )
                else:
                    return HealthCheckResult(
                        name="Ollama Service",
                        status="WARNING",
                        message="Ollama is running but no models are available",
                        recommendations=[
                            "Pull a model: make -f Makefile.ai ai-ollama-pull-model",
                            "Check Ollama logs: make -f Makefile.ai ai-ollama-logs",
                        ],
                    )
            else:
                return HealthCheckResult(
                    name="Ollama Service",
                    status="ERROR",
                    message=f"Ollama returned status {response.status_code}",
                    recommendations=[
                        "Start Ollama: make -f Makefile.ai ai-ollama-serve-docker-gateway-bg",
                        "Check Ollama installation",
                    ],
                )

        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                name="Ollama Service",
                status="WARNING",
                message="Ollama service is not accessible",
                recommendations=[
                    "Start Ollama: make -f Makefile.ai ai-ollama-serve-docker-gateway-bg",
                    "Install Ollama if not installed",
                    "Check Ollama configuration",
                ],
            )
        except Exception as e:
            return HealthCheckResult(
                name="Ollama Service",
                status="ERROR",
                message=f"Ollama check failed: {str(e)}",
                recommendations=["Check Ollama logs", "Restart Ollama service"],
            )

    def check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and health"""
        try:
            # Try to connect to database via API
            response = requests.get(f"{API_BASE_URL}/env", timeout=5)
            if response.status_code == 200:
                env_data = response.json()

                # Check if database connection is working
                try:
                    db_response = requests.get(f"{API_BASE_URL}/rules", timeout=5)
                    if db_response.status_code == 200:
                        rules = db_response.json()
                        return HealthCheckResult(
                            name="Database Health",
                            status="OK",
                            message=f"Database is accessible with {len(rules)} rules",
                            details={
                                "database_url": env_data.get("database_url", "unknown"),
                                "rule_count": len(rules),
                            },
                        )
                    else:
                        return HealthCheckResult(
                            name="Database Health",
                            status="ERROR",
                            message=f"Database query failed with status {db_response.status_code}",
                            recommendations=[
                                "Check database logs: make -f Makefile.ai logs-db",
                                "Run migrations: make -f Makefile.ai ai-db-migrate",
                                "Check database connectivity",
                            ],
                        )
                except Exception as e:
                    return HealthCheckResult(
                        name="Database Health",
                        status="ERROR",
                        message=f"Database query failed: {str(e)}",
                        recommendations=[
                            "Check database service",
                            "Verify database credentials",
                            "Run database health check",
                        ],
                    )
            else:
                return HealthCheckResult(
                    name="Database Health",
                    status="ERROR",
                    message="Cannot access API to check database",
                    recommendations=[
                        "Start API service first",
                        "Check API connectivity",
                    ],
                )

        except Exception as e:
            return HealthCheckResult(
                name="Database Health",
                status="ERROR",
                message=f"Database health check failed: {str(e)}",
                recommendations=["Check database configuration", "Review error logs"],
            )

    def check_makefile_targets(self) -> HealthCheckResult:
        """Check if required Makefile targets exist"""
        required_targets = [
            "ai-test",
            "ai-test-one",
            "ai-test-json",
            "ai-accept-enhancement",
            "ai-complete-enhancement",
            "ai-list-enhancements",
            "ai-proposal-to-enhancement",
            "ai-db-autorevision",
            "ai-db-migrate",
            "ai-bug-report",
            "ai-suggest-enhancement",
            "ai-onboarding-health",
        ]

        if not os.path.exists("Makefile.ai"):
            return HealthCheckResult(
                name="Makefile Targets",
                status="ERROR",
                message="Makefile.ai not found",
                recommendations=["Create Makefile.ai", "Restore from backup"],
            )

        with open("Makefile.ai") as f:
            makefile_content = f.read()

        missing_targets = []
        for target in required_targets:
            if f"{target}:" not in makefile_content:
                missing_targets.append(target)

        if not missing_targets:
            return HealthCheckResult(
                name="Makefile Targets",
                status="OK",
                message="All required Makefile targets are present",
                details={"checked_targets": required_targets},
            )
        else:
            return HealthCheckResult(
                name="Makefile Targets",
                status="WARNING",
                message=f"Missing Makefile targets: {', '.join(missing_targets)}",
                recommendations=[
                    "Update Makefile.ai with missing targets",
                    "Check Makefile.ai version",
                    "Restore from backup if needed",
                ],
                details={"missing_targets": missing_targets},
            )

    def check_rules_directory(self) -> HealthCheckResult:
        """Check .cursor/rules directory structure"""
        rules_dir = ".cursor/rules"

        if not os.path.isdir(rules_dir):
            return HealthCheckResult(
                name="Rules Directory",
                status="ERROR",
                message="Rules directory not found",
                recommendations=[
                    "Create .cursor/rules directory",
                    "Restore rules from backup",
                    "Check git repository",
                ],
            )

        mdc_files = []
        txt_files = []
        invalid_files = []

        for fname in os.listdir(rules_dir):
            path = os.path.join(rules_dir, fname)
            if fname.endswith(".mdc"):
                # Check YAML frontmatter
                with open(path) as f:
                    content = f.read()
                yaml_pattern = re.compile(r"^---\s*([\s\S]+?)---", re.MULTILINE)
                m = yaml_pattern.search(content)

                if m:
                    yaml_block = m.group(1)
                    if "description:" in yaml_block and "globs:" in yaml_block:
                        mdc_files.append(fname)
                    else:
                        invalid_files.append(f"{fname} (missing required frontmatter)")
                else:
                    invalid_files.append(f"{fname} (missing YAML frontmatter)")
            elif fname.endswith(".txt"):
                txt_files.append(fname)

        if txt_files:
            return HealthCheckResult(
                name="Rules Directory",
                status="WARNING",
                message=f"Found .txt files (should be .mdc): {', '.join(txt_files)}",
                recommendations=[
                    "Convert .txt files to .mdc format",
                    "Add YAML frontmatter to .mdc files",
                ],
                details={"txt_files": txt_files, "mdc_files": mdc_files},
            )
        elif invalid_files:
            return HealthCheckResult(
                name="Rules Directory",
                status="WARNING",
                message=f"Invalid .mdc files: {', '.join(invalid_files)}",
                recommendations=[
                    "Add YAML frontmatter to .mdc files",
                    "Include description and globs fields",
                ],
                details={"invalid_files": invalid_files, "mdc_files": mdc_files},
            )
        else:
            return HealthCheckResult(
                name="Rules Directory",
                status="OK",
                message=f"Rules directory is properly structured with {len(mdc_files)} valid .mdc files",
                details={"mdc_files": mdc_files},
            )

    def check_onboarding_documentation(self) -> HealthCheckResult:
        """Check onboarding documentation completeness"""
        required_files = [
            "ONBOARDING.md",
            "ONBOARDING_OTHER_AI_IDE.md",
            "INTEGRATING_AI_IDE.md",
        ]

        missing_files = []
        present_files = []

        for file in required_files:
            if os.path.exists(file):
                present_files.append(file)
            else:
                missing_files.append(file)

        if missing_files:
            return HealthCheckResult(
                name="Onboarding Documentation",
                status="ERROR",
                message=f"Missing onboarding files: {', '.join(missing_files)}",
                recommendations=[
                    "Restore missing onboarding files",
                    "Check git repository",
                    "Create missing documentation",
                ],
                details={
                    "missing_files": missing_files,
                    "present_files": present_files,
                },
            )
        else:
            # Check for "What's New" section in ONBOARDING.md
            with open("ONBOARDING.md") as f:
                content = f.read()

            whats_new_match = re.search(
                r"## 🚨 What's New.*?\n(- .+\n)+", content, re.DOTALL
            )
            if (
                whats_new_match
                and len(whats_new_match.group(0).strip().splitlines()) > 2
            ):
                return HealthCheckResult(
                    name="Onboarding Documentation",
                    status="OK",
                    message="All onboarding documentation is present and up to date",
                    details={"present_files": present_files, "has_whats_new": True},
                )
            else:
                return HealthCheckResult(
                    name="Onboarding Documentation",
                    status="WARNING",
                    message="Onboarding documentation present but 'What's New' section is missing or empty",
                    recommendations=[
                        "Add 'What's New' section to ONBOARDING.md",
                        "Update documentation with recent changes",
                    ],
                    details={"present_files": present_files, "has_whats_new": False},
                )

    def generate_user_report(self) -> Dict:
        """Generate a comprehensive user report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_uptime": str(datetime.now() - self.start_time),
            "overall_status": "UNKNOWN",
            "checks": [],
            "summary": {
                "total_checks": len(self.results),
                "ok_count": 0,
                "warning_count": 0,
                "error_count": 0,
                "info_count": 0,
            },
            "recommendations": [],
            "quick_fixes": [],
        }

        # Count statuses
        for result in self.results:
            report["checks"].append(
                {
                    "name": result.name,
                    "status": result.status,
                    "message": result.message,
                    "details": result.details,
                    "recommendations": result.recommendations,
                }
            )

            if result.status == "OK":
                report["summary"]["ok_count"] += 1
            elif result.status == "WARNING":
                report["summary"]["warning_count"] += 1
            elif result.status == "ERROR":
                report["summary"]["error_count"] += 1
            elif result.status == "INFO":
                report["summary"]["info_count"] += 1

        # Determine overall status
        if report["summary"]["error_count"] > 0:
            report["overall_status"] = "ERROR"
        elif report["summary"]["warning_count"] > 0:
            report["overall_status"] = "WARNING"
        else:
            report["overall_status"] = "OK"

        # Collect all recommendations
        all_recommendations = []
        for result in self.results:
            if result.recommendations:
                all_recommendations.extend(result.recommendations)

        report["recommendations"] = list(set(all_recommendations))  # Remove duplicates

        # Generate quick fixes
        if report["summary"]["error_count"] > 0:
            report["quick_fixes"] = [
                "Run: make -f Makefile.ai ai-up",
                "Check logs: make -f Makefile.ai logs",
                "Run health check: make -f Makefile.ai ai-onboarding-health",
            ]

        return report

    def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all health checks"""
        self.log("Starting comprehensive health check...")

        checks = [
            self.check_env_variables,
            self.check_docker_services,
            self.check_api_connectivity,
            self.check_ollama_service,
            self.check_database_health,
            self.check_makefile_targets,
            self.check_rules_directory,
            self.check_onboarding_documentation,
        ]

        self.results = []
        for check in checks:
            try:
                result = check()
                result.timestamp = datetime.now()
                self.results.append(result)
                self.log(f"{result.name}: {result.status} - {result.message}")
            except Exception as e:
                error_result = HealthCheckResult(
                    name=check.__name__,
                    status="ERROR",
                    message=f"Check failed with exception: {str(e)}",
                    timestamp=datetime.now(),
                )
                self.results.append(error_result)
                self.log(f"Check {check.__name__} failed: {str(e)}", "ERROR")

        return self.results

    def print_report(self, format: str = "text"):
        """Print the health check report"""
        report = self.generate_user_report()

        if format == "json":
            print(json.dumps(report, indent=2))
        else:
            # Text format
            print("\n" + "=" * 60)
            print("PROACTIVE ONBOARDING HEALTH CHECK REPORT")
            print("=" * 60)
            print(f"Timestamp: {report['timestamp']}")
            print(f"Overall Status: {report['overall_status']}")
            print(f"System Uptime: {report['system_uptime']}")
            print()

            print("SUMMARY:")
            print(f"  Total Checks: {report['summary']['total_checks']}")
            print(f"  OK: {report['summary']['ok_count']}")
            print(f"  Warnings: {report['summary']['warning_count']}")
            print(f"  Errors: {report['summary']['error_count']}")
            print(f"  Info: {report['summary']['info_count']}")
            print()

            print("DETAILED RESULTS:")
            for check in report["checks"]:
                status_icon = {
                    "OK": "✅",
                    "WARNING": "⚠️",
                    "ERROR": "❌",
                    "INFO": "ℹ️",
                }.get(check["status"], "❓")

                print(f"{status_icon} {check['name']}")
                print(f"   Status: {check['status']}")
                print(f"   Message: {check['message']}")
                if check["details"]:
                    print(f"   Details: {json.dumps(check['details'], indent=6)}")
                if check["recommendations"]:
                    print(f"   Recommendations:")
                    for rec in check["recommendations"]:
                        print(f"     • {rec}")
                print()

            if report["recommendations"]:
                print("GENERAL RECOMMENDATIONS:")
                for rec in report["recommendations"]:
                    print(f"  • {rec}")
                print()

            if report["quick_fixes"]:
                print("QUICK FIXES:")
                for fix in report["quick_fixes"]:
                    print(f"  • {fix}")
                print()

            print("=" * 60)

    def run_continuous_monitoring(self):
        """Run continuous monitoring"""
        self.log("Starting continuous monitoring...")

        while True:
            try:
                self.run_all_checks()
                self.print_report()

                # Save report to file
                report = self.generate_user_report()
                with open("onboarding_health_report.json", "w") as f:
                    json.dump(report, f, indent=2, default=str)

                if not self.continuous:
                    break

                self.log(f"Sleeping for {CHECK_INTERVAL} seconds...")
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                self.log("Continuous monitoring stopped by user")
                break
            except Exception as e:
                self.log(f"Continuous monitoring error: {str(e)}", "ERROR")
                time.sleep(60)  # Wait before retrying


def main():
    import argparse

    # Global variable for check interval
    global CHECK_INTERVAL
    global API_BASE_URL

    parser = argparse.ArgumentParser(description="Proactive Onboarding Health Check")
    parser.add_argument(
        "--continuous", "-c", action="store_true", help="Run continuous monitoring"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--format", "-f", choices=["text", "json"], default="text", help="Output format"
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=CHECK_INTERVAL,
        help="Check interval in seconds (continuous mode)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="Override API base URL (default: http://api:8000)",
    )

    args = parser.parse_args()

    # Update check interval if specified
    CHECK_INTERVAL = args.interval
    if args.api_url:
        API_BASE_URL = args.api_url

    # Initialize health checker
    checker = ProactiveOnboardingHealthCheck(
        continuous=args.continuous, verbose=args.verbose
    )

    if args.continuous:
        checker.run_continuous_monitoring()
    else:
        checker.run_all_checks()
        checker.print_report(args.format)


if __name__ == "__main__":
    main()
