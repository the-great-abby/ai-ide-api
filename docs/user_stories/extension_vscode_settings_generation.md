---
title: "Extension VS Code Settings Generation"
description: "Automatic generation of .vscode/settings.json during project onboarding for seamless IDE extension configuration"
actors: ["Developer", "Onboarding Script", "IDE Extension", "AI IDE API"]
preconditions: ["Onboarding script is running", "Project is being set up", "API token is generated"]
postconditions: ["VS Code settings.json is created", "Extension is pre-configured", "Project-specific settings are applied"]
priority: "High"
tags: ["extension", "onboarding", "vscode", "settings", "automation"]
---

# Extension VS Code Settings Generation

## Motivation

As a developer setting up a new project with the AI IDE API, I want the onboarding process to automatically generate the necessary VS Code settings so that the extension is immediately configured and ready to use. This eliminates manual configuration steps and ensures consistent setup across all projects.

## Actors

- **Developer**: Setting up a new project with AI IDE API
- **Onboarding Script**: `onboard_external_updated.py` that handles project setup
- **IDE Extension**: VS Code/Cursor extension that provides AI assistance
- **AI IDE API**: Backend system providing project-specific rules and memories

## Preconditions

- Onboarding script is running (`./onboard_external.sh`)
- Project name and API token have been generated
- Project files (`.project`, `.apitoken`, `.teamname`) exist
- Developer has VS Code or Cursor installed

## Step-by-Step Actions

### 1. Onboarding Process Triggers Settings Generation

```python
# In onboard_external_updated.py
def run_onboarding(self):
    """Main onboarding flow."""
    # ... existing onboarding steps ...
    
    # Run example workflow
    self.create_example_workflow()
    
    # Generate VS Code settings
    if self.project_name:  # Ensure project_name is not None
        self.generate_vscode_settings()
    
    # Show next steps
    self.show_next_steps()
```

### 2. Settings Generation Process

```python
def generate_vscode_settings(self):
    """Generate .vscode/settings.json for the project."""
    print("📝 Generating VS Code Settings")
    print("-" * 40)
    
    try:
        # Create .vscode directory
        os.makedirs('.vscode', exist_ok=True)
        
        # Generate settings content
        settings_content = {
            "ai-ide.projectName": self.project_name,
            "ai-ide.namespace": f"{self.project_name}/private",
            "ai-ide.suggestionTypes": ["rules", "patterns", "memory"],
            "ai-ide.languageFocus": ["python", "javascript"],
            "ai-ide.framework": "fastapi",
            "ai-ide.apiUrl": self.api_base,
            "ai-ide.enableRealTime": True,
            "ai-ide.autoApply": False,
            "ai-ide.workspaceDetection": True,
            "ai-ide.projectConfigFiles": [".project", ".apitoken", ".teamname"]
        }
        
        # Write settings file
        with open('.vscode/settings.json', 'w') as f:
            json.dump(settings_content, f, indent=2)
        
        print("✅ Generated .vscode/settings.json")
        print("   📄 Project name:", self.project_name)
        print("   📄 Namespace:", f"{self.project_name}/private")
        print("   📄 API URL:", self.api_base)
        print("   📄 Wildcard access:", f"{self.project_name}/*")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate VS Code settings: {e}")
        return False
```

### 3. Generated Settings Structure

```json
{
  "ai-ide.projectName": "my-awesome-project",
  "ai-ide.namespace": "my-awesome-project/private",
  "ai-ide.suggestionTypes": ["rules", "patterns", "memory"],
  "ai-ide.languageFocus": ["python", "javascript"],
  "ai-ide.framework": "fastapi",
  "ai-ide.apiUrl": "http://localhost:9103",
  "ai-ide.enableRealTime": true,
  "ai-ide.autoApply": false,
  "ai-ide.workspaceDetection": true,
  "ai-ide.projectConfigFiles": [".project", ".apitoken", ".teamname"]
}
```

### 4. Extension Configuration Details

#### Project-Specific Settings
- **`ai-ide.projectName`**: Matches the project name from onboarding
- **`ai-ide.namespace`**: Default namespace for the project (`project-name/private`)
- **`ai-ide.apiUrl`**: API base URL for the extension to connect to

#### Extension Behavior Settings
- **`ai-ide.enableRealTime`**: Enables real-time code analysis
- **`ai-ide.autoApply`**: Disabled by default for safety
- **`ai-ide.workspaceDetection`**: Enables automatic project detection
- **`ai-ide.projectConfigFiles`**: Files the extension should look for

#### Language and Framework Settings
- **`ai-ide.languageFocus`**: Primary languages for suggestions
- **`ai-ide.framework`**: Main framework for framework-specific patterns
- **`ai-ide.suggestionTypes`**: Types of suggestions to show

### 5. Namespace Access Configuration

The settings include the default namespace (`project-name/private`), but the extension has access to **all namespaces under the project prefix** due to wildcard permissions:

```bash
# Wildcard access pattern set during onboarding
namespace_pattern = "my-awesome-project/*"

# This allows access to:
# - my-awesome-project/private
# - my-awesome-project/public  
# - my-awesome-project/docs
# - my-awesome-project/research
# - my-awesome-project/code
# - Any other namespace under the project prefix
```

## Expected Outcomes

### Immediate Benefits
- **Zero Configuration**: Extension works immediately after onboarding
- **Consistent Setup**: All projects get the same base configuration
- **Project Isolation**: Each project has its own settings
- **Namespace Access**: Full access to project namespaces via wildcards

### Extension Capabilities
- **Automatic Project Detection**: Extension reads `.project`, `.apitoken`, `.teamname`
- **Real-Time Suggestions**: Live code analysis and suggestions
- **Cross-Namespace Access**: Can read/write to any project namespace
- **Context-Aware**: Suggests based on project's language and framework

### Developer Experience
- **Seamless Onboarding**: No manual configuration required
- **Immediate Productivity**: Extension ready to use right away
- **Flexible Organization**: Can use any namespace under project prefix
- **Consistent Workflow**: Same setup process for all projects

## Technical Implementation

### 1. File Structure After Onboarding

```
my-awesome-project/
├── .project              # Project name
├── .apitoken            # API token
├── .teamname            # Team name
├── .vscode/
│   └── settings.json    # Generated extension settings
├── Makefile.external    # Generated Makefile
├── USAGE.md             # Usage guide
└── examples/            # Example files
```

### 2. Extension Integration

The extension reads the generated settings and:

```typescript
// Extension reads project configuration
const projectName = vscode.workspace.getConfiguration('ai-ide').get('projectName');
const namespace = vscode.workspace.getConfiguration('ai-ide').get('namespace');
const apiUrl = vscode.workspace.getConfiguration('ai-ide').get('apiUrl');

// Connects to API with project context
const websocket = new WebSocket(`${apiUrl}/ws/ide?token=${apiToken}&project=${projectName}`);

// Sends project-specific requests
websocket.send(JSON.stringify({
  type: "code_analysis",
  context: {
    project: projectName,
    namespace: namespace,
    // ... other context
  }
}));
```

### 3. Namespace Access Patterns

```typescript
// Extension can access any namespace under project prefix
const namespaces = [
  `${projectName}/private`,    // Private development notes
  `${projectName}/public`,     // Public documentation
  `${projectName}/docs`,       // Project documentation
  `${projectName}/research`,   // Research and experiments
  `${projectName}/code`,       // Code patterns and examples
  `${projectName}/tasks`,      // Task tracking
  `${projectName}/ideas`       // Ideas and concepts
];

// All accessible via wildcard permission: project-name/*
```

## Best Practices

### 1. Settings Customization
- **Modify After Generation**: Developers can customize settings after generation
- **Keep Project-Specific**: Don't modify global VS Code settings
- **Version Control**: Include `.vscode/settings.json` in version control
- **Team Consistency**: Share settings across team members

### 2. Namespace Organization
- **Use Descriptive Names**: Choose meaningful namespace names
- **Consistent Structure**: Use similar namespaces across projects
- **Documentation**: Document namespace purposes
- **Regular Cleanup**: Archive or delete unused namespaces

### 3. Extension Usage
- **Start with Defaults**: Use generated settings as starting point
- **Gradual Customization**: Add custom settings as needed
- **Test Changes**: Verify extension behavior after settings changes
- **Backup Settings**: Keep backups of working configurations

## Troubleshooting

### Common Issues

#### 1. Settings Not Generated
```bash
# Check if onboarding completed successfully
ls -la .vscode/settings.json

# Re-run onboarding if missing
./onboard_external.sh
```

#### 2. Extension Not Working
```bash
# Check settings file
cat .vscode/settings.json

# Verify API connection
make -f Makefile.external test-connection

# Check extension logs
# In VS Code: Help > Toggle Developer Tools > Console
```

#### 3. Namespace Access Issues
```bash
# Check namespace permissions
curl -H "Authorization: Bearer $(cat .apitoken)" \
  http://localhost:9103/memory/nodes?namespace=your-project/private

# Verify wildcard access
curl -H "Authorization: Bearer $(cat .apitoken)" \
  http://localhost:9103/memory/nodes?namespace=your-project/public
```

### Debug Mode
```json
// Add to .vscode/settings.json for debugging
{
  "ai-ide.debug": true,
  "ai-ide.logLevel": "debug"
}
```

## Future Enhancements

### 1. Advanced Settings
- **Language Detection**: Auto-detect project languages
- **Framework Detection**: Auto-detect frameworks from dependencies
- **Custom Templates**: Project-specific setting templates
- **Environment Variables**: Support for environment-specific settings

### 2. Team Collaboration
- **Shared Settings**: Team-wide setting templates
- **Settings Sync**: Sync settings across team members
- **Settings Validation**: Validate settings against project requirements
- **Settings Migration**: Migrate settings between projects

### 3. Integration Features
- **CI/CD Integration**: Generate settings in CI/CD pipelines
- **Project Templates**: Include settings in project templates
- **Settings API**: API endpoints for managing settings
- **Settings Analytics**: Track settings usage and effectiveness

## Success Metrics

### 1. Developer Productivity
- **Setup Time**: Time from onboarding to first extension use
- **Configuration Errors**: Reduction in manual configuration errors
- **Extension Adoption**: Percentage of projects using the extension
- **User Satisfaction**: Developer feedback on setup experience

### 2. System Performance
- **Settings Generation**: Success rate of settings generation
- **Extension Startup**: Time for extension to become ready
- **API Connectivity**: Success rate of extension API connections
- **Namespace Access**: Success rate of namespace operations

### 3. Quality Metrics
- **Settings Completeness**: Percentage of required settings included
- **Settings Accuracy**: Accuracy of auto-generated settings
- **Error Reduction**: Reduction in configuration-related errors
- **Support Requests**: Reduction in setup-related support requests

## References

- [Multi-Project Extension Architecture](multi_project_extension_architecture.md)
- [External Project Onboarding](external_project_onboarding.md)
- [Memory System Security and Privacy](memory_security_and_privacy.md)
- [Real-Time IDE Integration](real_time_ide_integration.md)
- [API Authentication Guide](../onboarding/AUTHENTICATION_AUTHORIZATION.md) 