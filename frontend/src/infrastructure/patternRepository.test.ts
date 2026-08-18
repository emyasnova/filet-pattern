import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  createPattern,
  detectImageSize,
  generatePatternPreview,
  loadCategories,
  loadPatterns,
  loadTags,
} from './patternRepository';

const pattern = {
  id: '83f9eefc-b6bc-5bdb-b521-c010422068ff',
  name: 'Rose',
  category: 'ornament',
  tags: ['flower', 'роза'],
  width: 1,
  height: 1,
  cells: [[1]],
  created_at: '2026-08-17T00:00:00Z',
};

afterEach(() => vi.unstubAllGlobals());

describe('patternRepository', () => {
  it('sends search, category, and repeated tags', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [pattern],
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await loadPatterns({
      search: ' rose ',
      category: 'ornament',
      tags: ['flower', 'роза'],
    });

    const url = new URL(fetchMock.mock.calls[0][0], 'http://localhost');
    expect(url.pathname).toBe('/api/v1/patterns');
    expect(url.searchParams.get('search')).toBe('rose');
    expect(url.searchParams.get('category')).toBe('ornament');
    expect(url.searchParams.getAll('tags')).toEqual(['flower', 'роза']);
    expect(result.patterns[0].createdAt).toBe(pattern.created_at);
  });

  it('keeps valid patterns and reports invalid items', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [pattern, { name: 'invalid' }],
    }));

    const result = await loadPatterns({ tags: [] });

    expect(result.patterns).toHaveLength(1);
    expect(result.errors.some((error) => error.source === 'patterns[1]')).toBe(true);
  });

  it('loads category and tag catalogs', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ slug: 'alphabet', name: 'Алфавит' }],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ id: 'tag-id', name: 'letter' }],
      });
    vi.stubGlobal('fetch', fetchMock);

    await expect(loadCategories()).resolves.toEqual([
      { slug: 'alphabet', name: 'Алфавит' },
    ]);
    await expect(loadTags()).resolves.toEqual([{ id: 'tag-id', name: 'letter' }]);
  });

  it('returns an error for an unsuccessful response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }));

    const result = await loadPatterns({ tags: [] });

    expect(result).toEqual({
      patterns: [],
      errors: [{ source: 'patterns API', message: 'HTTP 503' }],
    });
  });

  it('runs image size, preview, and create requests', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ width: 5, height: 4 }) })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ width: 1, height: 1, threshold: 128, fill_threshold: 0.35, cells: [[1]] }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => pattern });
    vi.stubGlobal('fetch', fetchMock);
    const file = new File(['image'], 'rose.png', { type: 'image/png' });

    await expect(detectImageSize(file)).resolves.toEqual({ width: 5, height: 4 });
    await expect(generatePatternPreview(file, { width: 5, height: 4, threshold: 128, fillThreshold: 0.35 })).resolves.toMatchObject({ width: 1, height: 1, fillThreshold: 0.35 });
    await expect(createPattern({ name: 'Rose', category: 'ornament', tags: [], width: 1, height: 1, cells: [[1]] })).resolves.toMatchObject({ name: 'Rose' });

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/images/size');
    expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/patterns/preview');
    expect(fetchMock.mock.calls[2][0]).toBe('/api/v1/patterns');
  });
});
