# 🏴‍☠️ Playbook MCP Quick Start Guide

Ahoy there, matey! Ready to set sail with automated web testing? Here's how to get Playbook MCP up and running in yer AI-IDE environment.

## Quick Setup (2 minutes)

### 1. Install Playbook MCP
```bash
# Install Playbook MCP globally (optional)
npm install -g @playbook-ai/playbook-mcp

# Or just test if it works
npx -y @playbook-ai/playbook-mcp --version
```

### 2. Verify Configuration
The `.cursor/mcp.json` file is already configured:

```json
{
  "mcpServers": {
    "playbook": {
      "command": "npx",
      "args": ["-y", "@playbook-ai/playbook-mcp"],
      "env": {
        "PLAYBOOK_API_KEY": "${PLAYBOOK_API_KEY}"
      }
    }
  }
}
```

### 3. Restart Cursor IDE
After installation, restart Cursor IDE to load the MCP configuration.

### 4. Test Installation
```bash
make -f Makefile.ai playbook-test
```

## What's Been Set Up

### Configuration Files
- `.cursor/mcp.json` - Cursor IDE MCP configuration (already done)
- `playbook-config/config.json` - Optional Playbook server configuration

### Makefile Targets
```bash
make -f Makefile.ai playbook-test  # Test Playbook MCP installation
```

## Using Playbook MCP in Cursor

Once connected, you can use Playbook MCP tools directly in Cursor:

```javascript
// Navigate to a website
await mcp_playbook_navigate({
  url: "http://localhost:3000"
});

// Take a screenshot
await mcp_playbook_screenshot({
  path: "/tmp/screenshot.png"
});

// Fill out forms
await mcp_playbook_fill({
  selector: "#email",
  value: "test@example.com"
});

// Click buttons
await mcp_playbook_click({
  selector: "#submit-button"
});
```

## Troubleshooting

### Installation Issues
```bash
# Check if npx is available
which npx

# Try installing globally
npm install -g @playbook-ai/playbook-mcp

# Check version
npx -y @playbook-ai/playbook-mcp --version
```

### MCP Not Working in Cursor
1. Restart Cursor IDE
2. Check `.cursor/mcp.json` is properly formatted
3. Verify npx is available in your PATH
4. Run the test: `make -f Makefile.ai playbook-test`

### Permission Issues
```bash
# If you get permission errors
sudo npm install -g @playbook-ai/playbook-mcp
```

## Next Steps

1. **Read the full user story**: `docs/user_stories/playbook_mcp_setup.md`
2. **Explore Playbook documentation**: [Playbook MCP GitHub](https://github.com/playbook-ai/playbook-mcp)
3. **Try web automation**: Start with simple navigation and screenshots
4. **Integrate with tests**: Use Playbook MCP in your Playwright test suites

## Why This Approach?

This simpler approach:
- ✅ No Docker containers needed
- ✅ Works immediately with npx
- ✅ Uses less resources
- ✅ Easier to debug and maintain
- ✅ Consistent with how most MCP servers work

## Support

If ye run into trouble:
- Check npx installation: `which npx`
- Test Playbook directly: `npx -y @playbook-ai/playbook-mcp --version`
- Review the user story for detailed troubleshooting steps

Happy testing, ye scurvy dogs! 🏴‍☠️ 