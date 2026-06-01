import { memo } from 'react';

import type { PatternLoadError } from '../../../infrastructure/patternRepository';
import type { Pattern } from '../../../domain/pattern';
import { PatternCard } from '../PatternCard/PatternCard';
import './PatternPanel.css';

interface PatternPanelProps {
  onPatternDragEnd: () => void;
  onPatternDragStart: (pattern: Pattern) => void;
  patterns: Pattern[];
  errors: PatternLoadError[];
  isLoading: boolean;
}

export const PatternPanel = memo(function PatternPanel({
  onPatternDragEnd,
  onPatternDragStart,
  patterns,
  errors,
  isLoading,
}: PatternPanelProps) {
  return (
    <aside className="patterns-panel" aria-labelledby="patterns-title">
      <div className="panel-header">
        <div>
          <h2 id="patterns-title">Мотивы</h2>
          <p>Загружаются из JSON-файлов в public/patterns.</p>
        </div>
      </div>

      {isLoading ? <div className="pattern-placeholder">Загрузка мотивов...</div> : null}

      {!isLoading && patterns.length === 0 ? (
        <div className="pattern-placeholder">Мотивы не найдены</div>
      ) : null}

      {patterns.length > 0 ? (
        <div className="pattern-card-list" aria-label="Загруженные мотивы">
          {patterns.map((pattern) => (
            <PatternCard
              key={pattern.id}
              pattern={pattern}
              onDragEnd={onPatternDragEnd}
              onDragStart={onPatternDragStart}
            />
          ))}
        </div>
      ) : null}

      {errors.length > 0 ? (
        <div className="pattern-errors" role="status" aria-label="Ошибки мотивов">
          <h3>Ошибки загрузки</h3>
          <ul>
            {errors.map((error) => (
              <li key={`${error.source}-${error.message}`}>
                <strong>{error.source}:</strong> {error.message}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </aside>
  );
});
