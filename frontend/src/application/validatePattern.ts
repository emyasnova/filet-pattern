import type { PatternCell } from '../domain/cell';
import type { Pattern } from '../domain/pattern';

export interface ValidatePatternResult {
  pattern?: Pattern;
  errors: string[];
}

export function validatePattern(data: unknown): ValidatePatternResult {
  const errors: string[] = [];

  if (!isRecord(data)) {
    return { errors: ['Pattern must be a JSON object.'] };
  }

  const id = data.id;
  const name = data.name;
  const category = data.category;
  const tags = data.tags;
  const width = data.width;
  const height = data.height;
  const cells = data.cells;
  const createdAt = data.created_at;

  if (typeof id !== 'string' || !id.trim()) errors.push('id must be a string.');
  if (typeof name !== 'string' || !name.trim()) errors.push('name must be a string.');
  if (typeof category !== 'string' || !category.trim()) {
    errors.push('category must be a string.');
  }
  if (!Array.isArray(tags) || tags.some((tag) => typeof tag !== 'string')) {
    errors.push('tags must be an array of strings.');
  }
  if (!isPositiveInteger(width)) errors.push('width must be a positive integer.');
  if (!isPositiveInteger(height)) errors.push('height must be a positive integer.');
  if (typeof createdAt !== 'string' || Number.isNaN(Date.parse(createdAt))) {
    errors.push('created_at must be an ISO datetime string.');
  }

  if (!Array.isArray(cells)) {
    errors.push('cells must be an array.');
  } else {
    if (isPositiveInteger(height) && cells.length !== height) {
      errors.push(`cells row count must equal height ${height}.`);
    }
    cells.forEach((row, rowIndex) => {
      if (!Array.isArray(row)) {
        errors.push(`cells[${rowIndex}] must be an array.`);
        return;
      }
      if (isPositiveInteger(width) && row.length !== width) {
        errors.push(`cells[${rowIndex}] length must equal width ${width}.`);
      }
      row.forEach((cell, colIndex) => {
        if (cell !== 0 && cell !== 1 && cell !== null) {
          errors.push(`cells[${rowIndex}][${colIndex}] must be 0, 1, or null.`);
        }
      });
    });
  }

  if (errors.length > 0) return { errors };

  return {
    pattern: {
      id: id as string,
      name: name as string,
      category: category as string,
      tags: tags as string[],
      width: width as number,
      height: height as number,
      cells: cells as PatternCell[][],
      createdAt: createdAt as string,
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
