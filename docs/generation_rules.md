# Generation Rules — Filet Crochet Pattern Generator

## 1. Purpose

This document defines the generation logic for transforming input text into a filet crochet scheme.

It describes:

* how text is split into lines
* how glyph sizes are selected
* how lines are composed
* how the final scheme is built
* how the best result is chosen

These rules are the source of truth for backend generation logic in v1.

---

## 2. Input Assumptions

The generator receives:

* input text
* scheme size constraints
* symbol size constraints

The generator operates only on text-based schemes.

Supported content:

* Latin characters
* Cyrillic characters
* digits
* punctuation

---

## 3. High-Level Pipeline

The generation process consists of these stages:

1. Normalize input text
2. Validate supported characters
3. Select candidate symbol sizes
4. Generate candidate line layouts
5. Compose glyphs into line matrices
6. Stack lines into a scheme matrix
7. Apply `null` padding outside visible content
8. Evaluate candidates
9. Return the best candidate or an error

---

## 4. Text Normalization Rules

Before layout generation:

* preserve original characters
* trim leading and trailing whitespace
* collapse repeated internal spaces into a single space
* preserve punctuation as part of the text
* preserve letter case unless explicitly changed by another rule set

If the resulting text is empty, generation must fail.

---

## 5. Character Validation Rules

Before generation starts:

* every character in the text must be supported by the glyph repository
* if at least one unsupported character is found, generation must fail

The error response must identify unsupported characters where possible.

---

## 6. Glyph Size Selection

## 6.1. General rule

The generator must search for a symbol size that fits within:

* `SymbolConstraints.width`
* `SymbolConstraints.height`

Glyphs may have different natural widths and heights, but the selected rendering process must ensure that every glyph stays within the selected symbol bounds for the current candidate.

## 6.2. Candidate sizes

The generator should evaluate multiple symbol size candidates within the allowed range.

A candidate symbol size consists of:

* target symbol width
* target symbol height

The search may iterate from larger symbols to smaller symbols, because larger readable symbols are preferred.

---

## 7. Word and Line Breaking Rules

## 7.1. Word boundary rule

Text must be split by words.

If a word does not fit in the current line:

* the word must be moved entirely to the next line

Words must not be split across lines in v1.

## 7.2. Single oversized word

If a single word cannot fit even on an empty line under the currently evaluated symbol size:

* that candidate is invalid

If no valid candidate exists across all allowed symbol sizes:

* generation must fail

## 7.3. Automatic line breaking

Line breaking is performed automatically by the system.

The generator must create candidate layouts that aim to fit text within scheme constraints while preserving whole words where possible.

---

## 8. Spacing Rules

## 8.1. Letter spacing

Letter spacing is fixed.

It is calculated as:

`letter_spacing = average_symbol_width // 4`

Where:

* `average_symbol_width` is the current candidate symbol width

The result should be converted to an integer and must remain stable during generation for a given candidate.

A practical lower bound of at least 1 cell is recommended.

## 8.2. Word spacing

Word spacing is represented by the glyph for the space character.

The space glyph is treated as a regular glyph during line composition.

## 8.3. Line spacing

Line spacing is required.

The system must insert vertical spacing between lines.

For v1, line spacing should be fixed for a given candidate and applied consistently across the scheme.

A simple implementation may use:

* 1 or more empty rows (`0`) between lines

---

## 9. Line Composition Rules

## 9.1. Glyph composition

Each line is composed by concatenating glyphs from left to right.

Each glyph contributes:

* its matrix
* letter spacing after it, except possibly the last glyph in the line

## 9.2. Vertical alignment inside a line

If glyphs in a line have different heights:

* all glyphs must be aligned by their bottom edge

Shorter glyphs must be padded vertically with empty cells (`0`) above them as needed.

## 9.3. Line matrix values

A line matrix contains only:

* `0`
* `1`

No `null` values are allowed inside line matrices.

---

## 10. Scheme Composition Rules

## 10.1. Vertical stacking

The final scheme is built by stacking line matrices vertically.

Line spacing is inserted between consecutive lines.

## 10.2. Scheme matrix values

The final scheme matrix may contain:

* `null`
* `0`
* `1`

## 10.3. `null` placement rule

`null` values may appear only outside visible content.

In v1, `null` may be added only:

* to the left of line content
* to the right of line content
* above all lines
* below all lines

`null` must not appear inside line content.

## 10.4. Rectangular output rule

The final scheme matrix must always be rectangular.

If visible content has uneven line widths or shape boundaries, the matrix must be padded to rectangular shape using `null`.

---

## 11. Constraint Fitting Rules

## 11.1. Scheme constraints

The generator should try to fit the final scheme into:

* scheme minimum width / height
* scheme maximum width / height

## 11.2. Overflow rule

Overflow beyond scheme constraints is allowed, but only up to 40%.

This means the resulting width or height may exceed the corresponding maximum constraint by at most 40%.

If the result exceeds this overflow threshold:

* the candidate is invalid

## 11.3. Underfill rule

A result smaller than the minimum target dimensions is allowed unless a stricter rule is introduced later.

For v1, the generator should prefer layouts that make reasonable use of the available space, but smaller valid layouts are acceptable.

---

## 12. Candidate Evaluation Rules

Multiple valid candidates may exist.

The generator must evaluate them and choose the best one by score.

## 12.1. Priority order

Candidate comparison must follow this priority:

1. the text fits
2. symbols are as large as possible
3. the number of lines is as small as possible

This priority order is mandatory.

## 12.2. Candidate validity

A candidate is valid only if:

* all characters are supported
* all words are placed without splitting
* all glyphs fit selected symbol bounds
* resulting dimensions do not exceed allowed overflow
* final matrix is rectangular
* final matrix contains only allowed values

## 12.3. Recommended scoring strategy

A score may combine:

* fit validity
* symbol area or symbol height/width preference
* penalty for additional lines
* penalty for excessive overflow

A practical comparison strategy:

1. reject all invalid candidates
2. prefer candidate with larger symbol size
3. if tied, prefer candidate with fewer lines
4. if still tied, prefer candidate with smaller overflow

---

## 13. Error Rules

Generation must return an error if:

* text is empty after normalization
* unsupported characters are present
* no valid symbol size exists
* no valid layout exists
* all candidates violate overflow constraints

The generator must not silently relax constraints beyond the allowed overflow rule.

---

## 14. Determinism and Variability

For v1, the generator returns one scheme.

Exact determinism is not required.

However, for a fixed implementation and fixed candidate search order, the result should be stable unless randomness is intentionally introduced later.

---

## 15. Out of Scope for v1

The generation rules do not include:

* decorative elements
* manual layout editing
* font selection by user
* image rendering
* PDF rendering
* multiple alternative outputs in one response

---
