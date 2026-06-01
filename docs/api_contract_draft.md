# API Contract Draft — Filet Crochet Pattern Generator

## 1. Purpose

This document defines the draft API contract for version 1 of the filet crochet pattern generator backend.

The backend:

* accepts structured JSON input
* validates the request
* generates a filet crochet scheme
* returns the result as JSON

Version 1 supports only one main generation endpoint and one health endpoint.

---

## 2. Base Principles

* Transport: HTTP
* Payload format: JSON
* API style: synchronous request-response
* Authentication: not required in v1
* Persistence: not required in v1

---

## 3. Endpoints

## 3.1. Health Check

### Request

`GET /health`

### Success Response

Status: `200 OK`

```json id="qj1g3q"
{
  "status": "ok"
}
```

---

## 3.2. Generate Scheme

### Request

`POST /api/v1/schemes/generate`

### Request Body

```json id="vqez9q"
{
  "text": "home sweet home",
  "scheme": {
    "width": {
      "min": 120,
      "max": 150
    },
    "height": {
      "min": 160,
      "max": 200
    }
  },
  "symbol": {
    "width": {
      "min": 15,
      "max": 25
    },
    "height": {
      "min": 30,
      "max": 40
    }
  }
}
```

---

## 4. Request Contract

## 4.1. Root Object

Fields:

* `text: string`
* `scheme: SchemeConstraintsDto`
* `symbol: SymbolConstraintsDto`

---

## 4.2. `text`

Rules:

* required
* must be a string
* must not be empty after normalization
* may include:

  * Latin characters
  * Cyrillic characters
  * digits
  * punctuation
  * spaces

Example:

```json id="mo5x91"
{
  "text": "home sweet home"
}
```

---

## 4.3. `scheme`

Structure:

```json id="3d0b1a"
{
  "scheme": {
    "width": {
      "min": 120,
      "max": 150
    },
    "height": {
      "min": 160,
      "max": 200
    }
  }
}
```

Rules:

* required
* contains `width` and `height`
* each dimension contains `min` and `max`
* all values must be positive integers
* `min <= max`

---

## 4.4. `symbol`

Structure:

```json id="315jdb"
{
  "symbol": {
    "width": {
      "min": 15,
      "max": 25
    },
    "height": {
      "min": 30,
      "max": 40
    }
  }
}
```

Rules:

* required
* contains `width` and `height`
* each dimension contains `min` and `max`
* all values must be positive integers
* `min <= max`

---

## 5. Success Response Contract

Status: `200 OK`

### Response Body

```json id="lm2xj4"
{
  "width": 132,
  "height": 176,
  "cells": [
    [null, null, 1, 1, null],
    [null, 1, 0, 0, 1],
    [1, 0, 1, 0, 1]
  ],
  "meta": {
    "normalized_text": "home sweet home",
    "lines": [
      "home",
      "sweet",
      "home"
    ],
    "symbol_size": {
      "width": 18,
      "height": 32
    },
    "letter_spacing": 4,
    "line_spacing": 2,
    "overflow": {
      "width_ratio": 0.0,
      "height_ratio": 0.0
    }
  }
}
```

---

## 6. Success Response Fields

## 6.1. Root Fields

* `width: int`
* `height: int`
* `cells: SchemeMatrix`
* `meta: object`

---

## 6.2. `width`

Final scheme width in cells.

Rules:

* positive integer
* equals the number of columns in `cells`

---

## 6.3. `height`

Final scheme height in cells.

Rules:

* positive integer
* equals the number of rows in `cells`

---

## 6.4. `cells`

The final rectangular scheme matrix.

Allowed values:

* `null`
* `0`
* `1`

Rules:

* required
* must be a 2D array
* all rows must have equal length
* row count must equal `height`
* column count must equal `width`

Semantics:

* `null` — invisible cell
* `0` — empty crochet cell
* `1` — filled crochet cell

---

## 6.5. `meta`

Metadata about generation result.

Draft fields:

* `normalized_text: string`
* `lines: string[]`
* `symbol_size: { width: int, height: int }`
* `letter_spacing: int`
* `line_spacing: int`
* `overflow: { width_ratio: float, height_ratio: float }`

The `meta` object is included to support frontend rendering, debugging, and future diagnostics.

---

## 7. Error Response Contract

All error responses must return JSON.

Draft common shape:

```json id="pz6jcb"
{
  "error": {
    "code": "SOME_ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  }
}
```

---

## 8. Error Types

## 8.1. Validation Error

Status: `422 Unprocessable Entity`

Used when request structure or field values are invalid.

Examples:

* missing required field
* negative dimension
* `min > max`
* wrong data type

Example:

```json id="lptqf3"
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field": "scheme.width.min"
    }
  }
}
```

---

## 8.2. Unsupported Character Error

Status: `400 Bad Request`

Used when text contains unsupported characters.

Example:

```json id="qxeypp"
{
  "error": {
    "code": "UNSUPPORTED_CHARACTERS",
    "message": "Text contains unsupported characters",
    "details": {
      "characters": ["@", "#"]
    }
  }
}
```

---

## 8.3. Empty Text Error

Status: `400 Bad Request`

Used when text becomes empty after normalization.

Example:

```json id="iwsf85"
{
  "error": {
    "code": "EMPTY_TEXT",
    "message": "Text is empty after normalization",
    "details": {}
  }
}
```

---

## 8.4. Generation Failed Error

Status: `422 Unprocessable Entity`

Used when request is valid, but no valid scheme can be generated.

Examples:

* no valid symbol size
* no valid layout
* all candidates exceed allowed overflow

Example:

```json id="9wydjh"
{
  "error": {
    "code": "GENERATION_FAILED",
    "message": "Unable to generate scheme within constraints",
    "details": {
      "reason": "No valid layout found"
    }
  }
}
```

---

## 8.5. Internal Server Error

Status: `500 Internal Server Error`

Used for unexpected server-side failures.

Example:

```json id="s2qn0a"
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Unexpected internal error",
    "details": {}
  }
}
```

---

## 9. Validation Rules Summary

The API must validate:

* request body is valid JSON
* `text` exists and is a string
* `scheme.width.min`, `scheme.width.max`, `scheme.height.min`, `scheme.height.max` are positive integers
* `symbol.width.min`, `symbol.width.max`, `symbol.height.min`, `symbol.height.max` are positive integers
* for every dimension, `min <= max`

Generation-specific validation:

* normalized text must not be empty
* all characters must be supported
* generator must find a valid layout candidate

---

## 10. Example Requests

## 10.1. Valid Request

```json id="0cz1rm"
{
  "text": "home sweet home",
  "scheme": {
    "width": {
      "min": 120,
      "max": 150
    },
    "height": {
      "min": 160,
      "max": 200
    }
  },
  "symbol": {
    "width": {
      "min": 15,
      "max": 25
    },
    "height": {
      "min": 30,
      "max": 40
    }
  }
}
```

## 10.2. Invalid Request: Wrong Range

```json id="f0qmwt"
{
  "text": "home sweet home",
  "scheme": {
    "width": {
      "min": 160,
      "max": 120
    },
    "height": {
      "min": 160,
      "max": 200
    }
  },
  "symbol": {
    "width": {
      "min": 15,
      "max": 25
    },
    "height": {
      "min": 30,
      "max": 40
    }
  }
}
```

## 10.3. Invalid Request: Unsupported Characters

```json id="9u5x2z"
{
  "text": "home ♥ home",
  "scheme": {
    "width": {
      "min": 120,
      "max": 150
    },
    "height": {
      "min": 160,
      "max": 200
    }
  },
  "symbol": {
    "width": {
      "min": 15,
      "max": 25
    },
    "height": {
      "min": 30,
      "max": 40
    }
  }
}
```

---

## 11. Open Draft Decisions

The following details are still implementation-level decisions and may be refined later without changing the general contract:

* exact normalization algorithm
* exact scoring formula for candidate selection
* exact `meta` field set
* exact structure of validation error details
* whether `overflow` is mandatory in every success response or optional

---

## 12. Versioning

This contract is a draft for API version 1.

Recommended route prefix:

* `/api/v1`

Future breaking changes should be introduced under a new version prefix.

---
