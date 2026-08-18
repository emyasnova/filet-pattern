import { describe, expect, it } from 'vitest';

import { validatePattern } from './validatePattern';

const validPattern = {
  id: '83f9eefc-b6bc-5bdb-b521-c010422068ff',
  name: 'Rose',
  category: 'ornament',
  tags: ['flower', 'роза'],
  width: 2,
  height: 2,
  cells: [
    [0, 1],
    [null, 0],
  ],
  created_at: '2026-08-17T00:00:00Z',
};

describe('validatePattern', () => {
  it('accepts a valid API pattern', () => {
    const result = validatePattern(validPattern);

    expect(result.errors).toEqual([]);
    expect(result.pattern).toEqual({
      id: validPattern.id,
      name: validPattern.name,
      category: validPattern.category,
      tags: validPattern.tags,
      width: validPattern.width,
      height: validPattern.height,
      cells: validPattern.cells,
      createdAt: validPattern.created_at,
    });
  });

  it('rejects invalid metadata', () => {
    const result = validatePattern({
      ...validPattern,
      name: '',
      tags: ['flower', 1],
      created_at: 'invalid',
    });

    expect(result.pattern).toBeUndefined();
    expect(result.errors).toContain('name must be a string.');
    expect(result.errors).toContain('tags must be an array of strings.');
    expect(result.errors).toContain('created_at must be an ISO datetime string.');
  });

  it('rejects invalid dimensions and cell values', () => {
    const result = validatePattern({
      ...validPattern,
      height: 3,
      cells: [[0, 2]],
    });

    expect(result.pattern).toBeUndefined();
    expect(result.errors).toContain('cells row count must equal height 3.');
    expect(result.errors).toContain('cells[0][1] must be 0, 1, or null.');
  });
});
