# Product Scope — Filet Crochet Pattern Generator (v1)

## 1. Purpose

The system is designed to generate filet crochet patterns from a textual input.

Primary goal:

* Quickly generate crochet-ready schemes from text without manual construction.

Secondary goal:

* Enable fast experimentation with different text inputs and layout constraints.

The system is initially intended for personal use, with possible future extension into a broader product.

---

## 2. Target User

* Single user (author of the project)
* The user is assumed to have prior knowledge of filet crochet patterns

---

## 3. Scope of Version 1 (MVP)

### Included functionality

The system must:

* Accept structured JSON input describing:

  * text content
  * scheme constraints (width and height ranges)
  * symbol constraints (letter dimensions)

* Generate a filet crochet scheme represented as a 2D matrix

* Use the following cell value semantics:

  * `null` — invisible cell (outside visible scheme shape)
  * `0` — empty crochet cell
  * `1` — filled crochet cell

* Support:

  * Latin alphabet
  * Cyrillic alphabet
  * digits
  * basic punctuation symbols

* Automatically:

  * split text into lines
  * select symbol size within constraints
  * fit layout within scheme constraints (with allowed minor overflow)

* Return:

  * generated scheme matrix
  * final scheme dimensions (width, height)

---

## 4. Input Format

The system accepts JSON input in the following form:

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

---

## 5. Output Format

The system returns JSON containing:

* generated scheme matrix
* scheme dimensions

Example:

```json
{
  "width": 132,
  "height": 176,
  "cells": [
    [null, null, 1, 1, null],
    [null, 1, 0, 0, 1],
    [1, 0, 1, 0, 1]
  ]
}
```

---

## 6. Layout Rules

* Text is automatically split into multiple lines if needed
* Line breaking is determined by the system
* Symbol size is selected within given constraints
* Layout must attempt to fit within scheme constraints
* Minor overflow beyond constraints is allowed

---

## 7. Error Handling

The system must return an error if:

* the text cannot be placed within constraints even with:

  * line splitting
  * symbol resizing within allowed bounds

No fallback or auto-relaxation beyond defined constraints is allowed.

---

## 8. Constraints and Limitations (v1)

The following features are explicitly out of scope:

* No image generation (PNG, SVG, etc.)
* No PDF export
* No persistence (no database, no storage of generated schemes)
* No authentication or user accounts
* No decorative elements (flowers, ornaments, etc.)
* No custom fonts or font selection
* No AI-based image generation
* No manual layout editing

---

## 9. Determinism

* The system generates a single scheme per request
* Exact determinism is not required
* Slight variations between runs are acceptable

---

## 10. Non-Goals

The system is not intended to:

* produce artistic or decorative compositions
* simulate real crochet rendering
* optimize for aesthetics beyond readability and correctness

---

## 11. Future Extensions (Not in v1)

Potential future features:

* multiple layout variants per request
* decorative elements (patterns, ornaments)
* export to image formats (PNG, SVG)
* PDF generation for printing
* interactive editing
* user accounts and storage
* AI-assisted layout suggestions

---
