# DETAILS.md

🔍 **Powered by [Detailer](https://detailer.ginylil.com)** - Smart agent-compatible documentation



---

## 1. Project Overview

### Purpose & Domain

**context-templates** is a **YAML-driven configuration and templating system** designed to define, manage, and enforce **coding standards, best practices, workflow automation, and documentation templates** across multiple programming languages and technology stacks.

- **Problem Addressed:**  
  Ensures consistent application of coding standards, project workflows, and documentation practices by externalizing rules and templates into declarative YAML files. This reduces manual enforcement overhead, improves code quality, and accelerates developer onboarding.

- **Target Users:**  
  - Developers and teams working across diverse tech stacks (Python, JavaScript, Rust, Vue, React, Tailwind CSS, etc.)  
  - DevOps and CI/CD engineers automating code quality checks and deployment workflows  
  - Documentation engineers and AI-assisted tooling systems that generate or validate project documentation and changelogs  
  - Tool builders integrating static analysis, linting, or template generation engines

- **Use Cases:**  
  - Defining and enforcing language/framework-specific coding standards  
  - Automating generation of documentation, changelogs, and test skeletons via shortcut templates  
  - Integrating with CI/CD pipelines to validate and push templates automatically  
  - Serving as a backend for AI-powered assistants or static analysis tools (e.g., Detailer) to guide developers

- **Core Business Logic & Domain Models:**  
  The project does not contain executable business logic but models **rules, shortcuts, and workflows as YAML templates** with rich metadata. These templates encapsulate domain knowledge such as SDK usage, code quality guidelines, project structures, and automation workflows.

---

## 2. Architecture and Structure

### High-Level Architecture

- **Template-Driven Configuration System:**  
  The entire project is architected around **declarative YAML templates** that define rules, shortcuts, and workflows. These templates are consumed by external tools or automation engines to enforce standards, generate content, or automate processes.

- **Separation of Concerns:**  
  - **Rules Templates (`templates/rules/cursor/`):** Define coding standards and best practices per language or framework.  
  - **Shortcuts Templates (`templates/shortcuts/`):** Define reusable automation snippets for documentation, changelogs, and testing.  
  - **Workflows Templates (`templates/workflows/`):** Define process automation steps and CI/CD workflows.  
  - **Scripts (`scripts/`):** Provide utility functions for environment setup, template preparation, and pushing templates to external APIs.  
  - **CI/CD (`.github/workflows/`):** Automate template deployment and validation.

- **Integration Points:**  
  The system integrates with external APIs (for pushing templates), CI/CD pipelines (GitHub Actions), and likely AI or static analysis tools (e.g., Detailer) that consume these YAML templates.

---

### Complete Repository Structure

```
.
├── .github/
│   └── workflows/
│       └── push_templates.yml
├── scripts/
│   ├── dotenv.sh
│   ├── prepare_rules.py
│   └── push_templates.py
├── templates/ (36 items)
│   ├── rules/ (21 items)
│   │   ├── cursor/ (18 items)
│   │   │   ├── beefreeSDK.yml
│   │   │   ├── clean-code.yml
│   │   │   ├── codequality.yml
│   │   │   ├── cpp.yml
│   │   │   ├── database.yml
│   │   │   ├── fastapi.yml
│   │   │   ├── gitflow.yml
│   │   │   ├── medusa.yml
│   │   │   ├── nativescript.yml
│   │   │   ├── nextjs.yml
│   │   │   ├── node-express.yml
│   │   │   ├── python.yml
│   │   │   ├── react.yml
│   │   │   ├── rust.yml
│   │   │   ├── svelte.yml
│   │   │   ├── tailwind.yml
│   │   │   ├── typescript.yml
│   │   │   └── vue.yml
│   │   ├── example-rule.yml
│   │   └── schema.yml
│   ├── shortcuts/ (10 items)
│   │   ├── api_endpoint_doc.yml
│   │   ├── bug_repro_template.yml
│   │   ├── changelog_entry.yml
│   │   ├── code_review_checklist.yml
│   │   ├── env_cheatsheet.yml
│   │   ├── example-shortcut.yml
│   │   ├── pr_description_generation.yml
│   │   ├── schema.yml
│   │   ├── task_planning_and_feature_development.yml
│   │   └── unit_test_skeleton.yml
│   └── workflows/
│       ├── example-workflow.yml
│       └── schema.yml
├── .gitignore
├── Makefile
├── README.md
├── env.template
└── requirements.txt
```

---

### Directory Responsibilities

| Directory / File Path           | Responsibility / Role                                                                                  |
|--------------------------------|------------------------------------------------------------------------------------------------------|
| `.github/workflows/`            | GitHub Actions workflows for CI/CD automation (e.g., pushing templates)                              |
| `scripts/`                     | Utility scripts for environment setup (`dotenv.sh`), rule preparation (`prepare_rules.py`), and pushing templates (`push_templates.py`) |
| `templates/rules/cursor/`       | YAML rule templates defining coding standards and best practices per language/framework               |
| `templates/shortcuts/`          | YAML shortcut templates for automating documentation, changelogs, code reviews, and test skeletons   |
| `templates/workflows/`          | Workflow templates defining automation steps and processes                                           |
| `Makefile`                     | Project-level automation for environment setup, dependency management, formatting, linting, and deployment |
| `env.template`                 | Template for environment variable configuration                                                      |
| `requirements.txt`             | Python dependencies for scripts and tooling                                                          |

---

## 3. Technical Implementation Details

### Template Types & Content

- **Rule Templates (`templates/rules/cursor/*.yml`):**  
  - Define **best practices, coding standards, and project conventions** for specific languages or frameworks (e.g., FastAPI, Gitflow, Tailwind CSS, TypeScript, Vue).  
  - Contain metadata fields:  
    - `template_type: "rule"`  
    - `template_subtype: "cursor"`  
    - `name`, `description`, `language`, `scope` (usually `"file"`)  
    - `globs`: file patterns to which the rules apply (e.g., `**/*.py`, `src/**/*.ts`)  
  - Content is structured as markdown-like bullet points describing guidelines, project structure, security, testing, deployment, and workflow rules.  
  - No executable code; purely declarative.

- **Shortcut Templates (`templates/shortcuts/*.yml`):**  
  - Define **automation snippets or templates** for generating documentation, changelogs, bug reports, API docs, and test skeletons.  
  - Metadata includes:  
    - `template_type: "shortcut"`  
    - `name`, `filename`, `short_description`, `long_description`  
    - `when`: triggers or user prompts activating the shortcut  
    - `then`: instructions or actions to perform  
    - `examples` and `output_example` for usage illustration  
  - Used by template engines or AI assistants to generate content based on user input or system events.

- **Workflow Templates (`templates/workflows/*.yml`):**  
  - Define **process automation steps** for CI/CD or internal workflows.  
  - Include ordered `steps` with instructions and conditions.  
  - Validated against schemas to ensure consistency.

---

### Scripts & Automation

- **`scripts/dotenv.sh`**  
  - Shell script that reads environment variables from a source file and updates a target `.env` file accordingly.  
  - Supports environment setup for local development or CI.

- **`scripts/prepare_rules.py`**  
  - Python script that converts raw markdown rule files (`.mdc`) into enriched YAML files with metadata frontmatter.  
  - Automates standardization of rule templates.

- **`scripts/push_templates.py`**  
  - Python script that reads templates from the `templates/` directory and pushes them to an external API endpoint.  
  - Handles authentication via environment variables and error handling.

---

### Makefile

- Provides **developer and CI automation** for:  
  - Environment preparation (`prepare`, `prepare-dotenv`)  
  - Dependency installation (`install`, `requirements-update`)  
  - Code formatting and linting (`format`, `lint`)  
  - Template deployment (`push-templates`)  
- Detects OS and adapts virtual environment activation accordingly.  
- Validates required environment variables before running commands.

---

## 4. Development Patterns and Standards

### Code Organization Principles

- **Declarative Configuration:**  
  All rules, shortcuts, and workflows are defined as YAML templates, separating configuration from code logic.

- **Modularity:**  
  Rules and shortcuts are organized by technology and purpose, enabling easy extension and maintenance.

- **Schema-Driven Validation:**  
  Schema files (`schema.yml`) define the structure and required fields for templates, ensuring consistency.

- **Separation of Concerns:**  
  - Rules focus on standards and best practices.  
  - Shortcuts focus on automation and content generation.  
  - Workflows focus on process automation.

### Testing Strategies

- No explicit test code present in the repository.  
- Quality is enforced via linting (`ruff`) and formatting targets in the Makefile.  
- Rules and shortcuts serve as documentation and guidance, indirectly supporting quality.

### Error Handling and Logging

- Scripts (`push_templates.py`) include error handling for API interactions and file parsing.  
- `dotenv.sh` logs info and errors during environment variable injection.  
- Makefile targets validate environment variables before execution.

### Configuration Management

- Environment variables are managed via `.env` files, with templates provided (`env.template`).  
- Makefile automates `.env` preparation and environment setup.  
- Scripts and workflows rely on environment variables for API URLs and tokens.

---

## 5. Integration and Dependencies

### External Libraries and Tools

- **Python Libraries:**  
  - `PyYAML` for YAML parsing and dumping in scripts.  
  - `requests` for HTTP API interactions in `push_templates.py`.

- **CLI Tools:**  
  - `python` and `pip` for environment and dependency management.  
  - `ruff` for code formatting and linting.

- **GitHub Actions:**  
  - `.github/workflows/push_templates.yml` automates template deployment in CI.

### Database or Storage

- No direct database integration; templates are stored as files in the repository.

### API Dependencies

- External API endpoints for pushing templates, configured via environment variables (`TEMPLATE_API_URL`, `TEMPLATE_API_TOKEN`).

### Build and Deployment Dependencies

- Makefile orchestrates build and deployment steps.  
- CI/CD pipeline uses GitHub Actions to run Makefile targets.

---

## 6. Usage and Operational Guidance

### Getting Started

1. **Setup Environment:**  
   - Copy `env.template` to `.env` and fill in required variables (e.g., API tokens).  
   - Run `make prepare` to create and activate a Python virtual environment.  
   - Run `make install` to install dependencies.

2. **Working with Templates:**  
   - Rule templates are located in `templates/rules/cursor/`.  
   - Shortcut templates are in `templates/shortcuts/`.  
   - Workflow templates are in `templates/workflows/`.

3. **Generating or Updating Rules:**  
   - Use `scripts/prepare_rules.py` to convert raw markdown rules into YAML templates.

4. **Pushing Templates:**  
   - Run `make push-templates` to deploy templates to the configured API.

5. **Code Quality:**  
   - Use `make format` and `make lint` to format and lint code/scripts.

### Extending the Project

- **Adding New Rules or Shortcuts:**  
  - Create new YAML files following the existing schema in the appropriate directory.  
  - Validate against `schema.yml` to ensure correctness.

- **Modifying Scripts:**  
  - Scripts are self-contained and can be extended for additional automation tasks.

- **CI/CD Integration:**  
  - Modify `.github/workflows/push_templates.yml` to customize deployment workflows.

### Performance and Scalability

- The project is primarily configuration-driven; performance depends on the consuming tools and APIs.  
- Scalability is supported by modular templates and schema validation, enabling large-scale multi-language support.

### Security Considerations

- API tokens and sensitive data are managed via environment variables and `.env` files.  
- Scripts and workflows avoid hardcoding secrets.  
- Guidelines in rule templates include security best practices for various frameworks.

### Monitoring and Observability

- No explicit monitoring tools included; observability depends on external CI/CD and API systems.  
- Logs from scripts and CI runs provide operational insights.

---

## Summary

**context-templates** is a **comprehensive YAML-based templating and rules system** designed to standardize coding practices, automate documentation and workflows, and integrate with CI/CD pipelines and AI-assisted tooling. Its modular, declarative architecture enables multi-language support and flexible extension, making it a powerful foundation for enforcing quality and accelerating development workflows in diverse projects.

---

# End of DETAILS.md