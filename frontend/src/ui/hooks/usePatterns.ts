import { useEffect, useState } from 'react';

import {
  loadCategories,
  loadPatterns,
  loadTags,
  type PatternFilters,
  type PatternLoadError,
} from '../../infrastructure/patternRepository';
import type { Pattern, PatternCategory, PatternTag } from '../../domain/pattern';

interface UsePatternsState {
  patterns: Pattern[];
  categories: PatternCategory[];
  availableTags: PatternTag[];
  errors: PatternLoadError[];
  isLoading: boolean;
}

export function usePatterns(filters: PatternFilters, revision = 0): UsePatternsState {
  const [debouncedSearch, setDebouncedSearch] = useState(filters.search ?? '');
  const [state, setState] = useState<UsePatternsState>({
    patterns: [],
    categories: [],
    availableTags: [],
    errors: [],
    isLoading: true,
  });

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([loadCategories(controller.signal), loadTags(controller.signal)])
      .then(([categories, availableTags]) => {
        setState((current) => ({ ...current, categories, availableTags }));
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setState((current) => ({
          ...current,
          errors: [{ source: 'catalog API', message: String(error) }],
        }));
      });
    return () => controller.abort();
  }, [revision]);

  useEffect(() => {
    const timeout = window.setTimeout(
      () => setDebouncedSearch(filters.search ?? ''),
      filters.search?.trim() ? 300 : 0,
    );
    return () => window.clearTimeout(timeout);
  }, [filters.search]);

  useEffect(() => {
    const controller = new AbortController();
    setState((current) => ({ ...current, isLoading: true }));
    loadPatterns({ ...filters, search: debouncedSearch }, controller.signal)
      .then((result) => {
        setState((current) => ({
          ...current,
          patterns: result.patterns,
          errors: result.errors,
          isLoading: false,
        }));
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setState((current) => ({
          ...current,
          patterns: [],
          errors: [{ source: 'patterns API', message: String(error) }],
          isLoading: false,
        }));
      });

    return () => controller.abort();
  }, [debouncedSearch, filters.category, filters.tags, revision]);

  return state;
}
