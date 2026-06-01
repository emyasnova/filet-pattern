# DOMAIN.md

## Обзор

text → glyphs → lines → scheme

---

## Сущности

### SchemeRequest

* text
* scheme_constraints
* symbol_constraints

### SchemeConstraints

* width_min
* width_max
* height_min
* height_max

### SymbolConstraints

* width_min
* width_max
* height_min
* height_max

### Glyph

* char
* width
* height
* cells (0/1)

### GlyphRepository

* получить глиф
* проверить символ

### Line

* список глифов
* cells

Правила:

* выравнивание по низу
* паддинг сверху
* только 0/1

### Layout

* список строк

### Scheme

* width
* height
* cells (null/0/1)

---

## Преобразования

1. Text → Layout
2. Layout → Glyphs
3. Glyphs → Lines
4. Lines → Scheme

---

## Валидация

* текст не пустой
* символы поддерживаются
* матрица прямоугольная
