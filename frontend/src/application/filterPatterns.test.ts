import { describe, expect, it } from 'vitest';

import {
  filterPatterns,
  getAvailablePatternTags,
  type PatternFilters,
} from './filterPatterns';
import type { Pattern } from '../domain/pattern';

const patterns: Pattern[] = [
  {
    id: 'A.json',
    char: 'A',
    category: 'alphabet',
    tags: ['letter', 'latin', 'A'],
    width: 1,
    height: 1,
    cells: [[1]],
  },
  {
    id: 'rose.json',
    name: 'Rose',
    category: 'ornament',
    tags: ['flower', 'цветок', 'rose', 'роза'],
    width: 1,
    height: 1,
    cells: [[1]],
  },
  {
    id: 'frame.json',
    name: 'Simple frame',
    category: 'frame',
    tags: ['border', 'рамка'],
    width: 1,
    height: 1,
    cells: [[1]],
  },
];

const defaultFilters: PatternFilters = {
  category: 'all',
  query: '',
  tags: [],
};

describe('filterPatterns', () => {
  it('filters patterns by category', () => {
    expect(
      filterPatterns(patterns, { ...defaultFilters, category: 'frame' }).map(
        (pattern) => pattern.id,
      ),
    ).toEqual(['frame.json']);
  });

  it('filters selected tags with AND semantics', () => {
    expect(
      filterPatterns(patterns, {
        ...defaultFilters,
        tags: ['flower', 'роза'],
      }).map((pattern) => pattern.id),
    ).toEqual(['rose.json']);

    expect(
      filterPatterns(patterns, {
        ...defaultFilters,
        tags: ['flower', 'latin'],
      }),
    ).toEqual([]);
  });

  it('searches by text fields and tags', () => {
    expect(
      filterPatterns(patterns, { ...defaultFilters, query: 'latin' }).map(
        (pattern) => pattern.id,
      ),
    ).toEqual(['A.json']);

    expect(
      filterPatterns(patterns, { ...defaultFilters, query: 'рамк' }).map(
        (pattern) => pattern.id,
      ),
    ).toEqual(['frame.json']);
  });

  it('collects unique available tags', () => {
    expect(getAvailablePatternTags(patterns)).toEqual([
      'рамка',
      'роза',
      'цветок',
      'A',
      'border',
      'flower',
      'latin',
      'letter',
      'rose',
    ]);
  });
});
