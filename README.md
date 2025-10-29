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

<input type="radio" id="tab-cursor" name="ide-tabs" checked="checked">
<input type="radio" id="tab-windsurf" name="ide-tabs">
<input type="radio" id="tab-claude" name="ide-tabs">
<input type="radio" id="tab-copilot" name="ide-tabs">
<input type="radio" id="tab-general" name="ide-tabs">

<div class="tabs">
  <label for="tab-cursor">Cursor</label>
  <label for="tab-windsurf">Windsurf</label>
  <label for="tab-claude">Claude Code</label>
  <label for="tab-copilot">Copilot</label>
  <label for="tab-general">General</label>
</div>

<div class="tab-content">
  <div class="tab-pane" id="content-cursor">
    
Add the following configuration to `~/.cursor/mcp.json`:

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

  </div>

  <div class="tab-pane" id="content-windsurf">
    
Add the following configuration to your Windsurf MCP settings file (typically `~/.windsurf/mcp.json` or in the Windsurf settings):

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

  </div>

  <div class="tab-pane" id="content-claude">
    
Add the following configuration to your Claude Code MCP settings:

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

  </div>

  <div class="tab-pane" id="content-copilot">
    
For GitHub Copilot, configure MCP in your Copilot settings (location may vary by installation):

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

  </div>

  <div class="tab-pane" id="content-general">
    
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

  </div>
</div>

<style>
input[type="radio"] { display: none; }
.tabs {
  display: flex;
  border-bottom: 1px solid #ddd;
  margin-bottom: 1rem;
}
.tabs label {
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  background: #f6f8fa;
  border: 1px solid #ddd;
  border-bottom: none;
  margin-right: 0.25rem;
  border-radius: 4px 4px 0 0;
  user-select: none;
}
.tabs label:hover {
  background: #e1e4e8;
}
input[type="radio"]:checked + .tabs label[for="tab-cursor"],
#tab-cursor:checked ~ .tabs label[for="tab-cursor"],
#tab-windsurf:checked ~ .tabs label[for="tab-windsurf"],
#tab-claude:checked ~ .tabs label[for="tab-claude"],
#tab-copilot:checked ~ .tabs label[for="tab-copilot"],
#tab-general:checked ~ .tabs label[for="tab-general"] {
  background: white;
  border-bottom: 1px solid white;
  margin-bottom: -1px;
  position: relative;
  z-index: 1;
}
.tab-content {
  position: relative;
}
.tab-pane {
  display: none;
  padding: 1rem 0;
}
#tab-cursor:checked ~ .tab-content #content-cursor,
#tab-windsurf:checked ~ .tab-content #content-windsurf,
#tab-claude:checked ~ .tab-content #content-claude,
#tab-copilot:checked ~ .tab-content #content-copilot,
#tab-general:checked ~ .tab-content #content-general {
  display: block;
}
</style>

**Note:** After adding the configuration, restart your IDE or reload the MCP servers for the changes to take effect.

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
