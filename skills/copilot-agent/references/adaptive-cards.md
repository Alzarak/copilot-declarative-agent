# Adaptive Card Templates

How to render rich responses from API plugins using Adaptive Cards in Microsoft 365 Copilot.

## Overview

Adaptive Cards provide structured visual rendering of API function responses. Configure them in the `response_semantics` property of a function in `apiPlugin.json`.

## Configuration

```json
{
  "name": "searchResources",
  "description": "Search for resources.",
  "capabilities": {
    "response_semantics": {
      "data_path": "$.results",
      "properties": {
        "title": "$.name",
        "subtitle": "$.status",
        "url": "$.href",
        "thumbnail_url": "$.imageUrl",
        "information_protection_label": "$.ipLabel"
      },
      "static_template": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
          {
            "type": "TextBlock",
            "text": "${name}",
            "weight": "Bolder",
            "size": "Medium"
          },
          {
            "type": "TextBlock",
            "text": "${description}",
            "wrap": true
          },
          {
            "type": "FactSet",
            "facts": [
              { "title": "Status", "value": "${status}" },
              { "title": "Priority", "value": "${priority}" }
            ]
          }
        ],
        "actions": [
          {
            "type": "Action.OpenUrl",
            "title": "View Details",
            "url": "${href}"
          }
        ]
      }
    }
  }
}
```

## Properties

### data_path
JSONPath (RFC 9535) pointing to the result array in the API response.
- `"$.results"` -- root-level `results` array
- `"$"` -- response is the array itself

### Semantic Properties
Map JSONPath expressions to semantic fields:

| Property | Purpose |
|----------|---------|
| `title` | Primary display text |
| `subtitle` | Secondary display text |
| `url` | Link to the resource |
| `thumbnail_url` | Image URL for thumbnails |
| `information_protection_label` | Sensitivity label |
| `template_selector` | Dynamic template selection |

### oauth_card_path
Optional property for OAuth card rendering when authentication is needed.

## Three Template Modes

### 1. Inline Static Template
Template defined directly in the function's `response_semantics`:
```json
"static_template": {
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [...]
}
```

### 2. File Reference (v2.4+)
Template in a separate file:
```json
"static_template": { "file": "./adaptive-cards/search-result.json" }
```
File path is relative to the appPackage directory. Keeps apiPlugin.json cleaner.

### 3. Dynamic via template_selector
Different templates based on response data. The `template_selector` property in semantic properties maps a JSONPath to a field that determines which template to use.

## Data Binding Syntax
Use `${fieldName}` to reference fields from the API response:
- `${name}` -- simple field
- `${status}` -- another field
- Fields come from objects in the array pointed to by `data_path`

## Example: Ticket Search Card
```json
{
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    {
      "type": "TextBlock",
      "text": "#${ticketNumber}: ${title}",
      "weight": "Bolder"
    },
    {
      "type": "ColumnSet",
      "columns": [
        {
          "type": "Column",
          "items": [{ "type": "TextBlock", "text": "Status: ${status}" }]
        },
        {
          "type": "Column",
          "items": [{ "type": "TextBlock", "text": "Priority: ${priority}" }]
        }
      ]
    }
  ],
  "actions": [
    { "type": "Action.OpenUrl", "title": "Open Ticket", "url": "${webUrl}" }
  ]
}
```

## Best Practices
- Keep cards concise -- show key fields, link to details
- Use FactSet for structured key-value data
- Use ColumnSet for side-by-side layout
- Always include an Action.OpenUrl for the source record
- Test with various data shapes (missing fields, long text, special characters)
