import type { ChangeEvent } from 'react';

import './Toolbar.css';

interface ToolbarProps {
  importError: string | null;
  isSelectionMode: boolean;
  onClear: () => void;
  onExportPng: () => void;
  onLoadJson: (file: File) => void;
  onSaveJson: () => void;
  onToggleSelectionMode: () => void;
}

export function Toolbar({
  importError,
  isSelectionMode,
  onClear,
  onExportPng,
  onLoadJson,
  onSaveJson,
  onToggleSelectionMode,
}: ToolbarProps) {
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    event.target.value = '';

    if (file) {
      onLoadJson(file);
    }
  };

  return (
    <div className="toolbar">
      <button type="button" onClick={onExportPng}>
        Сгенерировать PNG
      </button>

      <button type="button" onClick={onSaveJson}>
        Сохранить JSON
      </button>

      <label className="toolbar-file-button">
        Загрузить JSON
        <input type="file" accept="application/json,.json" onChange={handleFileChange} />
      </label>

      <button type="button" onClick={onClear}>
        Очистить
      </button>

      <button
        type="button"
        className={['toolbar-selection-button', isSelectionMode ? 'active' : '']
          .filter(Boolean)
          .join(' ')}
        aria-label="Режим выделения блока"
        aria-pressed={isSelectionMode}
        title="Режим выделения блока"
        onClick={onToggleSelectionMode}
      >
        <span className="toolbar-selection-icon" aria-hidden="true" />
      </button>

      {importError ? <p className="toolbar-error">{importError}</p> : null}
    </div>
  );
}
