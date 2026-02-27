# TypeSpec for Declarative Agents

TypeSpec is a strongly-typed API description language that compiles to declarative agent manifests. Available in Microsoft 365 Agents Toolkit v6.0+.

## Overview
- Select "Start with TypeSpec for Microsoft 365 Copilot" in Agents Toolkit
- Write agent definition in `main.tsp` file
- Run **Provision** in the Lifecycle pane -- TypeSpec compiles to JSON manifests
- Generates both declarativeAgent.json and apiDefinition.json from a single source

## Agent Definition
```typescript
@agent("Agent Name", "Agent description up to 1000 chars")
@instructions("""
  # Role
  You are a helpful assistant.

  # Workflow
  ## Step 1: Gather information
  - **Goal:** Understand the user's request.
  - **Action:** Ask clarifying questions if needed.
""")
namespace MyAgent {
}
```

## Conversation Starters
```typescript
@conversationStarter(#{
  title: "Getting started",
  text: "How can I get started?"
})
@conversationStarter(#{
  title: "Search",
  text: "Find information about..."
})
```

## Capability Decorators

### WebSearch
```typescript
// Unrestricted
op webSearch is AgentCapabilities.WebSearch;

// With site restriction
op webSearch is AgentCapabilities.WebSearch<Sites = [{
  url: "https://learn.microsoft.com"
}]>;
```

### OneDriveAndSharePoint
```typescript
// By URL
op odsp is AgentCapabilities.OneDriveAndSharePoint<ItemsByUrl = [{
  url: "https://contoso.sharepoint.com/sites/ProductSupport"
}]>;

// By SharePoint IDs
op odsp is AgentCapabilities.OneDriveAndSharePoint<
  ItemsBySharePointIds = [{
    site_id: "guid"; web_id: "guid"; list_id: "guid"; unique_id: "guid";
  }],
  ItemsByUrl = [{ url: "https://contoso.sharepoint.com/sites/Docs" }]
>;
```

### Copilot Connectors (GraphConnectors)
```typescript
op connectors is AgentCapabilities.CopilotConnectors<Connections = [{
  connectionId: "jiraCloudConnection"
}]>;
```
Note: TypeSpec uses camelCase (`connectionId`) while JSON uses snake_case (`connection_id`). The compiler handles the translation.

### GraphicArt (Image Generator)
```typescript
op graphicArt is AgentCapabilities.GraphicArt;
```

### CodeInterpreter
```typescript
op codeInterpreter is AgentCapabilities.CodeInterpreter;
```

### TeamsMessages
```typescript
op teamsMessages is AgentCapabilities.TeamsMessages<TeamsMessagesByUrl = [{
  url: "https://teams.microsoft.com/l/channel/19%3A...%40thread.tacv2/General?..."
}]>;
```

### Email
```typescript
op email is AgentCapabilities.Email<Folders = [{
  folder_id: "Inbox"
}]>;
```

### People
```typescript
op people is AgentCapabilities.People;
```

### Meetings
```typescript
op meetings is AgentCapabilities.Meetings;
```

## API Plugin Actions
```typescript
@service
@server("https://api.example.com")
@actions(#{
  nameForHuman: "Resource Manager",
  descriptionForHuman: "Manage resources and tasks.",
  descriptionForModel: "Use when the user wants to search, create, or manage resources."
})
namespace ResourceAPI {
  @route("/api/v1/resources/search")
  @post
  op searchResources(
    @body body: {
      query: string;
      max_results?: int32;
    }
  ): {
    results: Resource[];
  };
}

model Resource {
  id: int32;
  name: string;
  status: string;
}
```

## Advantages
- Type safety and compile-time validation
- Single source of truth -- no manual JSON sync between files
- IDE support via VS Code extension (autocomplete, error highlighting)
- Generates both agent manifest and OpenAPI spec from one file
- Eliminates the 4-file sync problem when adding API tools

## Caveats
- camelCase in TypeSpec maps to snake_case in JSON (compiler handles translation)
- Requires Microsoft 365 Agents Toolkit v6.0+
- Less flexible than manual JSON for edge cases
- Learning curve if unfamiliar with TypeSpec syntax
