# User Story: Memory System Namespaces and Search Strategies

## Motivation
As a developer or AI assistant working with the AI IDE API, I want to understand the different memory namespaces and how to effectively search them using RAG (Retrieval-Augmented Generation) to find relevant information quickly and accurately.

## Actors
- Developers
- AI Assistants
- Project Teams
- Documentation Writers
- System Administrators

## Preconditions
- Access to the AI IDE API
- Authentication token (`.api_admin_token` or `.apitoken`)
- Makefile.ai available in your project
- Memory system populated with content

## Available Namespaces

### 1. **progress_reports** 📊
**Purpose:** Technical summaries of recent code changes, commit digests, and development activity

**Content Types:**
- Git diff summaries
- Code change explanations
- Technical analysis of commits
- Development workflow updates

**Effective Search Phrases:**
```bash
# Search for specific file changes
make -f Makefile.ai memory-rag-search QUERY="gitignore changes" NAMESPACE="progress_reports"

# Search for recent features
make -f Makefile.ai memory-rag-search QUERY="new features added" NAMESPACE="progress_reports"

# Search for bug fixes
make -f Makefile.ai memory-rag-search QUERY="bug fixes" NAMESPACE="progress_reports"

# Search for Docker changes
make -f Makefile.ai memory-rag-search QUERY="docker compose changes" NAMESPACE="progress_reports"

# Search for Makefile updates
make -f Makefile.ai memory-rag-search QUERY="Makefile updates" NAMESPACE="progress_reports"
```

### 2. **user_stories** 📖
**Purpose:** User stories documenting workflows, features, and processes

**Content Types:**
- Workflow documentation
- Feature descriptions
- Process guides
- Best practices

**Effective Search Phrases:**
```bash
# Search for rule-related user stories
make -f Makefile.ai memory-rag-search QUERY="user story rules" NAMESPACE="user_stories"

# Search for workflow documentation
make -f Makefile.ai memory-rag-search QUERY="workflow process" NAMESPACE="user_stories"

# Search for automation guides
make -f Makefile.ai memory-rag-search QUERY="automation workflow" NAMESPACE="user_stories"

# Search for submission processes
make -f Makefile.ai memory-rag-search QUERY="submission process" NAMESPACE="user_stories"
```

### 3. **daily_analysis** 📅
**Purpose:** Daily summaries of git history and development activity

**Content Types:**
- Daily commit summaries
- Development story progression
- Code change patterns
- Author activity

**Effective Search Phrases:**
```bash
# Search for daily development patterns
make -f Makefile.ai memory-rag-search QUERY="daily development activity" NAMESPACE="daily_analysis"

# Search for recent commits
make -f Makefile.ai memory-rag-search QUERY="recent commits" NAMESPACE="daily_analysis"

# Search for author activity
make -f Makefile.ai memory-rag-search QUERY="author contributions" NAMESPACE="daily_analysis"
```

### 4. **weekly_analysis** 📈
**Purpose:** Weekly retrospectives and development summaries

**Content Types:**
- Weekly development stories
- Sprint-like summaries
- Code evolution patterns
- Team activity overview

**Effective Search Phrases:**
```bash
# Search for weekly patterns
make -f Makefile.ai memory-rag-search QUERY="weekly development patterns" NAMESPACE="weekly_analysis"

# Search for sprint summaries
make -f Makefile.ai memory-rag-search QUERY="sprint summary" NAMESPACE="weekly_analysis"
```

### 5. **sprint_analysis** 🏃‍♂️
**Purpose:** Sprint-based development analysis and retrospectives

**Content Types:**
- Sprint development stories
- Feature completion summaries
- Team velocity insights
- Sprint retrospectives

**Effective Search Phrases:**
```bash
# Search for sprint activity
make -f Makefile.ai memory-rag-search QUERY="sprint development" NAMESPACE="sprint_analysis"

# Search for feature completion
make -f Makefile.ai memory-rag-search QUERY="feature completion" NAMESPACE="sprint_analysis"
```

### 6. **monthly_analysis** 📊
**Purpose:** Monthly development overviews and long-term patterns

**Content Types:**
- Monthly development stories
- Long-term code evolution
- Major milestone summaries
- Architecture changes

**Effective Search Phrases:**
```bash
# Search for monthly patterns
make -f Makefile.ai memory-rag-search QUERY="monthly development overview" NAMESPACE="monthly_analysis"

# Search for major changes
make -f Makefile.ai memory-rag-search QUERY="major changes" NAMESPACE="monthly_analysis"
```

### 7. **default** 🔧
**Purpose:** General system information and miscellaneous content

**Content Types:**
- System configuration
- General documentation
- Miscellaneous notes
- Default content

**Effective Search Phrases:**
```bash
# Search for general system info
make -f Makefile.ai memory-rag-search QUERY="system configuration" NAMESPACE="default"

# Search for general documentation
make -f Makefile.ai memory-rag-search QUERY="general documentation" NAMESPACE="default"
```

## Search Strategies

### 1. **Namespace-Specific Search** 🎯
**Best Practice:** Always specify the namespace when you know the type of content you're looking for

```bash
# For workflow documentation
make -f Makefile.ai memory-rag-search QUERY="your query" NAMESPACE="user_stories"

# For recent code changes
make -f Makefile.ai memory-rag-search QUERY="your query" NAMESPACE="progress_reports"

# For development patterns
make -f Makefile.ai memory-rag-search QUERY="your query" NAMESPACE="daily_analysis"
```

### 2. **Cross-Namespace Search** 🔍
**Best Practice:** Use no namespace or "default" to search across all namespaces

```bash
# Search across all namespaces
make -f Makefile.ai memory-rag-search QUERY="your query"

# Or explicitly search all
make -f Makefile.ai memory-rag-search QUERY="your query" NAMESPACE="default"
```

### 3. **Time-Based Search** ⏰
**Best Practice:** Use time-based namespaces for historical analysis

```bash
# Recent activity (last day)
make -f Makefile.ai memory-rag-search QUERY="recent changes" NAMESPACE="daily_analysis"

# Recent activity (last week)
make -f Makefile.ai memory-rag-search QUERY="weekly patterns" NAMESPACE="weekly_analysis"

# Recent activity (last month)
make -f Makefile.ai memory-rag-search QUERY="monthly overview" NAMESPACE="monthly_analysis"
```

### 4. **Progressive Search** 📈
**Best Practice:** Start broad, then narrow down

```bash
# Step 1: Broad search across all namespaces
make -f Makefile.ai memory-rag-search QUERY="docker changes"

# Step 2: Narrow to specific namespace if needed
make -f Makefile.ai memory-rag-search QUERY="docker changes" NAMESPACE="progress_reports"

# Step 3: Increase results if needed
make -f Makefile.ai memory-rag-search QUERY="docker changes" NAMESPACE="progress_reports" TOP_K=10
```

## Common Search Patterns

### 1. **Finding Documentation** 📚
```bash
# User stories and workflows
make -f Makefile.ai memory-rag-search QUERY="how to submit rule proposal" NAMESPACE="user_stories"

# General documentation
make -f Makefile.ai memory-rag-search QUERY="documentation workflow" NAMESPACE="default"
```

### 2. **Finding Recent Changes** 🔄
```bash
# Recent code changes
make -f Makefile.ai memory-rag-search QUERY="recent git changes" NAMESPACE="progress_reports"

# Recent development activity
make -f Makefile.ai memory-rag-search QUERY="recent development" NAMESPACE="daily_analysis"
```

### 3. **Finding Patterns** 📊
```bash
# Development patterns
make -f Makefile.ai memory-rag-search QUERY="development patterns" NAMESPACE="weekly_analysis"

# Code evolution
make -f Makefile.ai memory-rag-search QUERY="code evolution" NAMESPACE="monthly_analysis"
```

### 4. **Finding Specific Features** ⚙️
```bash
# Feature implementation
make -f Makefile.ai memory-rag-search QUERY="feature implementation" NAMESPACE="progress_reports"

# Feature documentation
make -f Makefile.ai memory-rag-search QUERY="feature documentation" NAMESPACE="user_stories"
```

## Advanced Search Techniques

### 1. **Combining Multiple Queries** 🔗
```bash
# Search for both implementation and documentation
make -f Makefile.ai memory-rag-search QUERY="rule proposal implementation documentation" NAMESPACE="user_stories"
```

### 2. **Using Technical Terms** 💻
```bash
# Use specific technical terms
make -f Makefile.ai memory-rag-search QUERY="FastAPI authentication token generation" NAMESPACE="progress_reports"
```

### 3. **Searching for Errors** 🐛
```bash
# Search for error-related content
make -f Makefile.ai memory-rag-search QUERY="error handling authentication" NAMESPACE="progress_reports"
```

## Troubleshooting Search Issues

### 1. **No Results Found** ❌
**Solutions:**
- Try broader search terms
- Remove namespace restriction
- Increase TOP_K value
- Check if content exists in the namespace

```bash
# Broader search
make -f Makefile.ai memory-rag-search QUERY="docker" NAMESPACE="progress_reports"

# Cross-namespace search
make -f Makefile.ai memory-rag-search QUERY="docker"

# More results
make -f Makefile.ai memory-rag-search QUERY="docker" TOP_K=10
```

### 2. **Too Many Irrelevant Results** 📝
**Solutions:**
- Use more specific search terms
- Specify the correct namespace
- Use technical terminology
- Add context to your query

```bash
# More specific query
make -f Makefile.ai memory-rag-search QUERY="docker compose authentication token setup" NAMESPACE="progress_reports"
```

### 3. **Authentication Issues** 🔐
**Solutions:**
- Check token file exists: `ls -la .api_admin_token .apitoken`
- Verify token content: `cat .api_admin_token`
- Use direct token: `AUTH_TOKEN="your-token"`

## Expected Outcomes

After using these search strategies, you should be able to:
- Find relevant information quickly across different content types
- Discover related content and patterns
- Access historical context and development evolution
- Navigate the knowledge base effectively
- Understand the different types of content available

## Quick Reference Card

```bash
# User stories and workflows
make -f Makefile.ai memory-rag-search QUERY="your query" NAMESPACE="user_stories"

# Recent code changes
make -f Makefile.ai memory-rag-search QUERY="your query" NAMESPACE="progress_reports"

# Daily development activity
make -f Makefile.ai memory-rag-search QUERY="your query" NAMESPACE="daily_analysis"

# Cross-namespace search
make -f Makefile.ai memory-rag-search QUERY="your query"

# More results
make -f Makefile.ai memory-rag-search QUERY="your query" TOP_K=10
```

## Next Steps
1. Practice with different namespaces and search terms
2. Create search aliases for common queries
3. Integrate search into your development workflow
4. Contribute content to relevant namespaces
5. Share effective search patterns with your team

---

**Remember:** The memory system learns and grows with use. Regular searches help improve the system's understanding and connections between content. Different namespaces serve different purposes - choose the right one for your search needs!

Need help? Check the [Memory System Documentation](docs/MEMORY_SYSTEM.md) or contact your system administrator. 