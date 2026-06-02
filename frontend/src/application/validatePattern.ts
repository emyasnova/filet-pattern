import type { PatternCell } from '../domain/cell';
import type { Pattern, PatternCategory } from '../domain/pattern';
import { normalizePatternTransparency } from './normalizePatternTransparency';

const ALLOWED_PATTERN_CATEGORIES: PatternCategory[] = [
  'alphabet',
  'frame',
  'object',
  'ornament',
];

type PatternJson = Partial<Omit<Pattern, 'id' | 'category' | 'tags'>> & {
  category?: unknown;
  tags?: unknown;
};

export interface ValidatePatternResult {
  pattern?: Pattern;
  errors: string[];
}

export function validatePattern(data: unknown, id: string): ValidatePatternResult {
  const errors: string[] = [];

  if (!isRecord(data)) {
    return { errors: ['Pattern must be a JSON object.'] };
  }

  const patternJson = data as PatternJson;
  const width = patternJson.width;
  const height = patternJson.height;
  const cells = patternJson.cells;

  if (!isPositiveInteger(width)) {
    errors.push('width must be a positive integer.');
  }

  if (!isPositiveInteger(height)) {
    errors.push('height must be a positive integer.');
  }

  if (!Array.isArray(cells)) {
    errors.push('cells must be an array.');
  } else if (isPositiveInteger(height) && cells.length !== height) {
    errors.push(`cells row count must equal height ${height}.`);
  }

  if (Array.isArray(cells) && isPositiveInteger(width)) {
    cells.forEach((row, rowIndex) => {
      if (!Array.isArray(row)) {
        errors.push(`cells[${rowIndex}] must be an array.`);
        return;
      }

      if (row.length !== width) {
        errors.push(`cells[${rowIndex}] length must equal width ${width}.`);
      }

      row.forEach((cell, colIndex) => {
        if (!isPatternCell(cell)) {
          errors.push(`cells[${rowIndex}][${colIndex}] must be 0, 1, or null.`);
        }
      });
    });
  }

  if (patternJson.char !== undefined && typeof patternJson.char !== 'string') {
    errors.push('char must be a string when provided.');
  }

  if (patternJson.name !== undefined && typeof patternJson.name !== 'string') {
    errors.push('name must be a string when provided.');
  }

  if (
    patternJson.category !== undefined &&
    !isAllowedPatternCategory(patternJson.category)
  ) {
    errors.push('category must be one of alphabet, frame, object, or ornament.');
  }

  if (patternJson.tags !== undefined) {
    if (!Array.isArray(patternJson.tags)) {
      errors.push('tags must be an array when provided.');
    } else {
      patternJson.tags.forEach((tag, tagIndex) => {
        if (typeof tag !== 'string') {
          errors.push(`tags[${tagIndex}] must be a string.`);
        }
      });
    }
  }

  if (errors.length > 0) {
    return { errors };
  }

  const category = isAllowedPatternCategory(patternJson.category)
    ? patternJson.category
    : 'uncategorized';
  const tags = Array.isArray(patternJson.tags)
    ? [...new Set(patternJson.tags.map((tag) => tag.trim()).filter(Boolean))]
    : [];

  return {
    pattern: {
      id,
      char: patternJson.char,
      category,
      name: patternJson.name,
      tags,
      width: width as number,
      height: height as number,
      cells: normalizePatternTransparency(cells as PatternCell[][]),
    },
    errors,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isPositiveInteger(value: unknown): value is number {
  return Number.isInteger(value) && Number(value) > 0;
}

function isPatternCell(value: unknown): value is PatternCell {
  return value === 0 || value === 1 || value === null;
}

function isAllowedPatternCategory(value: unknown): value is PatternCategory {
  return (
    typeof value === 'string' &&
    ALLOWED_PATTERN_CATEGORIES.includes(value as PatternCategory)
  );
}
