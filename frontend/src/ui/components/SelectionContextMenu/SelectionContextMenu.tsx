import './SelectionContextMenu.css';

interface SelectionContextMenuProps {
  canPaste: boolean;
  left: number;
  top: number;
  onClear: () => void;
  onCopy: () => void;
  onCut: () => void;
  onFill: () => void;
  onFlipHorizontal: () => void;
  onFlipVertical: () => void;
  onPaste: () => void;
  onRotate: () => void;
}

export function SelectionContextMenu({
  canPaste,
  left,
  top,
  onClear,
  onCopy,
  onCut,
  onFill,
  onFlipHorizontal,
  onFlipVertical,
  onPaste,
  onRotate,
}: SelectionContextMenuProps) {
  return (
    <div
      className="selection-context-menu"
      role="menu"
      style={{ left, top }}
      onPointerDown={(event) => event.stopPropagation()}
      onContextMenu={(event) => event.preventDefault()}
    >
      <button type="button" role="menuitem" onClick={onCopy}>
        Копировать
      </button>
      <button type="button" role="menuitem" onClick={onCut}>
        Вырезать
      </button>
      <button type="button" role="menuitem" disabled={!canPaste} onClick={onPaste}>
        Вставить
      </button>
      <button type="button" role="menuitem" onClick={onClear}>
        Очистить
      </button>
      <button type="button" role="menuitem" onClick={onFill}>
        Заполнить
      </button>
      <button type="button" role="menuitem" onClick={onRotate}>
        Повернуть
      </button>
      <button type="button" role="menuitem" onClick={onFlipHorizontal}>
        Отразить H
      </button>
      <button type="button" role="menuitem" onClick={onFlipVertical}>
        Отразить V
      </button>
    </div>
  );
}
