import { validatePattern } from '../application/validatePattern';
import type { Pattern } from '../domain/pattern';

interface PatternIndexFile {
  patterns?: unknown;
}

export interface PatternLoadError {
  source: string;
  message: string;
}

export interface LoadPatternsResult {
  patterns: Pattern[];
  errors: PatternLoadError[];
}

const PATTERNS_BASE_PATH = '/patterns';

export async function loadPatterns(): Promise<LoadPatternsResult> {
  const errors: PatternLoadError[] = [];
  const indexResult = await fetchJson<PatternIndexFile>(
    `${PATTERNS_BASE_PATH}/index.json`,
  );

  if (!indexResult.ok) {
    return {
      patterns: [],
      errors: [{ source: 'index.json', message: indexResult.error }],
    };
  }

  if (!Array.isArray(indexResult.data.patterns)) {
    return {
      patterns: [],
      errors: [
        { source: 'index.json', message: 'patterns must be an array of file names.' },
      ],
    };
  }

  const fileNames = indexResult.data.patterns.filter(
    (fileName): fileName is string => typeof fileName === 'string',
  );

  if (fileNames.length !== indexResult.data.patterns.length) {
    errors.push({
      source: 'index.json',
      message: 'All pattern file names must be strings.',
    });
  }

  const loadedPatterns = await Promise.all(
    fileNames.map((fileName) => loadPatternFile(fileName)),
  );

  loadedPatterns.forEach((result) => {
    if (result.pattern) {
      errors.push(...result.errors);
      return;
    }

    errors.push(...result.errors);
  });

  return {
    patterns: loadedPatterns.flatMap((result) =>
      result.pattern ? [result.pattern] : [],
    ),
    errors,
  };
}

async function loadPatternFile(
  fileName: string,
): Promise<{ pattern?: Pattern; errors: PatternLoadError[] }> {
  const fileResult = await fetchJson<unknown>(`${PATTERNS_BASE_PATH}/${fileName}`);

  if (!fileResult.ok) {
    return {
      errors: [{ source: fileName, message: fileResult.error }],
    };
  }

  const validation = validatePattern(fileResult.data, fileName);

  return {
    pattern: validation.pattern,
    errors: validation.errors.map((message) => ({ source: fileName, message })),
  };
}

async function fetchJson<T>(
  url: string,
): Promise<{ ok: true; data: T } | { ok: false; error: string }> {
  try {
    const response = await fetch(url);

    if (!response.ok) {
      return { ok: false, error: `HTTP ${response.status}` };
    }

    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : 'Unknown loading error.',
    };
  }
}
