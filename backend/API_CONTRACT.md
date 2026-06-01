# API_CONTRACT.md

## Endpoints

### GET /health

```json
{ "status": "ok" }
```

---

### POST /api/v1/schemes/generate

Request:

```json
{
  "text": "home sweet home",
  "scheme": {
    "width": { "min": 120, "max": 150 },
    "height": { "min": 160, "max": 200 }
  },
  "symbol": {
    "width": { "min": 15, "max": 25 },
    "height": { "min": 30, "max": 40 }
  }
}
```

Response:

```json
{
  "width": 132,
  "height": 176,
  "cells": [[null,1,1],[1,0,1]],
  "meta": {}
}
```

---

## Ошибки

```json
{
  "error": {
    "code": "ERROR",
    "message": "Описание",
    "details": {}
  }
}
```

Коды:

* VALIDATION_ERROR
* EMPTY_TEXT
* UNSUPPORTED_CHARACTERS
* GENERATION_FAILED
* INTERNAL_ERROR
