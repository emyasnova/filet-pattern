import { useCallback, useState } from 'react';

import type { Pattern } from '../../domain/pattern';

interface UseDragPattern {
  draggedPattern: Pattern | null;
  clearDraggedPattern: () => void;
  startDragPattern: (pattern: Pattern) => void;
}

export function useDragPattern(): UseDragPattern {
  const [draggedPattern, setDraggedPattern] = useState<Pattern | null>(null);

  const startDragPattern = useCallback((pattern: Pattern) => {
    setDraggedPattern(pattern);
  }, []);

  const clearDraggedPattern = useCallback(() => {
    setDraggedPattern(null);
  }, []);

  return {
    draggedPattern,
    clearDraggedPattern,
    startDragPattern,
  };
}
