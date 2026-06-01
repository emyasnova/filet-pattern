import { useEffect, useState } from 'react';

import {
  loadPatterns,
  type PatternLoadError,
} from '../../infrastructure/patternRepository';
import type { Pattern } from '../../domain/pattern';

interface UsePatternsState {
  patterns: Pattern[];
  errors: PatternLoadError[];
  isLoading: boolean;
}

export function usePatterns(): UsePatternsState {
  const [state, setState] = useState<UsePatternsState>({
    patterns: [],
    errors: [],
    isLoading: true,
  });

  useEffect(() => {
    let isActive = true;

    loadPatterns().then((result) => {
      if (!isActive) {
        return;
      }

      setState({
        patterns: result.patterns,
        errors: result.errors,
        isLoading: false,
      });
    });

    return () => {
      isActive = false;
    };
  }, []);

  return state;
}
