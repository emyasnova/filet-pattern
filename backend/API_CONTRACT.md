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

### GET /api/v1/patterns

Optional query parameters:

* `search` — часть имени или тега;
* `category` — slug категории;
* `tags` — повторяемый параметр с AND-семантикой.

Response:

```json
[
  {
    "id": "83f9eefc-b6bc-5bdb-b521-c010422068ff",
    "name": "Rose",
    "category": "ornament",
    "tags": ["flower", "роза"],
    "width": 97,
    "height": 47,
    "cells": [[null, 1, 0]],
    "created_at": "2026-08-17T00:00:00Z"
  }
]
```

### GET /api/v1/categories

```json
[{ "slug": "alphabet", "name": "Алфавит" }]
```

### GET /api/v1/tags

```json
[{ "id": "6f68ca44-0999-578d-a772-078c702cec67", "name": "flower" }]
```

### POST /api/v1/patterns/preview

Multipart fields: `file`, `width`, `height`, optional `threshold` (default
`128`) and `fill_threshold` (default `0.35`).

```json
{
  "width": 34,
  "height": 26,
  "threshold": 128,
  "fill_threshold": 0.35,
  "cells": [[null, 1, 0]]
}
```

### POST /api/v1/patterns

```json
{
  "name": "rose",
  "category": "ornament",
  "tags": ["flower", "роза"],
  "width": 34,
  "height": 26,
  "cells": [[null, 1, 0]]
}
```

Ответ `201 Created` имеет формат обычного объекта паттерна. Новые теги
создаются автоматически. Внешний связный пустой фон нормализуется в `null`.

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
