# 🚀 Quick Start: Portable RabbitMQ Setup

## What is this?

This guide helps you set up your own RabbitMQ system that can talk to the AI IDE API. Think of it as building your own "bot helpers" that can:

- 📝 Store information in the AI IDE's memory system
- 🔍 Analyze your git history automatically  
- 📊 Generate progress reports
- 🧹 Clean up old data
- ⚙️ Run maintenance tasks

## Who is this for?

- **Developers** who want to build automated helpers for their projects
- **Teams** who need background job processing
- **DevOps engineers** setting up monitoring and automation
- **Anyone** who wants to integrate with the AI IDE system

## 🎯 What you'll get

After following this guide, you'll have:

✅ **Your own RabbitMQ server** running in Docker  
✅ **A worker** that processes different types of jobs  
✅ **Scripts** to send jobs to the system  
✅ **Examples** showing how to use each feature  
✅ **Integration** with the AI IDE memory system  

## 🚀 Quick Setup (5 minutes)

### 1. Create your project
```bash
mkdir my-ai-bots
cd my-ai-bots
```

### 2. Copy the files
Follow the step-by-step guide in [portable_rabbitmq_setup.md](portable_rabbitmq_setup.md) to create all the necessary files.

### 3. Start the system
```bash
docker compose up -d
```

### 4. Test it works
```bash
# Check if everything is running
docker compose ps

# Look at the logs
docker compose logs worker

# Try an example
python examples/memory_update_example.py
```

## 📋 What can you do?

### Store Information in AI IDE Memory
```python
# Send a memory update
job = {
    "content": "User completed database setup",
    "meta": {
        "type": "onboarding_progress",
        "tags": ["onboarding", "progress"],
        "categories": ["user_activity"]
    }
}
publisher.publish_job("memory.update", job)
```

### Analyze Git History
```python
# Trigger git analysis
job = {
    "since": "1 week ago",
    "max_commits": 50,
    "create_memory_node": True,
    "memory_namespace": "weekly_analysis"
}
publisher.publish_job("git.history.analysis", job)
```

### Run Background Jobs
```python
# Any custom background task
job = {
    "job_type": "data_processing",
    "data": {"files": ["file1.txt", "file2.txt"]},
    "priority": "high"
}
publisher.publish_job("background.jobs", job)
```

## 🔧 Customization

### Add Your Own Job Types
1. Add a new method to the worker in `workers/main.py`
2. Add the queue name to the `queues` dictionary
3. Create your job publishing script

### Connect to Your Own APIs
1. Add your API credentials to `.env`
2. Modify the worker methods to call your APIs
3. Use the existing memory integration as a template

## 🛠️ Troubleshooting

### "Connection refused" error?
```bash
# Check if RabbitMQ is running
docker compose ps

# Restart the services
docker compose restart
```

### "Worker not processing jobs"?
```bash
# Check worker logs
docker compose logs worker

# Check queue status
docker compose exec rabbitmq rabbitmqctl list_queues
```

### "Memory API not working"?
```bash
# Check your API token
echo $MEMORY_API_TOKEN

# Test API connection
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:9103/health
```

## 📚 Learn More

- **Full Guide**: [portable_rabbitmq_setup.md](portable_rabbitmq_setup.md) - Complete step-by-step instructions
- **Message Schemas**: See all the different job types and their formats
- **Best Practices**: Security, monitoring, and performance tips
- **Examples**: Ready-to-use code examples for common tasks

## 🆘 Need Help?

1. **Check the logs**: `docker compose logs -f`
2. **RabbitMQ Management UI**: http://localhost:15672 (user/password)
3. **Worker logs**: `docker compose logs worker`
4. **API health**: `curl http://localhost:9103/health`

## 🎉 Success!

Once you have this running, you can:
- Build bots that automatically update the AI IDE memory
- Create automated git analysis for your projects  
- Set up background job processing for your applications
- Integrate with the AI IDE system for enhanced automation

---

**Remember**: Start simple, test often, and gradually add complexity as you get comfortable with the system! 