import { useState } from 'react';
import type { DragEvent } from 'react';

import type { Pattern } from '../../../domain/pattern';
import {
  flipPatternHorizontal,
  flipPatternVertical,
  rotatePatternClockwise,
} from '../../../domain/transformations';
import { PatternPreview } from '../PatternPreview/PatternPreview';
import './PatternCard.css';

interface PatternCardProps {
  onDragEnd: () => void;
  onDragStart: (pattern: Pattern) => void;
  pattern: Pattern;
}

export function PatternCard({ pattern, onDragEnd, onDragStart }: PatternCardProps) {
  const [transformedPattern, setTransformedPattern] = useState(pattern);
  const title = transformedPattern.name ?? transformedPattern.char ?? transformedPattern.id;

  const handleDragStart = (event: DragEvent<HTMLElement>) => {
    onDragStart(transformedPattern);
    event.dataTransfer.effectAllowed = 'copy';
    event.dataTransfer.setData('text/plain', transformedPattern.id);
  };

  return (
    <article
      className="pattern-card"
      draggable
      onDragEnd={onDragEnd}
      onDragStart={handleDragStart}
    >
      <header className="pattern-card-header">
        <div>
          <h3>{title}</h3>
          <p>
            {transformedPattern.width} x {transformedPattern.height}
          </p>
        </div>
      </header>

      <div className="pattern-card-preview">
        <PatternPreview pattern={transformedPattern} />
      </div>

      <div className="pattern-card-actions" aria-label={`Трансформации ${title}`}>
        <button
          type="button"
          onClick={() => setTransformedPattern((current) => rotatePatternClockwise(current))}
        >
          Повернуть
        </button>
        <button
          type="button"
          onClick={() => setTransformedPattern((current) => flipPatternHorizontal(current))}
        >
          Отразить H
        </button>
        <button
          type="button"
          onClick={() => setTransformedPattern((current) => flipPatternVertical(current))}
        >
          Отразить V
        </button>
      </div>
    </article>
  );
}
