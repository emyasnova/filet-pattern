import { memo, useMemo, useState } from 'react';

import {
  filterPatterns,
  getAvailablePatternTags,
  PATTERN_CATEGORY_LABELS,
  PATTERN_CATEGORY_OPTIONS,
} from '../../../application/filterPatterns';
import type { Pattern, PatternCategory } from '../../../domain/pattern';
import type { PatternLoadError } from '../../../infrastructure/patternRepository';
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
  const [category, setCategory] = useState<PatternCategory | 'all'>('all');
  const [query, setQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [tagDraft, setTagDraft] = useState('');

  const availableTags = useMemo(() => getAvailablePatternTags(patterns), [patterns]);
  const filteredTags = useMemo(() => {
    const normalizedDraft = tagDraft.trim().toLocaleLowerCase('ru');

    return availableTags.filter((tag) => {
      if (selectedTags.includes(tag)) {
        return false;
      }

      return !normalizedDraft || tag.toLocaleLowerCase('ru').includes(normalizedDraft);
    });
  }, [availableTags, selectedTags, tagDraft]);
  const filteredPatterns = useMemo(
    () =>
      filterPatterns(patterns, {
        category,
        query,
        tags: selectedTags,
      }),
    [category, patterns, query, selectedTags],
  );
  const hasActiveFilters =
    category !== 'all' || query.trim().length > 0 || selectedTags.length > 0;

  const handleAddTag = (tag: string) => {
    const nextTag = tag.trim();

    if (!nextTag || !availableTags.includes(nextTag) || selectedTags.includes(nextTag)) {
      return;
    }

    setSelectedTags((current) => [...current, nextTag]);
    setTagDraft('');
  };

  const handleResetFilters = () => {
    setCategory('all');
    setQuery('');
    setSelectedTags([]);
    setTagDraft('');
  };

  return (
    <aside className="patterns-panel" aria-labelledby="patterns-title">
      <div className="panel-header">
        <div>
          <h2 id="patterns-title">Мотивы</h2>
          <p>Загружаются из JSON-файлов в public/patterns.</p>
        </div>
      </div>

      <div className="pattern-filters" aria-label="Поиск и фильтры мотивов">
        <label className="pattern-filter-field">
          <span>Поиск</span>
          <input
            type="search"
            value={query}
            placeholder="Название, тэг, id"
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>

        <label className="pattern-filter-field">
          <span>Категория</span>
          <select
            value={category}
            onChange={(event) =>
              setCategory(event.target.value as PatternCategory | 'all')
            }
          >
            <option value="all">Все</option>
            {PATTERN_CATEGORY_OPTIONS.map((categoryOption) => (
              <option key={categoryOption} value={categoryOption}>
                {PATTERN_CATEGORY_LABELS[categoryOption]}
              </option>
            ))}
          </select>
        </label>

        <label className="pattern-filter-field">
          <span>Тэги</span>
          <input
            type="search"
            list="pattern-tags"
            value={tagDraft}
            placeholder="Начните ввод"
            onChange={(event) => setTagDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key !== 'Enter') {
                return;
              }

              event.preventDefault();
              handleAddTag(tagDraft);
            }}
          />
          <datalist id="pattern-tags">
            {filteredTags.map((tag) => (
              <option key={tag} value={tag} />
            ))}
          </datalist>
        </label>

        <button
          type="button"
          className="pattern-add-tag-button"
          disabled={!filteredTags.includes(tagDraft.trim())}
          onClick={() => handleAddTag(tagDraft)}
        >
          Добавить тэг
        </button>

        {selectedTags.length > 0 ? (
          <div className="pattern-tag-chips" aria-label="Выбранные тэги">
            {selectedTags.map((tag) => (
              <button
                type="button"
                className="pattern-tag-chip"
                key={tag}
                onClick={() =>
                  setSelectedTags((current) =>
                    current.filter((currentTag) => currentTag !== tag),
                  )
                }
              >
                {tag} <span aria-hidden="true">x</span>
              </button>
            ))}
          </div>
        ) : null}

        <div className="pattern-filter-footer">
          <span>
            Найдено {filteredPatterns.length} из {patterns.length}
          </span>
          <button type="button" disabled={!hasActiveFilters} onClick={handleResetFilters}>
            Сбросить
          </button>
        </div>
      </div>

      {isLoading ? <div className="pattern-placeholder">Загрузка мотивов...</div> : null}

      {!isLoading && patterns.length === 0 ? (
        <div className="pattern-placeholder">Мотивы не найдены</div>
      ) : null}

      {!isLoading && patterns.length > 0 && filteredPatterns.length === 0 ? (
        <div className="pattern-placeholder">Нет мотивов по фильтрам</div>
      ) : null}

      {filteredPatterns.length > 0 ? (
        <div className="pattern-card-list" aria-label="Загруженные мотивы">
          {filteredPatterns.map((pattern) => (
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
