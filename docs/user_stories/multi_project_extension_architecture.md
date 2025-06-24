---
title: "Multi-Project Extension Architecture"
description: "Complete guide to how IDE extensions work across multiple projects with automatic context switching and project isolation"
actors: ["Developer", "IDE Extension", "AI IDE API", "Project Manager"]
preconditions: ["AI IDE API is running", "Multiple projects are set up", "Extension is installed"]
postconditions: ["Extension automatically switches between projects", "Each project has isolated rules and memories", "Seamless multi-project workflow"]
priority: "High"
tags: ["extension", "multi-project", "workspace-detection", "context-switching", "isolation"]
---

# Multi-Project Extension Architecture

## Motivation

As a developer working on multiple projects, I want my IDE extension to automatically detect which project I'm working on and provide contextually relevant suggestions, rules, and memories for that specific project. The extension should seamlessly switch between projects without manual configuration, maintaining complete isolation between project knowledge bases.

## Actors

- **Developer**: Working on multiple projects in the same IDE
- **IDE Extension**: VS Code, Cursor, or JetBrains extension that provides AI assistance
- **AI IDE API**: Backend system providing project-specific rules and memories
- **Project Manager**: Managing multiple projects and their configurations

## Preconditions

- AI IDE API is running and accessible
- Multiple projects are set up in the system
- IDE extension is installed and configured
- Each project has its own API token and namespace

## Step-by-Step Actions

### 1. Extension Installation & Initial Setup

#### Install the Extension
```bash
# For VS Code/Cursor
code --install-extension ai-ide.extension

# For JetBrains IDEs
# Download from plugin marketplace or install manually
```

#### Global Extension Configuration
```json
// Global settings.json (user-level)
{
  "ai-ide.apiUrl": "http://localhost:9103",
  "ai-ide.enableRealTime": true,
  "ai-ide.suggestionTypes": ["rules", "patterns", "memory", "predictions"],
  "ai-ide.autoApply": false,
  "ai-ide.workspaceDetection": true,
  "ai-ide.projectConfigFiles": [".project", ".apitoken", ".teamname"]
}
```

### 2. Project-Specific Configuration

Each project gets its own configuration files:

#### Project Configuration Files
```bash
# Project A: frontend-app
frontend-app/
├── .project              # Project name: "frontend-app"
├── .apitoken            # API token for frontend-app
├── .teamname            # Team name: "frontend-team"
├── .vscode/
│   └── settings.json    # Project-specific extension settings
└── src/

# Project B: backend-api
backend-api/
├── .project              # Project name: "backend-api"
├── .apitoken            # API token for backend-api
├── .teamname            # Team name: "backend-team"
├── .vscode/
│   └── settings.json    # Project-specific extension settings
└── src/
```

#### Project-Specific Settings
```json
// frontend-app/.vscode/settings.json
{
  "ai-ide.projectName": "frontend-app",
  "ai-ide.namespace": "frontend-app/private",
  "ai-ide.suggestionTypes": ["rules", "patterns", "memory"],
  "ai-ide.languageFocus": ["javascript", "typescript", "jsx", "tsx"],
  "ai-ide.framework": "react"
}

// backend-api/.vscode/settings.json
{
  "ai-ide.projectName": "backend-api",
  "ai-ide.namespace": "backend-api/private",
  "ai-ide.suggestionTypes": ["rules", "patterns", "memory", "api-design"],
  "ai-ide.languageFocus": ["python", "sql"],
  "ai-ide.framework": "fastapi"
}
```

### 3. Workspace Detection & Context Switching

#### Automatic Project Detection
```typescript
// Extension automatically detects project context
class AIIDEExtension {
  private currentProject: ProjectContext | null = null;
  
  private async detectProjectContext(workspaceFolder: vscode.WorkspaceFolder): Promise<ProjectContext> {
    const projectConfig = await this.loadProjectConfig(workspaceFolder);
    
    return {
      projectName: projectConfig.projectName,
      projectId: projectConfig.projectId,
      namespace: projectConfig.namespace,
      apiToken: projectConfig.apiToken,
      teamName: projectConfig.teamName,
      settings: projectConfig.settings
    };
  }
  
  private async loadProjectConfig(workspaceFolder: vscode.WorkspaceFolder): Promise<ProjectConfig> {
    // Load project files
    const projectName = await this.readProjectFile(workspaceFolder, '.project');
    const apiToken = await this.readProjectFile(workspaceFolder, '.apitoken');
    const teamName = await this.readProjectFile(workspaceFolder, '.teamname');
    
    // Load VS Code settings
    const settings = await this.loadVSCodeSettings(workspaceFolder);
    
    return {
      projectName,
      apiToken,
      teamName,
      settings,
      namespace: `${projectName}/private`
    };
  }
}
```

#### Context Switching Logic
```typescript
// Extension handles workspace changes
class AIIDEExtension {
  async activate(context: vscode.ExtensionContext) {
    // Listen for workspace folder changes
    vscode.workspace.onDidChangeWorkspaceFolders(this.handleWorkspaceChange.bind(this));
    
    // Listen for active text editor changes
    vscode.window.onDidChangeActiveTextEditor(this.handleEditorChange.bind(this));
    
    // Initialize with current workspace
    await this.initializeCurrentWorkspace();
  }
  
  private async handleWorkspaceChange(event: vscode.WorkspaceFoldersChangeEvent) {
    // When switching between projects
    if (event.added.length > 0) {
      const newWorkspace = event.added[0];
      await this.switchToProject(newWorkspace);
    }
  }
  
  private async switchToProject(workspaceFolder: vscode.WorkspaceFolder) {
    // Detect new project context
    const newProject = await this.detectProjectContext(workspaceFolder);
    
    // Disconnect from previous project
    if (this.currentProject) {
      await this.disconnectFromProject(this.currentProject);
    }
    
    // Connect to new project
    await this.connectToProject(newProject);
    
    // Update UI and status
    this.updateStatusBar(newProject);
    this.updateSuggestions(newProject);
    
    this.currentProject = newProject;
  }
}
```

### 4. Project Isolation & Security

#### Token-Based Isolation
```typescript
// Each project uses its own API token
class ProjectConnection {
  private websocket: WebSocket | null = null;
  
  async connectToProject(project: ProjectContext) {
    // Connect using project-specific token
    const wsUrl = `${this.apiUrl}/ws/ide?token=${project.apiToken}&project=${project.projectName}`;
    this.websocket = new WebSocket(wsUrl);
    
    // Set up project-specific message handlers
    this.websocket.onmessage = (event) => {
      this.handleProjectMessage(event, project);
    };
  }
  
  private async handleProjectMessage(event: MessageEvent, project: ProjectContext) {
    const data = JSON.parse(event.data);
    
    // All messages are scoped to the current project
    switch (data.type) {
      case "suggestions":
        await this.displayProjectSuggestions(data.suggestions, project);
        break;
      case "rules":
        await this.displayProjectRules(data.rules, project);
        break;
      case "memory":
        await this.displayProjectMemory(data.memory, project);
        break;
    }
  }
}
```

#### Namespace Isolation
```typescript
// Memory and rules are isolated by namespace
class ProjectMemoryManager {
  async queryProjectMemory(query: string, project: ProjectContext) {
    const response = await fetch(`${this.apiUrl}/memory/nodes/search`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${project.apiToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: query,
        namespace: project.namespace,  // Scoped to project namespace
        limit: 10
      })
    });
    
    return response.json();
  }
  
  async getProjectRules(project: ProjectContext) {
    const response = await fetch(`${this.apiUrl}/rules?scope_level=project&scope_id=${project.projectId}`, {
      headers: {
        'Authorization': `Bearer ${project.apiToken}`
      }
    });
    
    return response.json();
  }
}
```

### 5. Real-Time Context Awareness

#### Code Analysis with Project Context
```typescript
// Extension sends project context with code analysis
class CodeAnalyzer {
  private async analyzeCode(code: string, document: vscode.TextDocument, project: ProjectContext) {
    const context = {
      code: code,
      language: document.languageId,
      filePath: document.fileName,
      project: {
        name: project.projectName,
        id: project.projectId,
        namespace: project.namespace,
        framework: project.settings.framework,
        languageFocus: project.settings.languageFocus
      },
      timestamp: new Date().toISOString()
    };
    
    // Send to API for project-specific analysis
    this.websocket.send(JSON.stringify({
      type: "code_analysis",
      context: context
    }));
  }
}
```

#### Project-Specific Suggestions
```typescript
// Display suggestions relevant to current project
class SuggestionDisplay {
  async displayProjectSuggestions(suggestions: any[], project: ProjectContext) {
    // Filter suggestions based on project settings
    const relevantSuggestions = suggestions.filter(suggestion => {
      // Check if suggestion applies to current project's language focus
      if (project.settings.languageFocus && suggestion.language) {
        return project.settings.languageFocus.includes(suggestion.language);
      }
      
      // Check if suggestion applies to current project's framework
      if (project.settings.framework && suggestion.framework) {
        return suggestion.framework === project.settings.framework;
      }
      
      return true;
    });
    
    // Display with project context
    this.showSuggestions(relevantSuggestions, project.projectName);
  }
}
```

### 6. Multi-Project Workflow Examples

#### Working with Multiple Projects

```bash
# Project A: Frontend React App
cd ~/projects/frontend-app
code .  # Opens VS Code with frontend-app context

# Extension automatically:
# - Detects .project file: "frontend-app"
# - Loads .apitoken for frontend-app
# - Connects to frontend-app/private namespace
# - Shows React/TypeScript specific suggestions

# Switch to Project B: Backend API
cd ~/projects/backend-api
code .  # Opens new VS Code window with backend-api context

# Extension automatically:
# - Detects .project file: "backend-api"
# - Loads .apitoken for backend-api
# - Connects to backend-api/private namespace
# - Shows Python/FastAPI specific suggestions
```

#### Configuration Examples

```json
// frontend-app/.vscode/settings.json
{
  "ai-ide.projectName": "frontend-app",
  "ai-ide.namespace": "frontend-app/private",
  "ai-ide.suggestionTypes": ["rules", "patterns", "memory"],
  "ai-ide.languageFocus": ["javascript", "typescript", "jsx", "tsx"],
  "ai-ide.framework": "react",
  "ai-ide.uiFramework": "material-ui",
  "ai-ide.testingFramework": "jest",
  "ai-ide.bundler": "webpack"
}

// backend-api/.vscode/settings.json
{
  "ai-ide.projectName": "backend-api",
  "ai-ide.namespace": "backend-api/private",
  "ai-ide.suggestionTypes": ["rules", "patterns", "memory", "api-design"],
  "ai-ide.languageFocus": ["python", "sql"],
  "ai-ide.framework": "fastapi",
  "ai-ide.database": "postgresql",
  "ai-ide.testingFramework": "pytest",
  "ai-ide.deployment": "docker"
}
```

### 7. Cross-Project Knowledge Sharing

#### Optional Knowledge Sharing
```typescript
// Projects can optionally share knowledge
class CrossProjectSharing {
  async shareKnowledge(sourceProject: ProjectContext, targetProject: ProjectContext, knowledge: any) {
    // Check if target project allows knowledge sharing
    const sharingAllowed = await this.checkSharingPermissions(sourceProject, targetProject);
    
    if (sharingAllowed) {
      // Create shared memory node
      await this.createSharedMemory(sourceProject, targetProject, knowledge);
    }
  }
  
  async getSharedKnowledge(project: ProjectContext) {
    // Get knowledge shared with this project
    const sharedNamespaces = await this.getSharedNamespaces(project);
    
    const sharedKnowledge = [];
    for (const namespace of sharedNamespaces) {
      const knowledge = await this.querySharedNamespace(namespace, project);
      sharedKnowledge.push(...knowledge);
    }
    
    return sharedKnowledge;
  }
}
```

### 8. Extension Status & UI

#### Status Bar Integration
```typescript
// Show current project in status bar
class StatusBarManager {
  private statusBarItem: vscode.StatusBarItem;
  
  updateStatusBar(project: ProjectContext) {
    this.statusBarItem.text = `$(project) ${project.projectName}`;
    this.statusBarItem.tooltip = `AI IDE: ${project.projectName} (${project.teamName})`;
    this.statusBarItem.command = 'ai-ide.showProjectInfo';
    this.statusBarItem.show();
  }
  
  async showProjectInfo() {
    if (this.currentProject) {
      const info = await this.getProjectInfo(this.currentProject);
      vscode.window.showInformationMessage(
        `Project: ${info.name}\nTeam: ${info.team}\nNamespace: ${info.namespace}\nRules: ${info.ruleCount}\nMemories: ${info.memoryCount}`
      );
    }
  }
}
```

#### Project-Specific Commands
```typescript
// Register project-specific commands
class CommandManager {
  registerProjectCommands(project: ProjectContext) {
    // Project-specific rule management
    vscode.commands.registerCommand('ai-ide.project.rules', () => {
      this.showProjectRules(project);
    });
    
    // Project-specific memory search
    vscode.commands.registerCommand('ai-ide.project.memory', () => {
      this.showProjectMemory(project);
    });
    
    // Project-specific suggestions
    vscode.commands.registerCommand('ai-ide.project.suggestions', () => {
      this.showProjectSuggestions(project);
    });
  }
}
```

## Expected Outcomes

### Immediate Benefits
- **Automatic Context Switching**: Extension seamlessly switches between projects
- **Project-Specific Suggestions**: Relevant rules and patterns for each project
- **Isolated Knowledge Bases**: No cross-contamination between projects
- **Reduced Configuration**: Minimal setup required per project

### Long-term Benefits
- **Consistent Development**: Same extension works across all projects
- **Knowledge Accumulation**: Each project builds its own knowledge base
- **Team Collaboration**: Multiple developers can work on different projects
- **Scalable Architecture**: Works with any number of projects

## Technical Implementation

### 1. Extension Architecture
```typescript
// Main extension class
class AIIDEExtension {
  private projectManager: ProjectManager;
  private connectionManager: ConnectionManager;
  private suggestionEngine: SuggestionEngine;
  private memoryManager: MemoryManager;
  
  async activate(context: vscode.ExtensionContext) {
    // Initialize managers
    this.projectManager = new ProjectManager();
    this.connectionManager = new ConnectionManager();
    this.suggestionEngine = new SuggestionEngine();
    this.memoryManager = new MemoryManager();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Initialize current project
    await this.initializeCurrentProject();
  }
  
  private setupEventListeners() {
    // Workspace changes
    vscode.workspace.onDidChangeWorkspaceFolders(this.handleWorkspaceChange.bind(this));
    
    // Editor changes
    vscode.window.onDidChangeActiveTextEditor(this.handleEditorChange.bind(this));
    
    // Document changes
    vscode.workspace.onDidChangeTextDocument(this.handleDocumentChange.bind(this));
  }
}
```

### 2. Project Detection Algorithm
```typescript
// Project detection logic
class ProjectDetector {
  async detectProject(workspaceFolder: vscode.WorkspaceFolder): Promise<ProjectContext | null> {
    try {
      // Check for project configuration files
      const projectFiles = await this.findProjectFiles(workspaceFolder);
      
      if (projectFiles.length === 0) {
        return null; // No project configuration found
      }
      
      // Load project configuration
      const config = await this.loadProjectConfig(workspaceFolder, projectFiles);
      
      // Validate configuration
      if (!this.validateProjectConfig(config)) {
        throw new Error('Invalid project configuration');
      }
      
      return config;
    } catch (error) {
      vscode.window.showErrorMessage(`Failed to detect project: ${error.message}`);
      return null;
    }
  }
  
  private async findProjectFiles(workspaceFolder: vscode.WorkspaceFolder): Promise<string[]> {
    const files = ['.project', '.apitoken', '.teamname'];
    const foundFiles = [];
    
    for (const file of files) {
      const filePath = vscode.Uri.joinPath(workspaceFolder.uri, file);
      try {
        await vscode.workspace.fs.stat(filePath);
        foundFiles.push(file);
      } catch {
        // File doesn't exist
      }
    }
    
    return foundFiles;
  }
}
```

### 3. Connection Management
```typescript
// Manage connections to different projects
class ConnectionManager {
  private connections: Map<string, ProjectConnection> = new Map();
  
  async connectToProject(project: ProjectContext): Promise<void> {
    // Close existing connection if any
    await this.disconnectFromProject(project.projectName);
    
    // Create new connection
    const connection = new ProjectConnection(project);
    await connection.connect();
    
    this.connections.set(project.projectName, connection);
  }
  
  async disconnectFromProject(projectName: string): Promise<void> {
    const connection = this.connections.get(projectName);
    if (connection) {
      await connection.disconnect();
      this.connections.delete(projectName);
    }
  }
  
  getConnection(projectName: string): ProjectConnection | undefined {
    return this.connections.get(projectName);
  }
}
```

## Best Practices

### 1. Project Configuration
- **Use descriptive project names**: Make project names clear and memorable
- **Keep tokens secure**: Store API tokens in `.apitoken` files (not in version control)
- **Set language focus**: Configure `languageFocus` to get relevant suggestions
- **Define frameworks**: Set `framework` for framework-specific patterns

### 2. Workspace Organization
- **One project per workspace**: Keep projects in separate workspace folders
- **Consistent file structure**: Use the same configuration file names across projects
- **Clear naming**: Use descriptive folder names that match project names

### 3. Security & Privacy
- **Token isolation**: Each project uses its own API token
- **Namespace separation**: Projects have completely isolated namespaces
- **No cross-contamination**: Knowledge doesn't leak between projects
- **Optional sharing**: Cross-project knowledge sharing is opt-in

### 4. Performance Optimization
- **Lazy loading**: Only connect to projects when actively working on them
- **Connection pooling**: Reuse connections when switching between projects
- **Caching**: Cache project configurations and frequently used data
- **Background processing**: Don't block UI when switching projects

## Troubleshooting

### Common Issues

#### 1. Project Not Detected
```bash
# Check if project files exist
ls -la ~/projects/my-project/.project
ls -la ~/projects/my-project/.apitoken
ls -la ~/projects/my-project/.teamname

# Create missing files
echo "my-project" > .project
echo "your-api-token" > .apitoken
echo "my-team" > .teamname
```

#### 2. Connection Failed
```bash
# Check API token
cat .apitoken

# Test API connectivity
curl -H "Authorization: Bearer $(cat .apitoken)" \
  http://localhost:9103/health

# Regenerate token if needed
curl -X POST http://localhost:9103/admin/generate-token \
  -H "Authorization: Bearer $(cat .admin_token)" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "your-project-id", "description": "New token"}'
```

#### 3. Wrong Project Context
```bash
# Check current workspace
echo $PWD

# Verify project files
cat .project
cat .teamname

# Restart extension
# In VS Code: Ctrl+Shift+P -> "Developer: Reload Window"
```

#### 4. Suggestions Not Relevant
```json
// Update .vscode/settings.json
{
  "ai-ide.languageFocus": ["python", "javascript"],
  "ai-ide.framework": "fastapi",
  "ai-ide.suggestionTypes": ["rules", "patterns", "memory"]
}
```

### Debug Mode
```json
// Enable debug logging
{
  "ai-ide.debug": true,
  "ai-ide.logLevel": "debug"
}
```

## Future Enhancements

### 1. Advanced Features
- **Project templates**: Pre-configured project setups
- **Cross-project search**: Search across multiple projects
- **Project analytics**: Track usage and effectiveness per project
- **Team collaboration**: Share insights across team projects

### 2. IDE Integration
- **Multi-workspace support**: Work with multiple projects simultaneously
- **Project switching shortcuts**: Quick keyboard shortcuts to switch projects
- **Project-specific themes**: Visual indicators for different projects
- **Integrated project management**: Built-in project creation and setup

### 3. Advanced Analytics
- **Project-specific metrics**: Track productivity per project
- **Knowledge graph visualization**: Visual representation of project knowledge
- **Pattern recognition**: Identify common patterns across projects
- **Predictive suggestions**: Suggest improvements based on project history

## Success Metrics

### 1. Developer Productivity
- **Context switching time**: Time to switch between projects
- **Suggestion relevance**: Percentage of relevant suggestions per project
- **Setup time**: Time to configure new projects
- **Error reduction**: Reduction in project-specific errors

### 2. System Performance
- **Connection speed**: Time to connect to project API
- **Memory usage**: Extension memory usage with multiple projects
- **Response time**: Time for suggestions to appear
- **Reliability**: Uptime and error rates

### 3. User Satisfaction
- **Ease of use**: User feedback on multi-project workflow
- **Feature adoption**: Usage of project-specific features
- **Support requests**: Reduction in configuration-related support
- **User retention**: Continued use across multiple projects

## References

- [Project-Scoped Rules and Multi-User Collaboration](project_scoped_rules_and_multiuser.md)
- [External Project Onboarding](external_project_onboarding.md)
- [Real-Time IDE Integration](real_time_ide_integration.md)
- [Memory System Documentation](../onboarding/MEMORY_SYSTEM.md)
- [API Authentication Guide](../onboarding/AUTHENTICATION_AUTHORIZATION.md) 