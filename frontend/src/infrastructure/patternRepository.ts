import { validatePattern } from '../application/validatePattern';
import type { Pattern, PatternCategory, PatternTag } from '../domain/pattern';

export interface PatternFilters {
  search?: string;
  category?: string;
  tags: string[];
}

export interface PatternPreview {
  width: number;
  height: number;
  threshold: number;
  fillThreshold: number;
  cells: Pattern['cells'];
}

export interface CreatePatternInput {
  name: string;
  category: string;
  tags: string[];
  width: number;
  height: number;
  cells: Pattern['cells'];
}

export interface PatternLoadError {
  source: string;
  message: string;
}

export interface LoadPatternsResult {
  patterns: Pattern[];
  errors: PatternLoadError[];
}

export async function loadPatterns(
  filters: PatternFilters,
  signal?: AbortSignal,
): Promise<LoadPatternsResult> {
  const params = new URLSearchParams();
  if (filters.search?.trim()) params.set('search', filters.search.trim());
  if (filters.category) params.set('category', filters.category);
  filters.tags.forEach((tag) => params.append('tags', tag));
  const suffix = params.size ? `?${params.toString()}` : '';
  const result = await fetchJson<unknown>(`/api/v1/patterns${suffix}`, signal);

  if (!result.ok) {
    return { patterns: [], errors: [{ source: 'patterns API', message: result.error }] };
  }
  if (!Array.isArray(result.data)) {
    return {
      patterns: [],
      errors: [{ source: 'patterns API', message: 'Response must be an array.' }],
    };
  }

  const patterns: Pattern[] = [];
  const errors: PatternLoadError[] = [];
  result.data.forEach((item, index) => {
    const validation = validatePattern(item);
    if (validation.pattern) patterns.push(validation.pattern);
    validation.errors.forEach((message) =>
      errors.push({ source: `patterns[${index}]`, message }),
    );
  });
  return { patterns, errors };
}

export async function loadCategories(signal?: AbortSignal): Promise<PatternCategory[]> {
  const result = await fetchJson<unknown>('/api/v1/categories', signal);
  if (!result.ok) throw new Error(result.error);
  if (!Array.isArray(result.data)) throw new Error('Categories response must be an array.');
  return result.data.filter(isPatternCategory);
}

export async function loadTags(signal?: AbortSignal): Promise<PatternTag[]> {
  const result = await fetchJson<unknown>('/api/v1/tags', signal);
  if (!result.ok) throw new Error(result.error);
  if (!Array.isArray(result.data)) throw new Error('Tags response must be an array.');
  return result.data.filter(isPatternTag);
}

export async function detectImageSize(file: File): Promise<{ width: number; height: number }> {
  const form = new FormData();
  form.set('file', file);
  return requestJson('/api/v1/images/size', { method: 'POST', body: form });
}

export async function generatePatternPreview(
  file: File,
  options: { width: number; height: number; threshold: number; fillThreshold: number },
): Promise<PatternPreview> {
  const form = new FormData();
  form.set('file', file);
  form.set('width', String(options.width));
  form.set('height', String(options.height));
  form.set('threshold', String(options.threshold));
  form.set('fill_threshold', String(options.fillThreshold));
  const data = await requestJson<{
    width: number;
    height: number;
    threshold: number;
    fill_threshold: number;
    cells: Pattern['cells'];
  }>('/api/v1/patterns/preview', { method: 'POST', body: form });
  return { ...data, fillThreshold: data.fill_threshold };
}

export async function createPattern(input: CreatePatternInput): Promise<Pattern> {
  const data = await requestJson<unknown>('/api/v1/patterns', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  const validation = validatePattern(data);
  if (!validation.pattern) throw new Error(validation.errors.join(' '));
  return validation.pattern;
}

async function requestJson<T>(url: string, init: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === 'string') message = body.detail;
    } catch {
      // Keep the HTTP status when the server did not return JSON.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

async function fetchJson<T>(
  url: string,
  signal?: AbortSignal,
): Promise<{ ok: true; data: T } | { ok: false; error: string }> {
  try {
    const response = await fetch(url, { signal });
    if (!response.ok) return { ok: false, error: `HTTP ${response.status}` };
    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    return {
      ok: false,
      error: error instanceof Error ? error.message : 'Unknown loading error.',
    };
  }
}

function isPatternCategory(value: unknown): value is PatternCategory {
  return isRecord(value) && typeof value.slug === 'string' && typeof value.name === 'string';
}

function isPatternTag(value: unknown): value is PatternTag {
  return isRecord(value) && typeof value.id === 'string' && typeof value.name === 'string';
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
