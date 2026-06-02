import { useEffect, useState } from 'react';

import {
  copyCanvasBlock,
  flipCanvasBlockHorizontal,
  flipCanvasBlockVertical,
  rotateCanvasBlockClockwise,
} from '../application/canvasBlockOperations';
import {
  createCanvasFile,
  validateCanvasFile,
} from '../application/validateCanvasFile';
import type { CanvasBlock, SelectionRect } from '../domain/selection';
import { normalizeSelectionRect } from '../domain/selection';
import { downloadJson } from '../infrastructure/downloadJson';
import { exportCanvasToPng } from '../infrastructure/exportCanvasToPng';
import { readJsonFile } from '../infrastructure/readJsonFile';
import { CanvasGrid } from '../ui/components/CanvasGrid/CanvasGrid';
import { PatternPanel } from '../ui/components/PatternPanel/PatternPanel';
import { SelectionContextMenu } from '../ui/components/SelectionContextMenu/SelectionContextMenu';
import { SizeControls } from '../ui/components/SizeControls/SizeControls';
import { Toolbar } from '../ui/components/Toolbar/Toolbar';
import { useCanvasState } from '../ui/hooks/useCanvasState';
import { useDragPattern } from '../ui/hooks/useDragPattern';
import { usePatterns } from '../ui/hooks/usePatterns';
import './App.css';

export function App() {
  const {
    addColumnsLeft,
    addRowsTop,
    applyPattern,
    canvas,
    clear,
    clearBlock,
    fillBlock,
    pasteBlock,
    replaceCanvas,
    resize,
    setCell,
    toggleCell,
  } = useCanvasState();
  const { clearDraggedPattern, draggedPattern, startDragPattern } = useDragPattern();
  const { patterns, errors, isLoading } = usePatterns();
  const [blockClipboard, setBlockClipboard] = useState<CanvasBlock | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [selectionContextMenu, setSelectionContextMenu] = useState<{
    left: number;
    top: number;
  } | null>(null);
  const [selection, setSelection] = useState<SelectionRect | null>(null);

  useEffect(() => {
    if (!selectionContextMenu) {
      return;
    }

    const closeMenu = () => setSelectionContextMenu(null);

    window.addEventListener('pointerdown', closeMenu);
    window.addEventListener('keydown', closeMenu);

    return () => {
      window.removeEventListener('pointerdown', closeMenu);
      window.removeEventListener('keydown', closeMenu);
    };
  }, [selectionContextMenu]);

  const handleSaveJson = () => {
    downloadJson('filet-crochet-canvas.json', createCanvasFile(canvas));
  };

  const handleClear = () => {
    if (window.confirm('Очистить рабочую область?')) {
      clear();
      setSelection(null);
      setSelectionContextMenu(null);
    }
  };

  const handleExportPng = () => {
    exportCanvasToPng(canvas);
  };

  const handleLoadJson = async (file: File) => {
    try {
      const data = await readJsonFile(file);
      const validation = validateCanvasFile(data);

      if (!validation.canvas) {
        setImportError(validation.errors.join(' '));
        return;
      }

      replaceCanvas(validation.canvas);
      setSelection(null);
      setSelectionContextMenu(null);
      setImportError(null);
    } catch {
      setImportError('Не удалось прочитать JSON-файл.');
    }
  };

  const handleResize = (width: number, height: number) => {
    resize(width, height);
    setSelection(null);
    setSelectionContextMenu(null);
  };

  const handleAddRowTop = () => {
    addRowsTop();
    setSelection(null);
    setSelectionContextMenu(null);
  };

  const handleAddColumnLeft = () => {
    addColumnsLeft();
    setSelection(null);
    setSelectionContextMenu(null);
  };

  const handleCopyBlock = () => {
    if (!selection) {
      return;
    }

    setBlockClipboard(copyCanvasBlock(canvas, selection));
    setSelectionContextMenu(null);
  };

  const handleCutBlock = () => {
    if (!selection) {
      return;
    }

    setBlockClipboard(copyCanvasBlock(canvas, selection));
    clearBlock(selection);
    setSelectionContextMenu(null);
  };

  const handlePasteBlock = () => {
    if (!selection || !blockClipboard) {
      return;
    }

    const pastePosition = normalizeSelectionRect(selection);
    pasteBlock(blockClipboard, pastePosition.top, pastePosition.left);
    setSelectionContextMenu(null);
  };

  const handleClearBlock = () => {
    if (selection) {
      clearBlock(selection);
      setSelectionContextMenu(null);
    }
  };

  const handleFillBlock = () => {
    if (selection) {
      fillBlock(selection);
      setSelectionContextMenu(null);
    }
  };

  const handleRotateBlock = () => {
    if (!selection) {
      return;
    }

    const result = rotateCanvasBlockClockwise(canvas, selection);
    replaceCanvas(result.canvas);
    setSelection(result.selection);
    setSelectionContextMenu(null);
  };

  const handleFlipBlockHorizontal = () => {
    if (!selection) {
      return;
    }

    const result = flipCanvasBlockHorizontal(canvas, selection);
    replaceCanvas(result.canvas);
    setSelection(result.selection);
    setSelectionContextMenu(null);
  };

  const handleFlipBlockVertical = () => {
    if (!selection) {
      return;
    }

    const result = flipCanvasBlockVertical(canvas, selection);
    replaceCanvas(result.canvas);
    setSelection(result.selection);
    setSelectionContextMenu(null);
  };

  const handleToggleSelectionMode = () => {
    setIsSelectionMode((current) => {
      if (current) {
        setSelection(null);
        setSelectionContextMenu(null);
      }

      return !current;
    });
  };

  return (
    <main className="app-shell">
      <section className="workspace-panel" aria-labelledby="workspace-title">
        <div className="panel-header">
          <div>
            <h1 id="workspace-title">Редактор схемы</h1>
            <p>Клик по клетке переключает заполнение.</p>
          </div>
          <div className="workspace-tools">
            <SizeControls
              width={canvas.width}
              height={canvas.height}
              onApplySize={handleResize}
            />
            <div className="canvas-edge-actions" aria-label="Добавление строк и столбцов">
              <button type="button" onClick={handleAddRowTop}>
                + Строка сверху
              </button>

              <button type="button" onClick={handleAddColumnLeft}>
                + Столбец слева
              </button>
            </div>
          </div>
        </div>

        <Toolbar
          importError={importError}
          isSelectionMode={isSelectionMode}
          onClear={handleClear}
          onExportPng={handleExportPng}
          onLoadJson={handleLoadJson}
          onSaveJson={handleSaveJson}
          onToggleSelectionMode={handleToggleSelectionMode}
        />

        <CanvasGrid
          canvas={canvas}
          draggedPattern={draggedPattern}
          isSelectionMode={isSelectionMode}
          onDropPattern={(pattern, row, col) => {
            applyPattern(pattern, row, col);
            clearDraggedPattern();
          }}
          onSelectRect={setSelection}
          onSelectionContextMenu={(left, top) => setSelectionContextMenu({ left, top })}
          onSetCell={setCell}
          onToggleCell={toggleCell}
          selection={selection}
        />

        {selectionContextMenu && selection ? (
          <SelectionContextMenu
            canPaste={Boolean(blockClipboard)}
            left={selectionContextMenu.left}
            top={selectionContextMenu.top}
            onClear={handleClearBlock}
            onCopy={handleCopyBlock}
            onCut={handleCutBlock}
            onFill={handleFillBlock}
            onFlipHorizontal={handleFlipBlockHorizontal}
            onFlipVertical={handleFlipBlockVertical}
            onPaste={handlePasteBlock}
            onRotate={handleRotateBlock}
          />
        ) : null}
      </section>

      <PatternPanel
        patterns={patterns}
        errors={errors}
        isLoading={isLoading}
        onPatternDragEnd={clearDraggedPattern}
        onPatternDragStart={startDragPattern}
      />
    </main>
  );
}
