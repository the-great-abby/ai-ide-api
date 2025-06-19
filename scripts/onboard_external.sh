#!/bin/bash
# External Onboarding Script (Fixed Version)
# This script can be downloaded from the API for easy onboarding.
# Fixed to follow the correct flow: onboarding/init first, then token generation

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if jq is available
check_jq() {
    if ! command -v jq &> /dev/null; then
        print_warning "jq is not installed. Some features may not work properly."
        print_warning "Install jq with: brew install jq (macOS) or apt-get install jq (Ubuntu)"
        JQ_AVAILABLE=false
    else
        JQ_AVAILABLE=true
    fi
}

# Function to extract JSON values safely
extract_json_value() {
    local json="$1"
    local key="$2"
    
    if [ "$JQ_AVAILABLE" = true ]; then
        echo "$json" | jq -r ".$key" 2>/dev/null
    else
        # Fallback to grep/sed for basic extraction
        echo "$json" | grep -o "\"$key\"[ ]*:[ ]*\"[^\"]*\"" | head -1 | sed 's/.*"'"$key"'"[ ]*:[ ]*"\([^"]*\)".*/\1/'
    fi
}

# Function to suggest new name if project/team already exists
suggest_new_name() {
    local base_name="$1"
    local suffix=$(date +%s | tail -c 4)
    echo "${base_name}_${suffix}"
}

# Check for jq
check_jq

print_status "🏴‍☠️  AI IDE External Onboarding Script (Fixed Version)"
echo "=================================================="

# Get user input
read -p "Enter the API base URL (e.g., http://localhost:9103): " API_URL
API_URL=${API_URL%/}

read -p "Enter your project name: " PROJECT_NAME
read -p "Enter your team name: " TEAM_NAME
read -p "Enter user identifier (email or username): " USER
read -p "Enter onboarding path (e.g., external_project): " ONBOARDING_PATH

# Set defaults if empty
ONBOARDING_PATH=${ONBOARDING_PATH:-external_project}

print_status "Testing API connectivity..."
if ! curl -s "$API_URL/docs" > /dev/null; then
    print_error "Cannot connect to API at $API_URL. Please check the URL and try again."
    exit 1
fi
print_success "API is accessible!"

# Step 1: Initialize onboarding journey (create/get project and team)
print_status "Initializing onboarding journey..."
INIT_PAYLOAD="{\"project_name\": \"$PROJECT_NAME\", \"team_name\": \"$TEAM_NAME\", \"path\": \"$ONBOARDING_PATH\", \"user\": \"$USER\"}"

INIT_RESP=$(curl -s -X POST "$API_URL/onboarding/init" \
  -H 'Content-Type: application/json' \
  -d "$INIT_PAYLOAD")

# Check if initialization failed
if echo "$INIT_RESP" | grep -q 'error\|Error'; then
    print_error "Failed to initialize onboarding: $INIT_RESP"
    print_warning "This might be because the project/team name already exists."
    
    read -p "Would you like to try with a new project/team name? (y/n): " retry_choice
    if [[ $retry_choice =~ ^[Yy]$ ]]; then
        PROJECT_NAME=$(suggest_new_name "$PROJECT_NAME")
        TEAM_NAME=$(suggest_new_name "$TEAM_NAME")
        print_status "Trying with project: $PROJECT_NAME, team: $TEAM_NAME"
        
        INIT_PAYLOAD="{\"project_name\": \"$PROJECT_NAME\", \"team_name\": \"$TEAM_NAME\", \"path\": \"$ONBOARDING_PATH\", \"user\": \"$USER\"}"
        INIT_RESP=$(curl -s -X POST "$API_URL/onboarding/init" \
          -H 'Content-Type: application/json' \
          -d "$INIT_PAYLOAD")
        
        if echo "$INIT_RESP" | grep -q 'error\|Error'; then
            print_error "Still failed to initialize onboarding: $INIT_RESP"
            exit 1
        fi
    else
        print_error "Onboarding initialization failed. Exiting."
        exit 1
    fi
fi

print_success "Onboarding initialized successfully!"

# Extract project_id from response
PROJECT_ID=$(extract_json_value "$INIT_RESP" "project_id")
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "null" ]; then
    print_error "Onboarding response did not contain a project_id!"
    print_error "Response: $INIT_RESP"
    exit 1
fi

print_status "Project ID: $PROJECT_ID"

# Step 2: Generate user token associated with the project
print_status "Generating user token..."
TOKEN_PAYLOAD="{\"description\": \"Token for $PROJECT_NAME\", \"role\": \"user\", \"project_id\": \"$PROJECT_ID\", \"user\": \"$USER\"}"

TOKEN_RESP=$(curl -s -X POST "$API_URL/admin/generate-token" \
  -H 'Content-Type: application/json' \
  -d "$TOKEN_PAYLOAD")

# Check if token generation failed
if echo "$TOKEN_RESP" | grep -q 'error\|Error'; then
    print_error "Failed to generate user token: $TOKEN_RESP"
    
    # Check if it's a 401 error (token already exists)
    if echo "$TOKEN_RESP" | grep -q '401'; then
        print_warning "It looks like a user token for this project already exists."
        print_warning "You may need to use an existing token or contact an admin."
    fi
    exit 1
fi

TOKEN=$(extract_json_value "$TOKEN_RESP" "token")
if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    print_error "Token response did not contain a token!"
    print_error "Response: $TOKEN_RESP"
    exit 1
fi

# Save token to file
echo "$TOKEN" > .apitoken
print_success "User token generated: ${TOKEN:0:8}... (saved to .apitoken)"

# Step 3: Generate admin token using user token (optional)
read -p "Would you like to generate an admin token as well? (y/n): " admin_choice
if [[ $admin_choice =~ ^[Yy]$ ]]; then
    print_status "Generating admin token..."
    ADMIN_PAYLOAD="{\"description\": \"Admin token for $PROJECT_NAME\", \"role\": \"admin\", \"project_id\": \"$PROJECT_ID\", \"user\": \"$USER\"}"
    
    ADMIN_RESP=$(curl -s -X POST "$API_URL/admin/generate-token" \
      -H "Authorization: Bearer $TOKEN" \
      -H 'Content-Type: application/json' \
      -d "$ADMIN_PAYLOAD")
    
    if echo "$ADMIN_RESP" | grep -q 'error\|Error'; then
        print_warning "Failed to generate admin token: $ADMIN_RESP"
        print_warning "You can still use the user token for most operations."
    else
        ADMIN_TOKEN=$(extract_json_value "$ADMIN_RESP" "token")
        if [ -n "$ADMIN_TOKEN" ] && [ "$ADMIN_TOKEN" != "null" ]; then
            echo "$ADMIN_TOKEN" > .api_admin_token
            print_success "Admin token generated: ${ADMIN_TOKEN:0:8}... (saved to .api_admin_token)"
            
            # Step 3.5: Enable LLM access for the project
            print_status "Enabling LLM access for the project..."
            LLM_PAYLOAD="{\"project_id\": \"$PROJECT_ID\", \"has_llm_access\": true}"
            
            LLM_RESP=$(curl -s -X POST "$API_URL/memory/admin/project/llm-access" \
              -H "Authorization: Bearer $ADMIN_TOKEN" \
              -H 'Content-Type: application/json' \
              -d "$LLM_PAYLOAD")
            
            if echo "$LLM_RESP" | grep -q 'error\|Error'; then
                print_warning "Failed to enable LLM access: $LLM_RESP"
                print_warning "You may need to enable LLM access manually or contact an admin."
            else
                print_success "LLM access enabled successfully!"
                print_status "Your project now has access to AI-powered memory features."
            fi
        fi
    fi
else
    print_warning "No admin token generated. LLM access may not be available."
    print_warning "To enable LLM access later, you'll need an admin token or contact an admin."
fi

# Step 4: Test memory API
print_status "Testing memory API..."
TEST_PAYLOAD="{\"namespace\": \"onboarding_test\", \"content\": \"Test memory node from external onboarding script\", \"meta\": \"{\\\"tags\\\":[\\\"onboarding\\\",\\\"test\\\"],\\\"source\\\":\\\"external_script\\\"}\"}"

TEST_RESP=$(curl -s -X POST "$API_URL/memory/nodes" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "$TEST_PAYLOAD")

if echo "$TEST_RESP" | grep -q 'error\|Error'; then
    print_warning "Memory API test failed: $TEST_RESP"
    print_warning "This might be due to permissions or configuration issues."
else
    print_success "Memory API test successful!"
fi

# Step 5: Create .env file
print_status "Creating configuration files..."
ENV_CONTENT="# AI IDE API Configuration
AI_IDE_API_URL=$API_URL
MEMORY_API_URL=$API_URL/memory
MEMORY_API_TOKEN=$TOKEN

# Project Configuration
PROJECT_NAME=$PROJECT_NAME
TEAM_NAME=$TEAM_NAME
USER=$USER

# RabbitMQ Configuration (if using workers)
RABBITMQ_URL=amqp://user:password@localhost:5672/

# Worker Configuration
WORKER_LOG_LEVEL=INFO
WORKER_MAX_RETRIES=3
"

echo "$ENV_CONTENT" > .env
print_success "Configuration saved to .env"

# Step 6: Save API info
API_INFO="{\"api_token\": \"$TOKEN\", \"project_id\": \"$PROJECT_ID\", \"project_name\": \"$PROJECT_NAME\", \"team_name\": \"$TEAM_NAME\", \"user\": \"$USER\"}"
echo "$API_INFO" > .api_info_capture
print_success "API info saved to .api_info_capture"

print_success "🎉 Onboarding completed successfully!"
echo "=================================================="
echo "Next steps:"
echo "1. Your API token is saved in .apitoken"
echo "2. Configuration is saved in .env"
echo "3. API info is saved in .api_info_capture"
echo "4. Explore the API docs at $API_URL/docs"
echo "5. Follow the onboarding steps for '$ONBOARDING_PATH'"
echo "6. Use 'Authorization: Bearer <token>' in your API requests"
echo ""
echo "Example API call:"
echo "curl -X GET $API_URL/memory/nodes \\"
echo "  -H 'Authorization: Bearer ${TOKEN:0:8}...'"
echo ""

# Step 7: RabbitMQ Worker Setup (Optional)
read -p "Would you like to set up RabbitMQ workers for background job processing? (y/n): " rabbitmq_choice
if [[ $rabbitmq_choice =~ ^[Yy]$ ]]; then
    print_status "Setting up RabbitMQ worker templates..."
    
    # Create worker directory structure
    mkdir -p rabbitmq-workers/{workers,scripts,examples}
    print_success "Created rabbitmq-workers directory structure"
    
    # Download RabbitMQ setup documentation
    print_status "Downloading RabbitMQ setup guide..."
    curl -s "$API_URL/docs/rabbitmq-setup" > rabbitmq-workers/RABBITMQ_SETUP.md 2>/dev/null
    if [ $? -eq 0 ]; then
        print_success "Downloaded RabbitMQ setup guide to rabbitmq-workers/RABBITMQ_SETUP.md"
    else
        print_warning "Could not download RabbitMQ setup guide. You can find it at: $API_URL/docs/rabbitmq-setup"
    fi
    
    # Create basic docker-compose.yml for RabbitMQ
    print_status "Creating RabbitMQ docker-compose.yml..."
    DOCKER_COMPOSE_CONTENT="version: \"3.8\"
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - \"5672:5672\"      # AMQP protocol
      - \"15672:15672\"    # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: \${RABBITMQ_USER:-user}
      RABBITMQ_DEFAULT_PASS: \${RABBITMQ_PASS:-password}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: [\"CMD\", \"rabbitmq-diagnostics\", \"ping\"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    build:
      context: ./workers
      dockerfile: Dockerfile
    environment:
      - RABBITMQ_URL=amqp://\${RABBITMQ_USER:-user}:\${RABBITMQ_PASS:-password}@rabbitmq:5672/
      - MEMORY_API_URL=\${MEMORY_API_URL:-$API_URL/memory}
      - MEMORY_API_TOKEN=\${MEMORY_API_TOKEN:-$TOKEN}
      - AI_IDE_API_URL=\${AI_IDE_API_URL:-$API_URL}
    volumes:
      - ./workers:/app
      - ./examples:/app/examples
    depends_on:
      rabbitmq:
        condition: service_healthy
    restart: unless-stopped

volumes:
  rabbitmq_data:"
    
    echo "$DOCKER_COMPOSE_CONTENT" > rabbitmq-workers/docker-compose.yml
    print_success "Created rabbitmq-workers/docker-compose.yml"
    
    # Create worker requirements.txt
    print_status "Creating worker requirements.txt..."
    REQUIREMENTS_CONTENT="pika==1.3.1
requests==2.31.0
python-dotenv==1.0.0
aiohttp==3.8.5
asyncio-mqtt==0.11.1"
    
    echo "$REQUIREMENTS_CONTENT" > rabbitmq-workers/workers/requirements.txt
    print_success "Created rabbitmq-workers/workers/requirements.txt"
    
    # Create basic worker Dockerfile
    print_status "Creating worker Dockerfile..."
    DOCKERFILE_CONTENT="FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 worker && chown -R worker:worker /app
USER worker

CMD [\"python\", \"main.py\"]"
    
    echo "$DOCKERFILE_CONTENT" > rabbitmq-workers/workers/Dockerfile
    print_success "Created rabbitmq-workers/workers/Dockerfile"
    
    # Create basic worker main.py
    print_status "Creating basic worker main.py..."
    WORKER_MAIN_CONTENT="#!/usr/bin/env python3
\"\"\"
Enhanced RabbitMQ Worker for AI IDE Integration
Handles multiple queue types with real implementations.
\"\"\"

import os
import json
import asyncio
import logging
import pika
import time
import subprocess
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import aiohttp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIIDEWorker:
    def __init__(self):
        self.rabbitmq_url = os.getenv(\"RABBITMQ_URL\", \"amqp://user:password@rabbitmq:5672/\")
        self.memory_api_url = os.getenv(\"MEMORY_API_URL\", \"http://localhost:9103/memory\")
        self.memory_api_token = os.getenv(\"MEMORY_API_TOKEN\", \"\")
        self.ai_ide_api_url = os.getenv(\"AI_IDE_API_URL\", \"http://localhost:9103\")
        
        self.connection = None
        self.channel = None
        
        # Define supported queues and their handlers
        self.queues = {
            \"memory.update\": self.process_memory_update,
            \"memory.cleanup\": self.process_memory_cleanup,
            \"memory.enrichment\": self.process_memory_enrichment,
            \"memory.similarity\": self.process_memory_similarity,
            \"git.history.analysis\": self.process_git_history_analysis,
            \"progress.report\": self.process_progress_report,
            \"maintenance\": self.process_maintenance_task,
            \"background.jobs\": self.process_background_job,
        }

    def connect(self):
        \"\"\"Establish connection to RabbitMQ.\"\"\"
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare all queues as durable
            for queue in self.queues.keys():
                self.channel.queue_declare(queue=queue, durable=True)
                logger.info(f\"Declared queue: {queue}\")
                
            logger.info(\"Successfully connected to RabbitMQ\")
            
        except Exception as e:
            logger.error(f\"Failed to connect to RabbitMQ: {e}\")
            raise

    async def process_memory_update(self, body: Dict[str, Any]):
        \"\"\"Process memory update jobs.\"\"\"
        logger.info(f\"Processing memory update: {body}\")
        
        try:
            content = body.get(\"content\", \"\")
            meta = body.get(\"meta\", {})
            
            # Send to AI IDE memory API
            if self.memory_api_token:
                await self.send_to_memory_api(content, meta)
                
            logger.info(\"Memory update processed successfully\")
            
        except Exception as e:
            logger.error(f\"Error processing memory update: {e}\")

    async def process_memory_cleanup(self, body: Dict[str, Any]):
        \"\"\"Process memory cleanup jobs.\"\"\"
        logger.info(f\"Processing memory cleanup: {body}\")
        
        dry_run = body.get(\"dry_run\", True)
        age_days = body.get(\"age_days\", 180)
        
        try:
            # Get all memory nodes
            nodes = await self.get_memory_nodes()
            logger.info(f\"Loaded {len(nodes)} memory nodes\")
            
            # Find stale nodes (older than age_days)
            cutoff_time = time.time() - (age_days * 24 * 60 * 60)
            stale_nodes = [node for node in nodes if node.get('created_at', 0) < cutoff_time]
            
            logger.info(f\"Found {len(stale_nodes)} stale nodes (older than {age_days} days)\")
            
            if not dry_run:
                # Delete stale nodes
                for node in stale_nodes:
                    await self.delete_memory_node(node['id'])
                logger.info(f\"Deleted {len(stale_nodes)} stale nodes\")
            else:
                logger.info(f\"Dry run: Would delete {len(stale_nodes)} stale nodes\")
                
        except Exception as e:
            logger.error(f\"Error processing memory cleanup: {e}\")

    async def process_memory_enrichment(self, body: Dict[str, Any]):
        \"\"\"Process memory enrichment jobs.\"\"\"
        logger.info(f\"Processing memory enrichment: {body}\")
        
        scope = body.get(\"scope\", \"all\")
        dry_run = body.get(\"dry_run\", True)
        
        try:
            # Get nodes based on scope
            nodes = await self.get_memory_nodes()
            
            if scope == \"new\":
                # Only process nodes without tags
                nodes = [node for node in nodes if not node.get('tags')]
            elif scope.startswith(\"namespace:\"):
                namespace = scope.split(\":\", 1)[1]
                nodes = [node for node in nodes if node.get('namespace') == namespace]
            
            logger.info(f\"Processing {len(nodes)} nodes for enrichment\")
            
            # Simple enrichment: add basic tags based on content
            for node in nodes:
                content = node.get('content', '').lower()
                tags = []
                
                if 'error' in content:
                    tags.append('error')
                if 'test' in content:
                    tags.append('test')
                if 'doc' in content or 'readme' in content:
                    tags.append('documentation')
                if 'api' in content:
                    tags.append('api')
                
                if tags and not dry_run:
                    await self.update_memory_node(node['id'], {'tags': tags})
                    logger.info(f\"Enriched node {node['id']} with tags: {tags}\")
                elif tags:
                    logger.info(f\"Dry run: Would enrich node {node['id']} with tags: {tags}\")
                    
        except Exception as e:
            logger.error(f\"Error processing memory enrichment: {e}\")

    async def process_memory_similarity(self, body: Dict[str, Any]):
        \"\"\"Process memory similarity pruning jobs.\"\"\"
        logger.info(f\"Processing memory similarity: {body}\")
        
        scope = body.get(\"scope\", \"all\")
        vector_threshold = body.get(\"vector_similarity_threshold\", 0.92)
        content_threshold = body.get(\"content_similarity_threshold\", 0.85)
        
        try:
            # Get nodes based on scope
            nodes = await self.get_memory_nodes()
            
            if scope == \"new\":
                # Only process recent nodes
                cutoff_time = time.time() - (7 * 24 * 60 * 60)  # Last 7 days
                nodes = [node for node in nodes if node.get('created_at', 0) > cutoff_time]
            elif scope.startswith(\"namespace:\"):
                namespace = scope.split(\":\", 1)[1]
                nodes = [node for node in nodes if node.get('namespace') == namespace]
            
            logger.info(f\"Processing {len(nodes)} nodes for similarity analysis\")
            
            # Simple similarity detection based on content length and keywords
            similar_groups = []
            processed = set()
            
            for i, node1 in enumerate(nodes):
                if node1['id'] in processed:
                    continue
                    
                group = [node1]
                processed.add(node1['id'])
                
                for node2 in nodes[i+1:]:
                    if node2['id'] in processed:
                        continue
                        
                    # Simple similarity check
                    content1 = node1.get('content', '').lower()
                    content2 = node2.get('content', '').lower()
                    
                    # Check if contents are similar
                    if len(content1) > 50 and len(content2) > 50:
                        # Simple keyword overlap
                        words1 = set(content1.split())
                        words2 = set(content2.split())
                        overlap = len(words1.intersection(words2)) / len(words1.union(words2))
                        
                        if overlap > content_threshold:
                            group.append(node2)
                            processed.add(node2['id'])
                
                if len(group) > 1:
                    similar_groups.append(group)
            
            logger.info(f\"Found {len(similar_groups)} groups of similar nodes\")
            
            # Process similar groups
            for group in similar_groups:
                logger.info(f\"Similar group: {[node['id'] for node in group]}\")
                
        except Exception as e:
            logger.error(f\"Error processing memory similarity: {e}\")

    async def process_git_history_analysis(self, body: Dict[str, Any]):
        \"\"\"Process git history analysis jobs.\"\"\"
        logger.info(f\"Processing git history analysis: {body}\")
        
        since = body.get(\"since\", \"1 week ago\")
        max_commits = body.get(\"max_commits\", 20)
        create_memory = body.get(\"create_memory_node\", False)
        memory_namespace = body.get(\"memory_namespace\", \"git_history\")
        memory_tags = body.get(\"memory_tags\", [])
        
        try:
            # Get git log
            cmd = [\"git\", \"log\", \"--since\", since, \"--max-count\", str(max_commits), \"--pretty=format:%H|%an|%ad|%s\", \"--date=short\"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f\"Git command failed: {result.stderr}\")
                return
            
            commits = []
            for line in result.stdout.strip().split('\\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
            
            logger.info(f\"Found {len(commits)} commits since {since}\")
            
            # Create analysis summary
            if commits:
                summary = f\"Git history analysis: {len(commits)} commits since {since}\\n\\n\"
                summary += \"Recent commits:\\n\"
                for commit in commits[:5]:  # Show first 5 commits
                    summary += f\"- {commit['date']}: {commit['message']} (by {commit['author']})\\n\"
                
                if create_memory and self.memory_api_token:
                    meta = {
                        'type': 'git_history_analysis',
                        'since': since,
                        'max_commits': max_commits,
                        'commits_analyzed': len(commits),
                        'tags': memory_tags + ['git-history', 'analysis'],
                        'categories': ['development', 'code-analysis']
                    }
                    
                    await self.send_to_memory_api(summary, meta, memory_namespace)
                    logger.info(f\"Created memory node for git analysis\")
                
                logger.info(f\"Git history analysis completed: {len(commits)} commits analyzed\")
            else:
                logger.info(f\"No commits found since {since}\")
                
        except Exception as e:
            logger.error(f\"Error processing git history analysis: {e}\")

    async def process_progress_report(self, body: Dict[str, Any]):
        \"\"\"Process progress report jobs.\"\"\"
        logger.info(f\"Processing progress report: {body}\")
        
        try:
            # Get recent git activity
            cmd = [\"git\", \"log\", \"--since\", \"1 day ago\", \"--pretty=format:%s\", \"--oneline\"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip().split('\\n')
                summary = f\"Progress Report - Last 24 hours\\n\\n{len(commits)} commits:\\n\"
                summary += \"\\n\".join([f\"- {commit}\" for commit in commits[:10]])  # Show first 10
                
                if self.memory_api_token:
                    meta = {
                        'type': 'progress_report',
                        'source': 'external_worker',
                        'commits_count': len(commits),
                        'tags': ['progress', 'daily', 'automated'],
                        'categories': ['development', 'tracking']
                    }
                    
                    await self.send_to_memory_api(summary, meta, 'progress_reports')
                    logger.info(f\"Created progress report memory node\")
            else:
                logger.info(\"No recent commits found for progress report\")
                
        except Exception as e:
            logger.error(f\"Error processing progress report: {e}\")

    async def process_maintenance_task(self, body: Dict[str, Any]):
        \"\"\"Process maintenance tasks.\"\"\"
        logger.info(f\"Processing maintenance task: {body}\")
        
        task = body.get(\"task\", \"\")
        args = body.get(\"args\", {})
        
        try:
            if task == \"health_check\":
                # Perform health check
                health_status = await self.perform_health_check()
                logger.info(f\"Health check completed: {health_status}\")
            elif task == \"cleanup_old_data\":
                # Clean up old data
                await self.process_memory_cleanup({\"dry_run\": args.get(\"dry_run\", True), \"age_days\": args.get(\"age_days\", 180)})
            else:
                logger.info(f\"Unknown maintenance task: {task}\")
                
        except Exception as e:
            logger.error(f\"Error processing maintenance task: {e}\")

    async def process_background_job(self, body: Dict[str, Any]):
        \"\"\"Process general background jobs.\"\"\"
        logger.info(f\"Processing background job: {body}\")
        
        job_type = body.get(\"job_type\", \"\")
        
        try:
            if job_type == \"custom_analysis\":
                # Custom analysis logic
                logger.info(f\"Running custom analysis: {body.get('data', {})}\")
            else:
                logger.info(f\"Unknown background job type: {job_type}\")
                
        except Exception as e:
            logger.error(f\"Error processing background job: {e}\")

    async def send_to_memory_api(self, content: str, meta: Dict[str, Any], namespace: str = \"default\"):
        \"\"\"Send data to AI IDE memory API.\"\"\"
        try:
            headers = {
                \"Authorization\": f\"Bearer {self.memory_api_token}\",
                \"Content-Type\": \"application/json\"
            }
            
            payload = {
                \"namespace\": namespace,
                \"content\": content,
                \"meta\": json.dumps(meta)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f\"{self.memory_api_url}/nodes\",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f\"Memory node created: {result.get('id')}\")
                        return result.get('id')
                    else:
                        logger.error(f\"Failed to create memory node: {response.status}\")
                        return None
                        
        except Exception as e:
            logger.error(f\"Error sending to memory API: {e}\")
            return None

    async def get_memory_nodes(self) -> List[Dict[str, Any]]:
        \"\"\"Get all memory nodes from the API.\"\"\"
        try:
            headers = {\"Authorization\": f\"Bearer {self.memory_api_token}\"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f\"{self.memory_api_url}/nodes\", headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f\"Failed to get memory nodes: {response.status}\")
                        return []
        except Exception as e:
            logger.error(f\"Error getting memory nodes: {e}\")
            return []

    async def delete_memory_node(self, node_id: str):
        \"\"\"Delete a memory node.\"\"\"
        try:
            headers = {\"Authorization\": f\"Bearer {self.memory_api_token}\"}
            async with aiohttp.ClientSession() as session:
                async with session.delete(f\"{self.memory_api_url}/nodes/{node_id}\", headers=headers) as response:
                    if response.status == 200:
                        logger.info(f\"Deleted memory node: {node_id}\")
                    else:
                        logger.error(f\"Failed to delete memory node {node_id}: {response.status}\")
        except Exception as e:
            logger.error(f\"Error deleting memory node {node_id}: {e}\")

    async def update_memory_node(self, node_id: str, updates: Dict[str, Any]):
        \"\"\"Update a memory node.\"\"\"
        try:
            headers = {\"Authorization\": f\"Bearer {self.memory_api_token}\"}
            async with aiohttp.ClientSession() as session:
                async with session.patch(f\"{self.memory_api_url}/nodes/{node_id}\", headers=headers, json=updates) as response:
                    if response.status == 200:
                        logger.info(f\"Updated memory node: {node_id}\")
                    else:
                        logger.error(f\"Failed to update memory node {node_id}: {response.status}\")
        except Exception as e:
            logger.error(f\"Error updating memory node {node_id}: {e}\")

    async def perform_health_check(self) -> Dict[str, Any]:
        \"\"\"Perform a health check of the system.\"\"\"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f\"{self.ai_ide_api_url}/health\") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {\"status\": \"unhealthy\", \"error\": f\"HTTP {response.status}\"}
        except Exception as e:
            return {\"status\": \"unhealthy\", \"error\": str(e)}

    def start(self):
        \"\"\"Start the worker and begin processing messages.\"\"\"
        try:
            self.connect()
            logger.info(\"Worker started, waiting for messages...\")
            
            # Set up consumers for all queues
            for queue, callback in self.queues.items():
                self.channel.basic_consume(
                    queue=queue,
                    on_message_callback=lambda ch, method, props, body: asyncio.run(
                        self._handle_message(callback, body)
                    ),
                    auto_ack=True
                )
                logger.info(f\"Listening on queue: {queue}\")
            
            # Start consuming messages
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info(\"Shutting down worker...\")
            self._cleanup()
        except Exception as e:
            logger.error(f\"Worker error: {e}\")
            self._cleanup()

    async def _handle_message(self, callback, body):
        \"\"\"Handle incoming messages with error handling.\"\"\"
        try:
            message = json.loads(body)
            await callback(message)
        except json.JSONDecodeError as e:
            logger.error(f\"Invalid JSON in message: {e}\")
        except Exception as e:
            logger.error(f\"Error processing message: {e}\")

    def _cleanup(self):
        \"\"\"Clean up resources.\"\"\"
        if self.connection and not self.connection.is_closed:
            self.connection.close()

if __name__ == \"__main__\":
    worker = AIIDEWorker()
    worker.start()"
    
    echo "$WORKER_MAIN_CONTENT" > rabbitmq-workers/workers/main.py
    chmod +x rabbitmq-workers/workers/main.py
    print_success "Created rabbitmq-workers/workers/main.py"
    
    # Create job publisher script
    print_status "Creating job publisher script..."
    JOB_PUBLISHER_CONTENT="#!/usr/bin/env python3
\"\"\"
Job Publisher for AI IDE RabbitMQ Integration
Publishes jobs to various RabbitMQ queues for processing.
\"\"\"

import argparse
import json
import asyncio
import os
import pika
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class JobPublisher:
    def __init__(self):
        self.rabbitmq_url = os.getenv(\"RABBITMQ_URL\", \"amqp://user:password@rabbitmq:5672/\")
        self.connection = None
        self.channel = None

    def connect(self):
        \"\"\"Establish connection to RabbitMQ.\"\"\"
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare all queues as durable
            queues = [
                \"memory.update\",
                \"memory.cleanup\",
                \"memory.enrichment\",
                \"memory.similarity\",
                \"git.history.analysis\",
                \"progress.report\",
                \"maintenance\",
                \"background.jobs\"
            ]
            
            for queue in queues:
                self.channel.queue_declare(queue=queue, durable=True)
                
            print(f\"Connected to RabbitMQ and declared {len(queues)} queues\")
            
        except Exception as e:
            print(f\"Failed to connect to RabbitMQ: {e}\")
            raise

    def publish_job(self, queue: str, job_data: Dict[str, Any]):
        \"\"\"Publish a job to a specific queue.\"\"\"
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=json.dumps(job_data),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            print(f\"Published job to {queue}: {json.dumps(job_data, indent=2)}\")
            return True
        except Exception as e:
            print(f\"Failed to publish job to {queue}: {e}\")
            return False

    def publish_git_history_job(self, since: str, max_commits: int = 20, create_memory: bool = True, 
                               memory_namespace: str = \"git_history\", memory_tags: list = None):
        \"\"\"Publish a git history analysis job.\"\"\"
        job_data = {
            \"since\": since,
            \"max_commits\": max_commits,
            \"create_memory_node\": create_memory,
            \"memory_namespace\": memory_namespace,
            \"memory_tags\": memory_tags or [\"git-history\", \"analysis\"],
            \"include_diff\": False,
            \"summarize\": True,
            \"output_format\": \"summary\"
        }
        return self.publish_job(\"git.history.analysis\", job_data)

    def publish_memory_cleanup_job(self, dry_run: bool = True, age_days: int = 180):
        \"\"\"Publish a memory cleanup job.\"\"\"
        job_data = {
            \"dry_run\": dry_run,
            \"age_days\": age_days
        }
        return self.publish_job(\"memory.cleanup\", job_data)

    def publish_memory_enrichment_job(self, scope: str = \"all\", dry_run: bool = True):
        \"\"\"Publish a memory enrichment job.\"\"\"
        job_data = {
            \"scope\": scope,
            \"dry_run\": dry_run,
            \"similarity_threshold\": 0.85,
            \"max_tags\": 10
        }
        return self.publish_job(\"memory.enrichment\", job_data)

    def publish_memory_similarity_job(self, scope: str = \"all\", dry_run: bool = True):
        \"\"\"Publish a memory similarity pruning job.\"\"\"
        job_data = {
            \"scope\": scope,
            \"dry_run\": dry_run,
            \"vector_similarity_threshold\": 0.92,
            \"content_similarity_threshold\": 0.85,
            \"tag_overlap_threshold\": 0.80
        }
        return self.publish_job(\"memory.similarity\", job_data)

    def publish_progress_report_job(self):
        \"\"\"Publish a progress report job.\"\"\"
        job_data = {
            \"source\": \"external_worker\",
            \"include_git_diff\": True,
            \"create_memory_node\": True
        }
        return self.publish_job(\"progress.report\", job_data)

    def publish_maintenance_job(self, task: str, args: Dict[str, Any] = None):
        \"\"\"Publish a maintenance job.\"\"\"
        job_data = {
            \"task\": task,
            \"args\": args or {}
        }
        return self.publish_job(\"maintenance\", job_data)

    def publish_custom_job(self, queue: str, job_data: Dict[str, Any]):
        \"\"\"Publish a custom job to any queue.\"\"\"
        return self.publish_job(queue, job_data)

    def close(self):
        \"\"\"Close the connection.\"\"\"
        if self.connection and not self.connection.is_closed:
            self.connection.close()

def main():
    parser = argparse.ArgumentParser(description=\"Publish jobs to RabbitMQ queues\")
    parser.add_argument(\"--queue\", required=True, 
                       choices=[\"git.history.analysis\", \"memory.cleanup\", \"memory.enrichment\", 
                               \"memory.similarity\", \"progress.report\", \"maintenance\", \"custom\"],
                       help=\"Queue to publish to\")
    
    # Git history specific arguments
    parser.add_argument(\"--since\", help=\"Time period for git analysis (e.g., '1 week ago')\")
    parser.add_argument(\"--max-commits\", type=int, default=20, help=\"Maximum commits to analyze\")
    parser.add_argument(\"--create-memory\", action=\"store_true\", default=True, help=\"Create memory node\")
    parser.add_argument(\"--memory-namespace\", default=\"git_history\", help=\"Memory namespace\")
    parser.add_argument(\"--memory-tags\", nargs=\"*\", default=[], help=\"Memory tags\")
    
    # Memory cleanup specific arguments
    parser.add_argument(\"--dry-run\", action=\"store_true\", default=True, help=\"Dry run mode\")
    parser.add_argument(\"--age-days\", type=int, default=180, help=\"Age threshold for cleanup\")
    
    # Memory enrichment/similarity specific arguments
    parser.add_argument(\"--scope\", default=\"all\", help=\"Scope for processing (all, new, namespace:xyz)\")
    
    # Maintenance specific arguments
    parser.add_argument(\"--task\", help=\"Maintenance task to run\")
    parser.add_argument(\"--args\", help=\"JSON string of task arguments\")
    
    # Custom job arguments
    parser.add_argument(\"--job-data\", help=\"JSON string of custom job data\")
    
    args = parser.parse_args()
    
    publisher = JobPublisher()
    
    try:
        publisher.connect()
        
        if args.queue == \"git.history.analysis\":
            if not args.since:
                print(\"Error: --since is required for git history analysis\")
                return
            publisher.publish_git_history_job(
                since=args.since,
                max_commits=args.max_commits,
                create_memory=args.create_memory,
                memory_namespace=args.memory_namespace,
                memory_tags=args.memory_tags
            )
            
        elif args.queue == \"memory.cleanup\":
            publisher.publish_memory_cleanup_job(
                dry_run=args.dry_run,
                age_days=args.age_days
            )
            
        elif args.queue == \"memory.enrichment\":
            publisher.publish_memory_enrichment_job(
                scope=args.scope,
                dry_run=args.dry_run
            )
            
        elif args.queue == \"memory.similarity\":
            publisher.publish_memory_similarity_job(
                scope=args.scope,
                dry_run=args.dry_run
            )
            
        elif args.queue == \"progress.report\":
            publisher.publish_progress_report_job()
            
        elif args.queue == \"maintenance\":
            if not args.task:
                print(\"Error: --task is required for maintenance jobs\")
                return
            task_args = json.loads(args.args) if args.args else {}
            publisher.publish_maintenance_job(args.task, task_args)
            
        elif args.queue == \"custom\":
            if not args.job_data:
                print(\"Error: --job-data is required for custom jobs\")
                return
            job_data = json.loads(args.job_data)
            # For custom jobs, you need to specify the queue in the job data
            queue = job_data.pop(\"queue\", \"background.jobs\")
            publisher.publish_custom_job(queue, job_data)
            
    finally:
        publisher.close()

if __name__ == \"__main__\":
    main()"
    
    echo "$JOB_PUBLISHER_CONTENT" > rabbitmq-workers/scripts/publish_job.py
    chmod +x rabbitmq-workers/scripts/publish_job.py
    print_success "Created rabbitmq-workers/scripts/publish_job.py"
    
    # Create README for RabbitMQ setup
    print_status "Creating RabbitMQ README..."
    RABBITMQ_README_CONTENT="# RabbitMQ Worker Setup

This directory contains everything you need to set up RabbitMQ workers for background job processing with the AI IDE API.

## Quick Start

1. **Start RabbitMQ and Worker:**
   \`\`\`bash
   cd rabbitmq-workers
   docker compose up -d
   \`\`\`

2. **Publish a Test Job:**
   \`\`\`bash
   python scripts/publish_job.py \\
     --queue memory.update \\
     --message '{\"content\": \"Test memory update\", \"meta\": {\"tags\": [\"test\"]}}'
   \`\`\`

3. **Monitor Jobs:**
   - RabbitMQ Management UI: http://localhost:15672 (user/password)
   - Worker logs: \`docker compose logs -f worker\`

## Available Queues

- \`memory.update\` - Update memory with new information
- \`memory.cleanup\` - Clean up old memory entries
- \`memory.enrichment\` - Enhance existing memory
- \`memory.similarity\` - Find and merge similar entries
- \`git.history.analysis\` - Analyze repository commits
- \`progress.report\` - Generate progress reports
- \`maintenance\` - Run maintenance tasks
- \`background.jobs\` - Custom background processing

## Configuration

Update the \`.env\` file in the parent directory with your API token and configuration.

## Documentation

- Complete setup guide: RABBITMQ_SETUP.md
- API documentation: $API_URL/docs
- Queue schemas: $API_URL/worker-queues

## Examples

See the \`examples/\` directory for more usage examples.
"
    
    echo "$RABBITMQ_README_CONTENT" > rabbitmq-workers/README.md
    print_success "Created rabbitmq-workers/README.md"
    
    print_success "🎉 RabbitMQ worker setup completed!"
    echo ""
    echo "RabbitMQ Worker Setup Summary:"
    echo "✅ Created rabbitmq-workers/ directory"
    echo "✅ Downloaded setup documentation"
    echo "✅ Created docker-compose.yml for RabbitMQ"
    echo "✅ Created worker Dockerfile and requirements.txt"
    echo "✅ Created basic worker main.py"
    echo "✅ Created job publisher script"
    echo "✅ Created README with quick start guide"
    echo ""
    echo "To start using RabbitMQ workers:"
    echo "1. cd rabbitmq-workers"
    echo "2. docker compose up -d"
    echo "3. python scripts/publish_job.py --queue memory.update --message '{\"content\": \"test\"}'"
    echo ""
    echo "RabbitMQ Management UI: http://localhost:15672 (user/password)"
else
    print_status "Skipping RabbitMQ worker setup."
    print_status "You can set up RabbitMQ workers later by visiting: $API_URL/docs/rabbitmq-setup"
fi

echo "Happy coding! 🚀" 