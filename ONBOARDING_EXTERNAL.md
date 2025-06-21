# External/Partner Onboarding

Welcome, external collaborator or partner! This guide will help you get started quickly and use the project's essential features via the public API.

## 🚀 Quick Start (Recommended)

### Option 1: Automated Onboarding Script (Easiest)
Download and run our automated onboarding script:

```bash
# Download the onboarding package
curl http://localhost:9103/external/onboarding/download/all \
  -o ai-ide-api-onboarding.zip

# Extract and run
unzip ai-ide-api-onboarding.zip
chmod +x onboard_external.sh
./onboard_external.sh
```

The script will:
- ✅ Test API connectivity
- ✅ Create your project and team
- ✅ Generate API tokens with proper permissions
- ✅ Create a focused, project-specific Makefile
- ✅ Test authentication and basic operations
- ✅ Provide simple usage instructions

### Option 2: Manual Setup
If you prefer manual setup:

1. **Download Onboarding Scripts**:
   ```bash
   curl http://localhost:9103/external/onboarding/download/scripts \
     -o ai-ide-api-scripts.zip
   unzip ai-ide-api-scripts.zip
   ```

2. **Run the Python Onboarding Script**:
   ```bash
   python onboard_external_updated.py --api-base http://localhost:9103 --project-name "your_project"
   ```

3. **Use the Generated Makefile**:
   ```bash
   make -f Makefile.external test-connection
   make -f Makefile.external help
   ```

## 📋 What You Get

### Generated Files
- **`Makefile.external`** - Focused Makefile with essential operations (~50 lines)
- **`USAGE.md`** - Simple usage guide
- **`.apitoken`** - Your API token for authentication
- **`.api_admin_token`** - Admin token (if admin access requested)
- **`.project`** - Project name for reference
- **`.teamname`** - Team name for reference
- **`.env`** - Environment configuration

### Essential Makefile Operations
```bash
# Test your connection and authentication
make -f Makefile.external test-connection

# Check if your project has LLM access enabled
make -f Makefile.external check-llm-access

# Get instructions for requesting LLM access
make -f Makefile.external request-llm-access

# Check API health
make -f Makefile.external health

# Show all available commands
make -f Makefile.external help
```

## 🤖 LLM (Large Language Model) Access

### What is LLM Access?
LLM access enables AI-powered features in the memory system:
- **Semantic Search**: Find memories based on meaning, not just keywords
- **Intelligent Analysis**: AI-powered insights and connections
- **Smart Recommendations**: AI-suggested related memories
- **Natural Language Processing**: Better understanding of content

### How to Get LLM Access

#### Option 1: Request via Makefile
```bash
# Check current status
make -f Makefile.external check-llm-access

# Get instructions for requesting access
make -f Makefile.external request-llm-access
```

#### Option 2: Contact Administrator
1. Get your project ID from the Makefile instructions
2. Contact the AI IDE API administrator
3. Request LLM access to be enabled for your project

### Checking LLM Access Status
```bash
# Check your token's LLM access
curl -X GET "http://localhost:9103/protected" \
  -H "Authorization: Bearer $(cat .apitoken)"

# Response will show: "has_llm_access": true/false
```

## 🔐 Admin Access for External Projects

### What is Admin Access?
Admin access allows you to:
- **Enable/Disable LLM Access** for your project
- **Generate New Tokens** for team members
- **Manage Project Settings** directly
- **View Project Information** and statistics

### How to Get Admin Access

#### Option 1: During Onboarding (Recommended)
When running the onboarding script, choose to generate an admin token:
```bash
./onboard_external.sh

# When prompted: "Do you need admin access for this project? (y/n): y"
# This will generate both .apitoken and .api_admin_token
```

#### Option 2: Generate Admin Token Later
If you already have a user token, you can generate an admin token:
```bash
# Using the admin script
python scripts/admin_external_projects.py generate-token <project_id> \
  --role admin \
  --admin-token $(cat .apitoken) \
  --api-base http://localhost:9103

# Save the admin token
echo "your-admin-token" > .api_admin_token
```

### Using Admin Commands

Once you have an admin token (`.api_admin_token` file), you can use admin commands:

```bash
# Enable LLM access for your project
make -f Makefile.external admin-enable-llm

# Disable LLM access
make -f Makefile.external admin-disable-llm

# Generate new tokens for team members
make -f Makefile.external admin-generate-token DESCRIPTION="Team member token" ROLE=user

# View project information
make -f Makefile.external admin-project-info

# See all available admin commands
make -f Makefile.external help
```

### Admin vs User Tokens

- **User Token** (`.apitoken`): Basic API access for your project
- **Admin Token** (`.api_admin_token`): Full administrative access for your project

Both tokens are scoped to your specific project and user.

## 🔧 Custom Makefile Generation

For project-specific needs, generate a custom Makefile:

```bash
# Generate custom Makefile via API
curl -X POST "http://localhost:9103/external/onboarding/generate" \
  -H "Authorization: Bearer $(cat .apitoken)" \
  -H "Content-Type: application/json" \
  -d '{"api_base": "http://localhost:9103", "output_name": "Makefile.custom"}'

# Or use the generator script directly
python generate_external_makefile.py \
  --api-base http://localhost:9103 \
  --output Makefile.custom
```

## 📚 API Endpoints

### Onboarding Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/external/onboarding/files` | GET | List available onboarding files |
| `/external/onboarding/download/{type}` | GET | Download files (scripts, makefile, examples, all) |
| `/external/onboarding/generate` | POST | Generate custom Makefile |
| `/external/onboarding/quick-start` | GET | Get quick start guide |

### Essential API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/protected` | GET | Test authentication and get token info |
| `/health` | GET | Check API health |
| `/memory/admin/project/llm-access` | GET | Check LLM access status |

## 🎯 Simple Workflow

### 1. Initial Setup
```bash
# Download and run onboarding
curl http://localhost:9103/external/onboarding/download/all \
  -o ai-ide-api-onboarding.zip
unzip ai-ide-api-onboarding.zip
./onboard_external.sh
```

### 2. Test Your Setup
```bash
# Test connection and authentication
make -f Makefile.external test-connection

# Check LLM access
make -f Makefile.external check-llm-access
```

### 3. Start Using the API
```bash
# See all available commands
make -f Makefile.external help

# Check API health
make -f Makefile.external health
```

## 🐛 Troubleshooting

### Common Issues

1. **"Cannot connect to API"**
   - Check the API URL is correct
   - Verify the API is running and accessible

2. **"401 Unauthorized"**
   - Verify your API token is correct in `.apitoken`
   - Check token hasn't expired

3. **"Makefile.external not found"**
   - Run the onboarding script first
   - Or generate a custom Makefile via API

4. **"LLM access not available"**
   - Use `make -f Makefile.external request-llm-access` for instructions
   - Contact administrator to enable LLM access

### Getting Help

- **API Documentation**: Visit `http://localhost:9103/docs`
- **Quick Start Guide**: `GET /external/onboarding/quick-start`
- **File List**: `GET /external/onboarding/files`

## 🚀 Next Steps

After successful onboarding:

1. **Explore the Makefile** - Use `make -f Makefile.external help`
2. **Test Your Connection** - Use `make -f Makefile.external test-connection`
3. **Request LLM Access** - If needed, use `make -f Makefile.external request-llm-access`
4. **Integrate with Your Tools** - Use the API in your development workflow

## 📖 Additional Resources

- [External Project Onboarding User Story](docs/user_stories/external_onboarding_with_makefile.md)
- [API Authentication Guide](docs/onboarding/AUTHENTICATION_AUTHORIZATION.md)
- [Memory System Documentation](docs/onboarding/MEMORY_SYSTEM.md)

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