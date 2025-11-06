# context-templates

## Context Templates for Detailer MCP

This repository contains the official collection of context templates for the [Detailer MCP](https://detailer.ginylil.com), an AI-powered co-pilot for developers. These templates provide reusable prompts, configurations, and workflows to accelerate development tasks.

## What are Context Templates?

Context templates are structured files (YAML or Markdown) that define specific instructions and context for the Detailer MCP. They are designed to help with a variety of tasks, from enforcing coding standards to automating common workflows like generating pull request descriptions.

## How to Use These Templates

The templates in this repository are accessed through the Detailer MCP using a set of powerful tools:

### `list_templates`
Discover all available templates. You can see their names, descriptions, and types. This helps you find the right template for your task.

### `get_template`
Download a template's raw content directly into your workspace. This is useful when you want to view or customize a template to fit your specific needs.

### `do_template`
Execute a template directly and receive immediate, context-aware output. Instead of just getting the template file, `do_template` processes it and provides you with the generated result, such as a feature plan or a list of best practices.

## Using Context Templates with MCP Public Token

You can access context templates directly via MCP (Model Context Protocol) using the public token. This allows you to use templates across different AI development platforms without needing to clone this repository.

### Public Token

```
dtl_public_eec1f1037008dc82ce9d314c3294fbcc0e3f5d5df315d8c6
```

**MCP Server URL:** `https://detailer-api.supabase.co/functions/v1/mcp`

### Platform-Specific Setup

Choose your platform to see the configuration instructions:

<details open>
<summary><strong>⚡ Kiro (One-Click Install)</strong></summary>

**Try clicking this link:** <a href="kiro://kiro.mcp/add?name=context-templates&config=%7B%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22mcp-remote%22%2C%22https%3A%2F%2Fdetailer-api.supabase.co%2Ffunctions%2Fv1%2Fmcp%22%2C%22--header%22%2C%22Authorization%3ABearer%20dtl_public_eec1f1037008dc82ce9d314c3294fbcc0e3f5d5df315d8c6%22%2C%22--allow-http%22%5D%2C%22disabled%22%3Afalse%2C%22autoApprove%22%3A%5B%5D%7D">Add to Kiro</a>

If the link doesn't work, copy and paste this into your browser's address bar:

```
kiro://kiro.mcp/add?name=context-templates&config=%7B%22command%22%3A%22npx%22%2C%22args%22%3A%5B%22mcp-remote%22%2C%22https%3A%2F%2Fdetailer-api.supabase.co%2Ffunctions%2Fv1%2Fmcp%22%2C%22--header%22%2C%22Authorization%3ABearer%20dtl_public_eec1f1037008dc82ce9d314c3294fbcc0e3f5d5df315d8c6%22%2C%22--allow-http%22%5D%2C%22disabled%22%3Afalse%2C%22autoApprove%22%3A%5B%5D%7D
```

This will open Kiro and prompt you to install the context-templates MCP server automatically.

</details>

<details>
<summary><strong>🎯 Cursor IDE</strong></summary>

#### Option 1: Using Cursor's MCP Settings UI (Recommended)

1. Open Cursor IDE
2. Click the **Settings/Cog icon (⚙️)** in the top-right corner
3. Select **"MCP"** from the sidebar
4. Click **"Add new global MCP server"**
5. This will open your `mcp.json` configuration file
6. Add the configuration below

#### Option 2: Manual Configuration

Directly edit your Cursor MCP settings file at the following location:

**macOS/Linux:** `~/.cursor/mcp.json`  
**Windows:** `%USERPROFILE%\.cursor\mcp.json`

Add the following configuration:

```json
{
  "mcpServers": {
    "context-templates": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://detailer-api.supabase.co/functions/v1/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}",
        "--allow-http"
      ],
      "env": {
        "AUTH_HEADER": "Bearer dtl_public_eec1f1037008dc82ce9d314c3294fbcc0e3f5d5df315d8c6"
      }
    }
  }
}
```

**After configuration:**
- Save the file
- Restart Cursor IDE completely to load the new MCP server
- The MCP server indicator should appear in the Cursor interface

</details>

<details>
<summary><strong>🌊 Windsurf IDE</strong></summary>

#### Option 1: Using Windsurf's MCP Settings UI (Recommended)

1. Open Windsurf IDE
2. Press `Cmd/Ctrl + ,` to open **Windsurf Settings**
3. Scroll down to the **Cascade** section
4. Find **"Plugins (MCP servers)"** or **"Model Context Protocol (MCP) Servers"**
5. Click **"Manage Plugins"**
6. Click **"View raw config"** or **"Add custom server"**
7. Add the configuration below
8. Click the **Refresh** button after saving

#### Option 2: Manual Configuration

Directly edit your Windsurf MCP configuration file at the following location:

**macOS:** `~/.codeium/windsurf/mcp_config.json`  
**Windows:** `%APPDATA%\Codeium\Windsurf\mcp_config.json`  
**Linux:** `~/.config/Codeium/Windsurf/mcp_config.json` or `~/.codeium/windsurf/mcp_config.json`

Add the following configuration:

```json
{
  "mcpServers": {
    "context-templates": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://detailer-api.supabase.co/functions/v1/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}",
        "--allow-http"
      ],
      "env": {
        "AUTH_HEADER": "Bearer dtl_public_eec1f1037008dc82ce9d314c3294fbcc0e3f5d5df315d8c6"
      }
    }
  }
}
```

**After configuration:**
- Save the file
- Click the **Refresh** button in the MCP settings panel
- Restart Windsurf IDE for changes to take full effect

</details>

<details>
<summary><strong>🤖 Claude Desktop</strong></summary>

Add the following configuration to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "context-templates": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://detailer-api.supabase.co/functions/v1/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}",
        "--allow-http"
      ],
      "env": {
        "AUTH_HEADER": "Bearer dtl_public_eec1f1037008dc82ce9d314c3294fbcc0e3f5d5df315d8c6"
      }
    }
  }
}
```

**After configuration:**
- Save the file
- Completely quit Claude Desktop (not just close the window)
- Restart Claude Desktop to load the new MCP server
- You should see an MCP indicator in the bottom-right of the chat interface

</details>

<details>
<summary><strong>🔧 Other MCP-Compatible Tools</strong></summary>

For any other tool that supports MCP, use this standard configuration format:

```json
{
  "mcpServers": {
    "context-templates": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://detailer-api.supabase.co/functions/v1/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}",
        "--allow-http"
      ],
      "env": {
        "AUTH_HEADER": "Bearer dtl_public_eec1f1037008dc82ce9d314c3294fbcc0e3f5d5df315d8c6"
      }
    }
  }
}
```

Consult your tool's documentation for the specific configuration file location and format requirements.

</details>

---

**Important Notes:**
- After adding the configuration, **restart your IDE completely** (quit and reopen) for the changes to take effect
- For Cursor and Windsurf, you may need to **reload or refresh** the MCP servers panel after the first configuration
- Ensure you have **Node.js** installed on your system (required for `npx` command)
- If you encounter issues, check that the configuration file syntax is valid JSON

## Template Types

This repository is organized into three main categories of templates:

-   **`rules`**: Define coding standards, best practices, and style guides for various languages and frameworks (e.g., React, Python, TypeScript).
-   **`shortcuts`**: Provide quick actions and generators for common development tasks, like creating feature plans or generating PR descriptions.
-   **`workflows`**: Contain multi-step processes and guides for more complex development scenarios.

## Repository Structure

The templates are organized into directories based on their type:

```
templates/
├── rules/
│   └── cursor/
│       ├── react.yml
│       └── python.yml
├── shortcuts/
│   ├── pr_description_generation.yml
│   └── task_planning_and_feature_development.yml
└── workflows/
    └── example-workflow.yml
```

## Contributing

We welcome contributions! If you have a template that could benefit other developers, please feel free to open a pull request. (Contribution guidelines coming soon).

## Credits

A portion of the rules available in `templates/rules/cursor` are adapted from the collection at [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules/tree/main/rules-new) by [PatrickJS](https://github.com/PatrickJS). We are grateful for their contributions to the community.
