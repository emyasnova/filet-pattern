import { memo, useMemo, useState } from 'react';

import type { Pattern } from '../../../domain/pattern';
import { usePatterns } from '../../hooks/usePatterns';
import { PatternCard } from '../PatternCard/PatternCard';
import { PatternCreateModal } from '../PatternCreateModal/PatternCreateModal';
import './PatternPanel.css';

interface PatternPanelProps {
  onPatternDragEnd: () => void;
  onPatternDragStart: (pattern: Pattern) => void;
}

export const PatternPanel = memo(function PatternPanel({
  onPatternDragEnd,
  onPatternDragStart,
}: PatternPanelProps) {
  const [category, setCategory] = useState('');
  const [query, setQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [tagDraft, setTagDraft] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [catalogRevision, setCatalogRevision] = useState(0);
  const [notice, setNotice] = useState('');
  const filters = useMemo(
    () => ({ search: query, category: category || undefined, tags: selectedTags }),
    [category, query, selectedTags],
  );
  const { patterns, categories, availableTags, errors, isLoading } =
    usePatterns(filters, catalogRevision);
  const tagNames = useMemo(() => availableTags.map((tag) => tag.name), [availableTags]);
  const filteredTags = useMemo(() => {
    const normalizedDraft = tagDraft.trim().toLocaleLowerCase('ru');
    return tagNames.filter((tag) => {
      if (selectedTags.includes(tag)) return false;
      return !normalizedDraft || tag.toLocaleLowerCase('ru').includes(normalizedDraft);
    });
  }, [selectedTags, tagDraft, tagNames]);
  const hasActiveFilters = Boolean(category || query.trim() || selectedTags.length);

  const handleAddTag = (tag: string) => {
    const nextTag = tag.trim();
    if (!nextTag || !tagNames.includes(nextTag) || selectedTags.includes(nextTag)) return;
    setSelectedTags((current) => [...current, nextTag]);
    setTagDraft('');
  };

  const handleResetFilters = () => {
    setCategory('');
    setQuery('');
    setSelectedTags([]);
    setTagDraft('');
  };

  return (
    <aside className="patterns-panel" aria-labelledby="patterns-title">
      <div className="panel-header">
        <div>
          <h2 id="patterns-title">Мотивы</h2>
          <p>Загружаются из каталога на сервере.</p>
        </div>
        <button
          type="button"
          className="pattern-create-button"
          aria-label="Добавить паттерн"
          title="Добавить паттерн"
          onClick={() => setIsCreateOpen(true)}
        >
          +
        </button>
      </div>

      {notice ? <div className="pattern-create-notice" role="status">{notice}</div> : null}

      <div className="pattern-filters" aria-label="Поиск и фильтры мотивов">
        <label className="pattern-filter-field">
          <span>Поиск</span>
          <input
            type="search"
            value={query}
            placeholder="Название или тэг"
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>

        <label className="pattern-filter-field">
          <span>Категория</span>
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">Все</option>
            {categories.map((categoryOption) => (
              <option key={categoryOption.slug} value={categoryOption.slug}>
                {categoryOption.name}
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
              if (event.key !== 'Enter') return;
              event.preventDefault();
              handleAddTag(tagDraft);
            }}
          />
          <datalist id="pattern-tags">
            {filteredTags.map((tag) => <option key={tag} value={tag} />)}
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
                  setSelectedTags((current) => current.filter((currentTag) => currentTag !== tag))
                }
              >
                {tag} <span aria-hidden="true">x</span>
              </button>
            ))}
          </div>
        ) : null}

        <div className="pattern-filter-footer">
          <span>Найдено {patterns.length}</span>
          <button type="button" disabled={!hasActiveFilters} onClick={handleResetFilters}>
            Сбросить
          </button>
        </div>
      </div>

      {isLoading ? <div className="pattern-placeholder">Загрузка мотивов...</div> : null}
      {!isLoading && patterns.length === 0 ? (
        <div className="pattern-placeholder">
          {hasActiveFilters ? 'Нет мотивов по фильтрам' : 'Мотивы не найдены'}
        </div>
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
      {isCreateOpen ? (
        <PatternCreateModal
          categories={categories}
          availableTags={availableTags}
          onClose={() => setIsCreateOpen(false)}
          onCreated={(pattern) => {
            setIsCreateOpen(false);
            setNotice(`Паттерн «${pattern.name}» сохранён`);
            setCatalogRevision((current) => current + 1);
          }}
        />
      ) : null}
    </aside>
  );
});
