# External/Partner Onboarding

Welcome, external collaborator or partner! This guide will help you get started quickly and use the project's essential features via the public API.

## 🚀 Quick Start (Recommended)

### Option 1: Automated Script (Easiest)
Download and run our automated onboarding script:

```bash
# Download the script
curl -O https://your-ai-ide-api.example.com/onboarding/scripts/onboard_external.sh
chmod +x onboard_external.sh

# Run the script
./onboard_external.sh
```

The script will:
- ✅ Test API connectivity
- ✅ Initialize your project and team
- ✅ Generate API tokens with proper permissions
- ✅ Test the memory API functionality
- ✅ Create configuration files (`.env`, `.apitoken`, `.api_info_capture`)
- ✅ Provide example usage

**🤖 LLM Access**: If you choose to generate an admin token, the script will automatically enable LLM (Large Language Model) access for your project, which is required for AI-powered memory features like semantic search and intelligent memory analysis.

**🔄 RabbitMQ Workers**: The script can optionally set up RabbitMQ workers for background job processing, including **real implementations** for:
- **Git History Analysis**: Analyze your project's git history and create memory nodes
- **Memory Cleanup**: Remove stale or duplicate memory nodes automatically  
- **Memory Enrichment**: Add tags and categories to memory nodes
- **Memory Similarity**: Detect and handle similar content
- **Progress Reports**: Track development progress automatically
- **Maintenance Tasks**: Run system health checks and maintenance
- **Custom Background Jobs**: Process your own custom background tasks

**🎯 Real Worker Implementations**: Unlike basic templates, the onboarding script provides **fully functional worker implementations** that can:
- Connect to your AI IDE API memory system
- Process git history analysis with real git commands
- Clean up memory nodes based on age and relevance
- Enrich memory nodes with automatic tagging
- Detect similar content using content analysis
- Create progress reports from git activity
- Run maintenance tasks and health checks

### Option 2: Manual API Flow
If you prefer manual setup, follow this corrected flow:

1. **Initialize Onboarding** (creates project/team and gets project_id):
   ```bash
   curl -X POST "https://your-ai-ide-api.example.com/onboarding/init" \
     -H "Content-Type: application/json" \
     -d '{
       "project_name": "your_project_name",
       "team_name": "your_team_name", 
       "path": "external_project",
       "user": "your_email@example.com"
     }'
   ```

2. **Generate API Token** (using the project_id from step 1):
   ```bash
   curl -X POST "https://your-ai-ide-api.example.com/admin/generate-token" \
     -H "Content-Type: application/json" \
     -d '{
       "description": "Token for your_project_name",
       "role": "user",
       "project_id": "PROJECT_ID_FROM_STEP_1",
       "user": "your_email@example.com"
     }'
   ```

3. **Test Memory API**:
   ```bash
   curl -X POST "https://your-ai-ide-api.example.com/memory/nodes" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     -d '{
       "namespace": "test_namespace",
       "content": "Hello, memory system!",
       "meta": "{\"tags\":[\"test\"],\"source\":\"external_user\"}"
     }'
   ```

## 📋 Track Onboarding Progress

- **List your onboarding checklist and status**:
  ```bash
  curl -X GET "https://your-ai-ide-api.example.com/onboarding/progress/your_project_name?path=external_project" \
    -H "Authorization: Bearer YOUR_TOKEN_HERE"
  ```

- **Mark steps as completed**:
  ```bash
  curl -X PATCH "https://your-ai-ide-api.example.com/onboarding/progress/PROGRESS_ID" \
    -H "Authorization: Bearer YOUR_TOKEN_HERE" \
    -H "Content-Type: application/json" \
    -d '{"completed": true}'
  ```

## 🔑 Essential API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/onboarding/init` | POST | Initialize onboarding journey (creates project/team) |
| `/admin/generate-token` | POST | Generate API tokens with project permissions |
| `/onboarding/progress/{project_name}` | GET | List onboarding steps and status |
| `/onboarding/progress/{progress_id}` | PATCH | Mark steps as completed |
| `/memory/nodes` | POST | Store memory nodes |
| `/memory/search` | POST | Search memory nodes |
| `/memory/nodes/{node_id}` | GET | Retrieve specific memory node |

## 🎯 Onboarding Checklist & Step Details

For a full description of each onboarding step, see:
- [External Project Onboarding User Story](docs/user_stories/external_project_onboarding.md)

This user story includes a detailed table describing each step and what is required.

## 🔧 Configuration Files Created

The onboarding script creates these files:

- **`.apitoken`** - Your API token for authentication
- **`.api_admin_token`** - Admin token (if requested)
- **`.env`** - Environment configuration
- **`.api_info_capture`** - Project and API information

## 🐛 Troubleshooting

### Common Issues

1. **"Cannot connect to API"**
   - Check the API URL is correct
   - Verify the API is running and accessible

2. **"Failed to initialize onboarding"**
   - Project/team name might already exist
   - Try with a different name or let the script suggest one

3. **"Failed to generate token"**
   - Make sure you completed onboarding/init first
   - Check that project_id is correct

4. **"401 Unauthorized"**
   - Verify your API token is correct
   - Check token hasn't expired

5. **"Memory API test failed"**
   - Check token permissions
   - Verify memory system is configured

### Getting Help

- **API Documentation**: Visit `https://your-ai-ide-api.example.com/docs`
- **Issue Tracker**: Report problems via the project's issue tracker
- **Contact**: Reach out to your integration lead

## 🤖 LLM (Large Language Model) Access

### What is LLM Access?
LLM access enables AI-powered features in the memory system, including:
- **Semantic Search**: Find memories based on meaning, not just keywords
- **Intelligent Analysis**: AI-powered insights and connections between memories
- **Smart Recommendations**: AI-suggested related memories and patterns
- **Natural Language Processing**: Better understanding of memory content

### How to Get LLM Access

#### Option 1: Automatic (Recommended)
The onboarding script automatically enables LLM access when you choose to generate an admin token:
```bash
./onboard_external.sh
# When prompted: "Would you like to generate an admin token as well? (y/n): y"
```

#### Option 2: Manual Enablement
If you need to enable LLM access later:

1. **Using Admin Token**:
   ```bash
   curl -X POST "https://your-ai-ide-api.example.com/memory/admin/project/llm-access" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "project_id": "YOUR_PROJECT_ID",
       "has_llm_access": true
     }'
   ```

2. **Using Makefile Target** (if available):
   ```bash
   make -f Makefile.ai-llm enable-llm-access PROJECT_ID=YOUR_PROJECT_ID ADMIN_TOKEN=YOUR_ADMIN_TOKEN
   ```

### Checking LLM Access Status

You can check if your project has LLM access:

```bash
# Check your token's LLM access
curl -X GET "https://your-ai-ide-api.example.com/protected" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response will show: "has_llm_access": true/false
```

### LLM Access Requirements

- **Admin Token**: Required to enable LLM access for a project
- **Project Association**: LLM access is granted at the project level
- **Token Permissions**: User tokens inherit LLM access from their project

### Troubleshooting LLM Access

**Error: "LLM access not available for this token or project"**
- Ensure your project has LLM access enabled
- Check that you're using a token associated with the correct project
- Verify the project is active and not archived

**Error: "403 Forbidden" when enabling LLM access**
- Make sure you're using an admin token
- Verify the project ID is correct
- Check that the admin token has the necessary permissions

## 🔄 RabbitMQ Workers for Background Processing

### What are RabbitMQ Workers?
RabbitMQ workers enable background job processing for your project, allowing you to:
- **Process memory updates** asynchronously
- **Analyze git history** automatically with real git commands
- **Generate progress reports** on schedule
- **Run maintenance tasks** in the background
- **Handle custom background jobs** for your specific needs

### How to Set Up RabbitMQ Workers

#### Option 1: Automated Setup (Recommended)
The onboarding script can automatically set up RabbitMQ workers:
```bash
# During onboarding, choose to set up RabbitMQ workers
./onboard_external.sh

# The script will create:
# - rabbitmq-workers/ directory with all worker files
# - docker-compose.yml for RabbitMQ and worker containers
# - Real worker implementations (not just templates)
# - Job publisher scripts for easy job submission
```

#### Option 2: Manual Setup
If you prefer manual setup:
```bash
# Create worker directory
mkdir rabbitmq-workers
cd rabbitmq-workers

# Download worker files from the API
curl -O https://your-ai-ide-api.example.com/onboarding/workers/main.py
curl -O https://your-ai-ide-api.example.com/onboarding/workers/publish_job.py
curl -O https://your-ai-ide-api.example.com/onboarding/workers/docker-compose.yml
curl -O https://your-ai-ide-api.example.com/onboarding/workers/requirements.txt

# Start the worker environment
docker-compose up -d
```

### Real Worker Implementations Available

#### 1. **Git History Analysis Worker**
**What it does**: Analyzes your project's git history and creates memory nodes
```bash
# Publish a git history analysis job
python publish_job.py --queue git.history.analysis --since "1 week ago" --max-commits 50 --create-memory --memory-namespace weekly_analysis

# The worker will:
# - Run 'git log' commands to get commit history
# - Analyze commit messages and metadata
# - Create memory nodes with analysis results
# - Tag nodes with relevant categories
```

#### 2. **Memory Cleanup Worker**
**What it does**: Removes stale or duplicate memory nodes
```bash
# Preview cleanup without applying changes
python publish_job.py --queue memory.cleanup --dry-run --age-days 180

# Apply cleanup (removes nodes older than 180 days)
python publish_job.py --queue memory.cleanup --age-days 180

# The worker will:
# - Scan all memory nodes
# - Identify stale nodes based on age
# - Remove duplicate or irrelevant content
# - Log all cleanup actions
```

#### 3. **Memory Enrichment Worker**
**What it does**: Adds tags and categories to memory nodes
```bash
# Enrich all nodes with tags
python publish_job.py --queue memory.enrichment --scope all

# Enrich only new nodes (without tags)
python publish_job.py --queue memory.enrichment --scope new

# Enrich specific namespace
python publish_job.py --queue memory.enrichment --scope namespace:docs

# The worker will:
# - Analyze memory node content
# - Add relevant tags (error, test, documentation, api, etc.)
# - Categorize nodes automatically
# - Improve searchability
```

#### 4. **Memory Similarity Worker**
**What it does**: Detects and handles similar content
```bash
# Find similar nodes (preview mode)
python publish_job.py --queue memory.similarity --scope all --dry-run

# Process similar nodes
python publish_job.py --queue memory.similarity --scope new

# The worker will:
# - Compare memory node content
# - Detect similar or duplicate content
# - Group similar nodes together
# - Suggest merging or linking
```

#### 5. **Progress Report Worker**
**What it does**: Tracks development progress automatically
```bash
# Generate progress report
python publish_job.py --queue progress.report

# The worker will:
# - Check recent git activity
# - Summarize commits and changes
# - Create progress report memory nodes
# - Track development milestones
```

#### 6. **Maintenance Worker**
**What it does**: Runs system health checks and maintenance
```bash
# Run health check
python publish_job.py --queue maintenance --task health_check

# Run cleanup task
python publish_job.py --queue maintenance --task cleanup_old_data --args '{"dry_run": true, "age_days": 180}'

# The worker will:
# - Check system health
# - Run maintenance tasks
# - Generate health reports
# - Alert on issues
```

### Worker Configuration

#### Environment Variables
The workers use these environment variables:
```bash
# Required
RABBITMQ_URL=amqp://user:password@rabbitmq:5672/
MEMORY_API_URL=http://your-ai-ide-api.example.com/memory
MEMORY_API_TOKEN=your_api_token_here

# Optional
AI_IDE_API_URL=http://your-ai-ide-api.example.com
```

#### Docker Compose Setup
The onboarding script creates a complete Docker environment:
```yaml
# rabbitmq-workers/docker-compose.yml
version: '3.8'
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: user
      RABBITMQ_DEFAULT_PASS: password
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

  worker:
    build: .
    depends_on:
      - rabbitmq
    environment:
      - RABBITMQ_URL=amqp://user:password@rabbitmq:5672/
      - MEMORY_API_URL=${MEMORY_API_URL}
      - MEMORY_API_TOKEN=${MEMORY_API_TOKEN}
    volumes:
      - .:/app
      - /var/run/docker.sock:/var/run/docker.sock  # For git access

volumes:
  rabbitmq_data:
```

### Usage Examples

#### Daily Workflow
```bash
# 1. Start workers
cd rabbitmq-workers
docker-compose up -d

# 2. Generate daily progress report
python publish_job.py --queue progress.report

# 3. Analyze recent git history
python publish_job.py --queue git.history.analysis --since "1 day ago" --create-memory --memory-namespace daily_analysis

# 4. Enrich new memory nodes
python publish_job.py --queue memory.enrichment --scope new
```

#### Weekly Maintenance
```bash
# 1. Preview cleanup
python publish_job.py --queue memory.cleanup --dry-run --age-days 180

# 2. Apply cleanup if preview looks good
python publish_job.py --queue memory.cleanup --age-days 180

# 3. Find and handle similar content
python publish_job.py --queue memory.similarity --scope all --dry-run

# 4. Run health check
python publish_job.py --queue maintenance --task health_check
```

#### Custom Analysis
```bash
# Analyze specific time period
python publish_job.py --queue git.history.analysis --since "2024-01-01" --until "2024-01-31" --create-memory --memory-namespace sprint_analysis

# Enrich specific namespace
python publish_job.py --queue memory.enrichment --scope namespace:documentation

# Custom maintenance task
python publish_job.py --queue maintenance --task custom_analysis --args '{"data": {"type": "performance", "scope": "recent"}}'
```

### Monitoring and Management

#### Check Worker Status
```bash
# View worker logs
docker-compose logs -f worker

# Check RabbitMQ management interface
# Open http://localhost:15672 (user: user, password: password)

# Check queue status
docker-compose exec rabbitmq rabbitmqctl list_queues
```

#### Troubleshooting
```bash
# Restart workers
docker-compose restart worker

# Check worker health
python publish_job.py --queue maintenance --task health_check

# Clear stuck jobs
docker-compose exec rabbitmq rabbitmqctl purge_queue memory.cleanup
docker-compose exec rabbitmq rabbitmqctl purge_queue git.history.analysis
```

### Integration with Your Project

#### Git Repository Access
The workers need access to your git repository:
```bash
# Mount your git repository
docker-compose run -v /path/to/your/repo:/app/repo worker

# Or use git remote access
git remote add origin https://github.com/your-username/your-repo.git
```

#### Memory API Integration
Workers automatically integrate with your AI IDE memory system:
- **Authentication**: Uses your API token for all operations
- **Namespaces**: Organizes memory nodes by project/context
- **Tags**: Automatically tags content for better organization
- **Categories**: Categorizes content for improved searchability

#### Scheduled Jobs
Set up cron jobs for automated processing:
```bash
# Daily at 6 AM - Progress report
0 6 * * * cd /path/to/rabbitmq-workers && python publish_job.py --queue progress.report

# Weekly on Monday - Git analysis
0 7 * * 1 cd /path/to/rabbitmq-workers && python publish_job.py --queue git.history.analysis --since "1 week ago" --create-memory

# Monthly - Cleanup
0 2 1 * * cd /path/to/rabbitmq-workers && python publish_job.py --queue memory.cleanup --age-days 180
```

## 🚀 Next Steps

After successful onboarding:

1. **Explore the Memory API** - Store and search your project's knowledge
2. **Integrate with Your Tools** - Use the API in your development workflow
3. **Set Up Automation** - Create scripts for regular memory updates
4. **Monitor Usage** - Track your API usage and memory growth

---

**See also:** [Universal Onboarding](ONBOARDING.md) | [Internal Onboarding](ONBOARDING_INTERNAL.md)

## External Project Memory API Onboarding

If you want to use the AI IDE API as a hosted memory (vector) server for your own project (with no Docker or DB access required), follow this onboarding path:

- [External Project Memory API Onboarding →](docs/external/memory_api_onboarding.md)

This guide covers:
- How to get an API key
- How to create a namespace
- How to store and search memory via the API
- Example scripts and troubleshooting

For most external integrations, this is the recommended starting point. 