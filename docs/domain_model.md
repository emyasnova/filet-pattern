# Domain Model — Filet Crochet Pattern Generator

## 1. Overview

The domain model defines the core entities and structures used to generate filet crochet schemes from text.

The system transforms:

* input text
  → glyphs
  → lines
  → final scheme matrix

---

## 2. Core Entities

### 2.1. SchemeRequest

Represents the input provided to the system.

Fields:

* `text: string`
* `scheme_constraints: SchemeConstraints`
* `symbol_constraints: SymbolConstraints`

---

### 2.2. SchemeConstraints

Defines allowed dimensions for the final scheme.

Fields:

* `width_min: int`
* `width_max: int`
* `height_min: int`
* `height_max: int`

---

### 2.3. SymbolConstraints

Defines allowed dimensions for glyphs.

Fields:

* `width_min: int`
* `width_max: int`
* `height_min: int`
* `height_max: int`

---

### 2.4. Glyph

Represents a single character as a matrix.

Fields:

* `char: string`
* `width: int`
* `height: int`
* `cells: CellMatrix` (2D array of `0` and `1`)

Rules:

* Glyph contains only `0` and `1`
* Glyph dimensions may vary per character
* Glyph must be rectangular

---

### 2.5. GlyphRepository

Storage of all available glyphs.

Responsibilities:

* provide glyph by character
* validate that character is supported

---

### 2.6. Line

Represents a horizontal composition of glyphs.

Fields:

* `glyphs: list[Glyph]`
* `cells: CellMatrix` (result of horizontal concatenation)

Rules:

* All glyphs in a line are aligned by top edge
* Line height = max glyph height in the line
* Shorter glyphs are padded with empty cells (`0`) vertically

---

### 2.7. Layout

Represents the result of splitting text into lines.

Fields:

* `lines: list[string]`

Rules:

* Each string is a sequence of characters
* Line breaking is automatic
* Words are kept intact where possible

---

### 2.8. ComposedLines

Intermediate structure after converting layout into matrices.

Fields:

* `lines: list[Line]`

---

### 2.9. Scheme

Final result of generation.

Fields:

* `width: int`
* `height: int`
* `cells: CellMatrix` (2D array of `null`, `0`, `1`)

Rules:

* Scheme matrix is rectangular
* Visible content may be non-rectangular (due to `null`)
* Lines are stacked vertically
* Vertical spacing may be applied between lines
* `null` is used to mark cells outside visible content

---

### 2.10. CellMatrix

Generic matrix type used across the system.

Variants:

#### Glyph matrix

* values: `0`, `1`

#### Line matrix

* values: `0`, `1`

#### Scheme matrix

* values: `null`, `0`, `1`

---

## 3. Transformations

The system performs the following transformations:

### Step 1: Text → Layout

Input text is split into lines:

* respects word boundaries where possible
* aims to fit constraints

---

### Step 2: Layout → Glyphs

Each character is mapped to a glyph via `GlyphRepository`.

---

### Step 3: Glyphs → Lines

Glyph matrices are:

* aligned by top
* padded vertically if needed
* concatenated horizontally

---

### Step 4: Lines → Scheme

Lines are:

* stacked vertically
* optionally spaced
* embedded into final matrix

---

### Step 5: Scheme normalization

Final adjustments:

* ensure rectangular matrix
* add `null` padding where needed
* compute final width and height

---

## 4. Validation Rules

### 4.1. Input validation

* text must not be empty
* all characters must be supported
* constraints must be valid ranges

---

### 4.2. Layout validation

* text must fit into scheme constraints
* symbol size must be within symbol constraints

---

### 4.3. Scheme validation

* resulting dimensions must be within (or slightly exceed) constraints
* matrix must be rectangular
* cell values must be valid

---

## 5. Assumptions

* All lines share the same vertical stacking logic
* Glyphs may vary in both width and height
* No alignment (center/left/right) is applied in v1
* No decorative elements are included
* Only text-based schemes are supported

---

## 6. Non-Domain Concerns (Excluded)

The domain model does not include:

* API layer
* serialization logic
* UI representation
* persistence
* rendering to images or PDF

---
