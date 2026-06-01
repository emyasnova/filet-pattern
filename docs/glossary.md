# Glossary — Filet Crochet Pattern Generator

## 1. Scheme

A scheme is the final result of the system.

It is represented as a 2D matrix of cells with values:

* `null` — invisible cell (outside the visible shape)
* `0` — empty crochet cell
* `1` — filled crochet cell

A scheme is logically a **non-rectangular shape embedded into a rectangular matrix**, where `null` values define areas outside the visible pattern.

---

## 2. Cell

A cell is the smallest unit of a scheme.

Possible values:

* `null` — not part of the visible scheme (not rendered)
* `0` — empty filet crochet cell
* `1` — filled filet crochet cell

---

## 3. Glyph

A glyph is a representation of a single character (letter, digit, or punctuation symbol).

A glyph is defined as a 2D matrix of cells:

* values: `0`, or `1`

Glyphs are used as building blocks to construct words and lines.

---

## 4. Text

Text is the raw input string provided by the user.

It may include:

* Latin characters
* Cyrillic characters
* digits
* punctuation

---

## 5. Line

A line is a sequence of glyphs composed into a single horizontal structure.

A line is represented as a 2D matrix formed by concatenating glyph matrices with spacing between them.

---

## 6. Layout

Layout is the result of splitting text into multiple lines.

It is represented as an ordered list of lines:

```text
["home", "sweet", "home"]
```

The layout defines:

* how many lines are used
* which words belong to each line

---

## 7. SchemeConstraints

Constraints applied to the entire scheme.

Includes:

* minimum and maximum width (in cells)
* minimum and maximum height (in cells)

These constraints define the target size range for the generated scheme.

---

## 8. SymbolConstraints

Constraints applied to individual glyphs.

Includes:

* minimum and maximum width (in cells)
* minimum and maximum height (in cells)

These constraints control how large or small each character can be rendered.

---

## 9. Composition

Composition is the process of assembling:

* glyphs → lines
* lines → scheme

This includes:

* horizontal concatenation of glyphs
* vertical stacking of lines
* applying spacing rules

---

## 10. Line Breaking

Line breaking is the process of splitting text into multiple lines.

It is performed automatically by the system based on:

* scheme constraints
* symbol constraints
* text length

---

## 11. Scheme Matrix

The scheme matrix is the final 2D array returned by the system.

It contains:

* dimensions (width, height)
* cell values (`null`, `0`, `1`)

This is the canonical representation of the generated crochet pattern.

---
