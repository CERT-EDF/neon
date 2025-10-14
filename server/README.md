# EDF Neon Server


## Introduction

This server implements the API for Neon service. It uses EDF Fusion framework as a library to ease maintainance and take advantage of new generic features as they become available.

> [!TIP]
> This documentation does not aim at completeness but provides an overview of the main features

## Events

Neon, when configured to do so, can emit events using webhooks. Here is a list of event's categories it can emit:

- `create_case`
- `update_case`
- `create_sample`
- `update_sample`

Event's structure looks like this:

```json
{
    "source": "event's source, service's name is often used as source",
    "category": "event's category, the nature of the event",
    "case": {},
    "ext": {},
}
```

