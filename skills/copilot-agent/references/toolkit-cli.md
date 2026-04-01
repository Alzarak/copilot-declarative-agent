# Microsoft 365 Agents Toolkit CLI Reference

## Installation

```bash
npm install -g @microsoft/m365agentstoolkit-cli
atk -h
```

The CLI binary is `atk`. All commands support `--interactive -i` (default true), `--debug`, `--verbose`.

## Authentication

```bash
atk auth login        # Log in to M365/Azure
atk auth list         # Show connected accounts
atk auth logout m365  # Log out of M365
atk auth logout azure # Log out of Azure
```

## Project Lifecycle Commands

### Create (`atk new`)

```bash
# Interactive (recommended for first-time)
atk new

# Non-interactive declarative agent
atk new -c declarative-agent -l typescript -n myagent -i false

# From sample
atk new sample
```

**Parameters:**
| Flag | Required | Description |
|------|----------|-------------|
| `--app-name -n` | Yes | Application name |
| `--capability -c` | Yes | App type: `declarative-agent`, `basic-custom-engine-agent`, `weather-agent`, etc. |
| `--programming-language -l` | No | `javascript` (default), `typescript`, `csharp` |
| `--folder -f` | No | Output directory (default `./`) |
| `--openapi-spec-location -a` | No | OpenAPI spec path for API-backed agents |
| `--api-operation -o` | No | Select API operations |

### Add Features (`atk add`)

```bash
atk add action              # Add API action to agent
atk add auth-config         # Add auth for actions
atk add capability          # Add capability to agent
atk add spfx-web-part       # Add SPFx web part
```

### Validate (`atk validate`)

```bash
# Schema validation (default)
atk validate --env dev

# Validation rules
atk validate --env dev --validate-method validation-rules

# Test cases
atk validate --env dev --validate-method test-cases

# Custom manifest path
atk validate --manifest-file ./appPackage/manifest.json
```

**Parameters:**
| Flag | Description |
|------|-------------|
| `--env` | Environment name |
| `--manifest-file` | Manifest path (default `./appPackage/manifest.json`) |
| `--package-file` | Zipped package path |
| `--validate-method -m` | `validation-rules` or `test-cases` |
| `--folder -f` | Project root (default `./`) |

### Provision (`atk provision`)

```bash
# Remote environment
atk provision --env dev

# Local environment
atk provision --env local
```

Runs the provision stage in `m365agents.yml` or `m365agents.local.yml`.

**Parameters:**
| Flag | Description |
|------|-------------|
| `--env` | Environment name |
| `--folder -f` | Project root (default `./`) |
| `--ignore-env-file` | Skip loading .env |

### Deploy (`atk deploy`)

```bash
atk deploy --env dev
atk deploy --env local
```

Runs the deploy stage in `m365agents.yml`.

**Parameters:**
| Flag | Required | Description |
|------|----------|-------------|
| `--env` | Yes | Environment name |
| `--folder -f` | No | Project root |
| `--config-file-path -c` | No | Custom YAML config path |

### Package (`atk package`)

```bash
atk package --env dev
atk package --env dev --output-folder ./dist
```

Builds the app into a zip package for publishing.

### Preview (`atk preview`)

```bash
# Local preview
atk preview --env local
atk preview --env local --browser chrome

# Remote preview
atk preview --env remote
atk preview --env remote --m365-host outlook
```

**Prerequisites:** Must run `atk provision` and `atk deploy` first.

**Parameters:**
| Flag | Description |
|------|-------------|
| `--m365-host -m` | `teams` (default), `outlook`, `office` |
| `--browser -b` | `chrome`, `edge`, `default` |
| `--desktop -d` | Open desktop client instead of web |
| `--env` | Environment (default `local`) |
| `--run-command -c` | Custom start command |

### Publish (`atk publish`)

```bash
atk publish --env dev
```

Runs the publish stage in `m365agents.yml`. Submits to org app catalog.

**Parameters:**
| Flag | Description |
|------|-------------|
| `--env` | Environment name |
| `--manifest-file` | Manifest path |
| `--package-file` | Zipped package path |

### Install (`atk install`)

```bash
# Upload package
atk install --file-path appPackage.zip

# Shared scope
atk install --file-path appPackage.zip --scope Shared
```

### Uninstall (`atk uninstall`)

```bash
atk uninstall -i false --mode manifest-id --manifest-id <id> --options 'm365-app,app-registration,bot-framework-registration'
atk uninstall -i false --mode title-id --title-id <id>
atk uninstall -i false --mode env --env dev --folder ./myapp
```

## Environment Management

```bash
atk env list                  # List environments
atk env add staging --env dev # Create staging from dev
atk env reset                 # Reset environment file
```

## Other Commands

```bash
atk doctor                    # Check prerequisites
atk list templates            # List app templates
atk list samples              # List app samples
atk upgrade                   # Upgrade project to latest toolkit
atk update --env dev          # Update manifest in Developer Portal
atk launchinfo --manifest-id <id>  # Get launch info
```

## Collaboration

```bash
atk collaborator status --env dev
atk collaborator grant --email user@org.com --env dev -i false
```

## Declarative Agent Workflow

For declarative agents, the typical lifecycle:

1. **Create**: `atk new -c declarative-agent -n myagent`
2. **Edit**: Modify `appPackage/declarativeAgent.json`, add capabilities/actions
3. **Validate**: `atk validate --env dev`
4. **Provision**: `atk provision --env local` (or `--env dev` for cloud)
5. **Deploy**: `atk deploy --env local`
6. **Preview**: `atk preview --env local`
7. **Package**: `atk package --env dev`
8. **Publish**: `atk publish --env dev`

## Add Features (`atk add`)

```bash
atk add action              # Add API action to extend Copilot
atk add auth-config         # Add auth config for declarative agent actions
atk add capability          # Add capability to agent
atk add spfx-web-part       # Add SPFx web part
```

## Configuration Files

The toolkit uses `m365agents.yml` (remote) and `m365agents.local.yml` (local) for lifecycle stages. Environment-specific variables are in `env/.env.{envname}`.

### Provision Actions (in m365agents.yml)

- `teamsApp/create` — Register app in Developer Portal
- `teamsApp/validateManifest` — Validate manifest schema
- `teamsApp/zipAppPackage` — Build app package
- `teamsApp/validateAppPackage` — Validate using rules
- `teamsApp/update` — Apply manifest to Developer Portal
- `aadApp/create` — Create Entra ID app
- `aadApp/update` — Update Entra ID app
- `arm/deploy` — Deploy Azure resources via ARM/Bicep
- `botFramework/create` — Create bot registration

### Deploy Actions (in m365agents.yml)

- `cli/runNpmCommand` — Run npm commands
- `cli/runDotnetCommand` — Run dotnet commands
- `azureAppService/zipDeploy` — Deploy to Azure App Service
- `azureFunctions/zipDeploy` — Deploy to Azure Functions
- `azureStorage/deploy` — Deploy to Azure Storage

## Validation Details

- **Schema validation** (default): Validates manifest.json against official schema
- **`validation-rules`**: Microsoft's publishing rules (static tab constraints, icon sizes, entity naming)
- **`test-cases`**: Store-readiness test scenarios
- **RAI checks**: Automatically run for declarative agents (instructions safety)

## Distribution Methods

| Method | Supported |
|--------|-----------|
| Sideload for personal use | Yes |
| Share with others | No |
| Submit to organizational catalog | Yes (via Teams admin center) |
| Submit to Microsoft Commercial Marketplace | Yes |
