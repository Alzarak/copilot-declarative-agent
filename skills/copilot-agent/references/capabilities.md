# Capabilities Reference

Capabilities define what knowledge sources and tools a declarative agent can access. Add them to the `capabilities` array in `declarativeAgent.json`.

Only add capabilities that align with the agent's goals. Less is more — focused agents perform better.

---

## 1. WebSearch

Enables web search grounding. Optionally restrict to specific sites.

```json
{ "name": "WebSearch" }
```

With site restriction (max 4 URLs):

```json
{
  "name": "WebSearch",
  "sites": [
    { "url": "https://learn.microsoft.com" },
    { "url": "https://contoso.com/docs" }
  ]
}
```

**URL constraints:**
- Max **4** sites
- Max **2 path segments** (e.g., `https://contoso.com/projects/mark-8` is valid, `https://contoso.com/projects/mark-8/beta` is NOT)
- No query parameters (`?key=value` not allowed)
- Search results include data from deeper segments but scoping is limited to 2 levels

---

## 2. OneDriveAndSharePoint

Knowledge from SharePoint sites, libraries, folders, and files.

By URL:

```json
{
  "name": "OneDriveAndSharePoint",
  "items_by_url": [
    { "url": "https://contoso.sharepoint.com/sites/ProductSupport" }
  ]
}
```

By SharePoint IDs:

```json
{
  "name": "OneDriveAndSharePoint",
  "items_by_sharepoint_ids": [
    {
      "site_id": "00000000-0000-0000-0000-000000000000",
      "web_id": "00000000-0000-0000-0000-000000000000",
      "list_id": "00000000-0000-0000-0000-000000000000",
      "unique_id": "00000000-0000-0000-0000-000000000000",
      "search_associated_sites": true,
      "part_type": "OneNotePart",
      "part_id": "00000000-0000-0000-0000-000000000000"
    }
  ]
}
```

| Property | Required | Notes |
|----------|----------|-------|
| `items_by_url[].url` | Yes (if used) | SharePoint or OneDrive URL |
| `items_by_sharepoint_ids[].site_id` | Yes | Site GUID |
| `search_associated_sites` | No | For HubSites (v1.6) |
| `part_type` | No | `"OneNotePart"` for OneNote pages (v1.6) |
| `part_id` | No | GUID of specific part (v1.6) |

**Limits:** Max 100 SharePoint files per agent. Permissions and sensitivity labels respected.

---

## 3. GraphConnectors (Copilot Connectors)

Access Microsoft Graph connector data sources.

Basic:

```json
{
  "name": "GraphConnectors",
  "connections": [
    { "connection_id": "jiraCloudConnection" }
  ]
}
```

With v1.6 filtering:

```json
{
  "name": "GraphConnectors",
  "connections": [
    {
      "connection_id": "servicenowKB",
      "additional_search_terms": "category:networking",
      "items_by_external_id": [{ "item_id": "KB0012345" }],
      "items_by_path": [{ "path": "/knowledge-base/networking" }],
      "items_by_container_name": [{ "container_name": "IT Knowledge Base" }],
      "items_by_container_url": [{ "container_url": "https://instance.service-now.com/kb" }]
    }
  ]
}
```

| Property | Required | Notes |
|----------|----------|-------|
| `connection_id` | Yes | Connector identifier |
| `additional_search_terms` | No | KQL query filter (v1.6) |
| `items_by_external_id` | No | Specific items by ID (v1.6) |
| `items_by_path` | No | Filter by path (v1.6) |
| `items_by_container_name` | No | Filter by container name (v1.6) |
| `items_by_container_url` | No | Filter by container URL (v1.6) |

**Supported connectors:** Azure DevOps, Confluence, Google Drive, GitHub, Jira, ServiceNow Knowledge/Catalog/Tickets, and custom connectors.

---

## 4. GraphicArt (Image Generator)

Creates images and art from text descriptions. No additional properties.

```json
{ "name": "GraphicArt" }
```

Good for content creation agents. Reference in instructions: "Use the image generator to create visuals."

---

## 5. CodeInterpreter

Generates and executes Python code for math, data analysis, and visualizations. No additional properties.

```json
{ "name": "CodeInterpreter" }
```

Good for data analysis agents. Reference in instructions: "Use code interpreter to generate charts and analyze data."

---

## 6. Dataverse

Search Dynamics 365 Dataverse tables.

```json
{
  "name": "Dataverse",
  "knowledge_sources": [
    {
      "host_name": "org0f612cfc.crm.dynamics.com",
      "skill": "AIBuilderFileAttachedData_e7eTReDbkX_1t4X1oGoCF",
      "tables": [
        { "table_name": "account" },
        { "table_name": "opportunity" }
      ]
    }
  ]
}
```

| Property | Required | Notes |
|----------|----------|-------|
| `host_name` | Yes | Organization hostname in Dataverse |
| `skill` | Yes | Identifier from Copilot Studio (see below) |
| `tables[].table_name` | Yes | Dataverse table identifier |

**Getting the `skill` value** requires Copilot Studio:
1. Open Copilot Studio > Agents > Copilot for Microsoft 365 > Add new agent
2. Add Dataverse knowledge source
3. Publish and download the .zip
4. Extract `declarativeAgent.json` for the `skill` value

---

## 7. TeamsMessages

Search Teams channels, chats, and meetings.

All Teams data:

```json
{ "name": "TeamsMessages" }
```

Scoped to specific chats/channels (max 5 URLs):

```json
{
  "name": "TeamsMessages",
  "urls": [
    { "url": "https://teams.microsoft.com/l/channel/19%3A...%40thread.tacv2/General?..." },
    { "url": "https://teams.microsoft.com/l/chat/19%3A...%40unq.gbl.spaces/0?..." }
  ]
}
```

| Property | Required | Notes |
|----------|----------|-------|
| `urls` | No | Max 5 Teams URLs. If omitted, searches all. |

URLs must be valid Teams links to channels, meeting chats, group chats, or 1:1 chats. Requires Copilot add-on license.

---

## 8. Email

Search mailboxes with optional scoping.

```json
{
  "name": "Email",
  "shared_mailbox": "support@contoso.com",
  "group_mailboxes": [
    "it-team@contoso.com",
    "helpdesk@contoso.com"
  ],
  "folders": [
    { "folder_id": "inbox" }
  ]
}
```

| Property | Required | Notes |
|----------|----------|-------|
| `shared_mailbox` | No | SMTP address of shared mailbox |
| `group_mailboxes` | No | Max **25** SMTP addresses (v1.6) |
| `folders[].folder_id` | No | Well-known folder name or folder ID |

Via Agent Builder: cannot scope (uses entire mailbox), shared users do NOT access your email.

---

## 9. People

Organizational data: name, position, skills, org relationships, contact details.

```json
{ "name": "People" }
```

With related content (v1.6):

```json
{
  "name": "People",
  "include_related_content": true
}
```

| Property | Required | Notes |
|----------|----------|-------|
| `include_related_content` | No | Includes related docs, emails, Teams messages (v1.6) |

Enabled by default for Copilot-licensed users. Reference in instructions: "Use people knowledge to fetch user contact details."

---

## 10. ScenarioModels

Task-specific models for specialized processing.

```json
{
  "name": "ScenarioModels",
  "models": [
    { "id": "model_identifier" }
  ]
}
```

| Property | Required | Notes |
|----------|----------|-------|
| `models[].id` | Yes | Task-specific model identifier |

---

## 11. Meetings

Meeting transcripts and calendar data.

All meetings:

```json
{ "name": "Meetings" }
```

Scoped to specific meetings (max 5):

```json
{
  "name": "Meetings",
  "items_by_id": [
    { "id": "meeting-immutable-id", "is_series": true },
    { "id": "another-meeting-id", "is_series": false }
  ]
}
```

| Property | Required | Notes |
|----------|----------|-------|
| `items_by_id` | No | Max 5 items. If omitted, searches all. (v1.6) |
| `items_by_id[].id` | Yes | Meeting immutable ID |
| `items_by_id[].is_series` | Yes | Whether it's a recurring series |

---

## 12. EmbeddedKnowledge (NOT YET AVAILABLE)

Local files bundled in the app package.

```json
{
  "name": "EmbeddedKnowledge",
  "files": [
    { "file": "knowledge/policies.docx" },
    { "file": "knowledge/faq.pdf" }
  ]
}
```

| Property | Required | Notes |
|----------|----------|-------|
| `files` | No | Max **10** files, max **1 MB** each |

**Supported file types:** .doc, .docx, .ppt, .pptx, .xls, .xlsx, .txt, .pdf

When embedded files are present, the `sensitivity_label` in declarativeAgent.json applies to the agent.
