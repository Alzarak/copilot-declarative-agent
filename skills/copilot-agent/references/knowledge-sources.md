# Knowledge Sources

## Overview

Knowledge sources provide grounding data for declarative agents. The orchestrator retrieves relevant information from configured sources to inform responses. Max 50 grounding records available per turn.

## Public Websites (WebSearch capability)

- Max 4 URLs, max 2 path levels deep, no query parameters
- Toggle "Search all websites" for unrestricted web search (no `sites` array)
- Example: `https://contoso.com/docs` is valid, `https://contoso.com/docs/api/v2` is NOT (3 levels)

## SharePoint and OneDrive (OneDriveAndSharePoint capability)

- Max 100 files per agent
- Permissions and sensitivity labels respected -- agent only retrieves content the user can access
- Excel works best with data in a single sheet per workbook
- Files can take minutes to be "ready" after upload (shows "Preparing" status)
- Renamed/deleted SharePoint files are picked up automatically
- URL format: `contoso.sharepoint.com/sites/policies` -- searches URL and all subpaths
- SharePoint File Picker: Cloud icon in Knowledge section > browse sites > select files/folders
- Communication sites only appear in Quick Access and Recent
- If Restricted SharePoint Search is enabled, SharePoint cannot be used as knowledge
- v1.6 adds `search_associated_sites` for HubSites, `part_type`/`part_id` for OneNote pages

## Embedded Files (Agent Builder uploads)

- Max 20 files, individual files only (no folders)
- NOT supported in GCC Moderate environments

| File Type | Max Size |
|-----------|----------|
| .doc/.docx | 512 MB |
| .pdf | 512 MB |
| .ppt/.pptx | 512 MB |
| .txt | 512 MB |
| .xls/.xlsx | 30 MB |
| .html | SharePoint Online only |

- Sensitivity labels: Highest-priority label from any embedded file applies to all embedded content
- Unsupported: Double key encryption, user-defined permissions, extract rights disabled, cross-tenant encrypted files, password-protected files

## Embedded Knowledge (App Package files -- NOT YET AVAILABLE)

- Max 10 files, max 1 MB each in the app package
- Supported: .doc, .docx, .ppt, .pptx, .xls, .xlsx, .txt, .pdf
- When present, `sensitivity_label` in declarativeAgent.json applies

## Teams Data (TeamsMessages capability)

- Toggle "My Teams chats and meetings" for all chats/transcripts/calendar
- Scope to specific chats (max 5 Teams URLs): team channels, group chats, meeting chats
- Cannot scope to individual meetings separately (use Meetings capability for that)
- Requires Microsoft 365 Copilot add-on license
- Use specific threads rather than all chats for less noise, more targeted results

## Email (Email capability)

- `shared_mailbox`: SMTP address of shared mailbox (optional)
- `group_mailboxes`: Array of SMTP addresses, max 25 (v1.6)
- `folders`: Scope by well-known folder name or folder ID
- Via Agent Builder: cannot scope (uses entire mailbox), shared users do NOT access your email

## People Data (People capability)

- Enabled by default for Copilot-licensed users
- Provides: name, position, skills, org relationships, contact details
- `include_related_content` (v1.6): When true, includes related documents, emails, and Teams messages between agent user and referenced people

## Meetings (Meetings capability)

- All meetings: omit `items_by_id`
- Scoped: max 5 meeting IDs with `is_series` flag
- Access to meeting transcripts and calendar data

## Copilot Connectors (GraphConnectors capability)

| Connector | Scope Attribute |
|-----------|----------------|
| Azure DevOps Work Items | Area path |
| Azure DevOps Wiki | Project |
| Confluence | Space |
| Google Drive | Folder |
| GitHub Cloud Pull Requests | Repository |
| GitHub Cloud Issues | Repository |
| GitHub Cloud Knowledge | Repository |
| Jira | Project |
| ServiceNow Knowledge | Knowledge base |
| ServiceNow Catalog | Catalog |
| ServiceNow Tickets | Entity type |

v1.6 filtering options for connections:

- `additional_search_terms`: KQL query to filter items
- `items_by_external_id`: Specific items by external ID
- `items_by_path`: Filter by item path
- `items_by_container_name`: Filter by container name
- `items_by_container_url`: Filter by container URL

## Knowledge Prioritization

- Toggle "Only use specified sources" in Configure tab
- Agent uses specified sources for search-based queries only
- Falls back to general AI for non-search questions (translate, math, etc.)
- For stricter control (blocking ALL general AI knowledge), use `behavior_overrides.special_instructions.discourage_model_knowledge: true` or Copilot Studio

## Best Practices

1. **Relevance over quantity** -- be selective about sources
2. **Less is more** for files -- focused documents perform better than large dumps
3. **Ensure content is up-to-date** and accurate
4. **Use specific Teams threads** rather than all chats (less noise, more targeted)
5. **Permissions matter** -- agent can only retrieve content the user has access to
6. **Test with and without** knowledge sources to verify behavior and isolate issues
7. **Excel files** work best with data in a single sheet per workbook
