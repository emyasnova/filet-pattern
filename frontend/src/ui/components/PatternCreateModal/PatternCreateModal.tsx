import { useEffect, useMemo, useRef, useState } from 'react';

import { normalizePatternTransparency } from '../../../application/normalizePatternTransparency';
import { getPatternNameFromFile } from '../../../application/patternCreation';
import type { Pattern, PatternCategory, PatternTag } from '../../../domain/pattern';
import {
  createPattern,
  detectImageSize,
  generatePatternPreview,
} from '../../../infrastructure/patternRepository';
import { PatternGridEditor } from '../PatternGridEditor/PatternGridEditor';
import './PatternCreateModal.css';

interface PatternCreateModalProps {
  categories: PatternCategory[];
  availableTags: PatternTag[];
  onClose: () => void;
  onCreated: (pattern: Pattern) => void;
}

type Step = 'recognition' | 'metadata';

export function PatternCreateModal({ categories, availableTags, onClose, onCreated }: PatternCreateModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [step, setStep] = useState<Step>('recognition');
  const [file, setFile] = useState<File | null>(null);
  const [gridWidth, setGridWidth] = useState('');
  const [gridHeight, setGridHeight] = useState('');
  const [threshold, setThreshold] = useState('128');
  const [fillThreshold, setFillThreshold] = useState('0.35');
  const [previewZoom, setPreviewZoom] = useState(14);
  const [preview, setPreview] = useState<Awaited<ReturnType<typeof generatePatternPreview>> | null>(null);
  const [originalCells, setOriginalCells] = useState<Pattern['cells']>([]);
  const [isEdited, setIsEdited] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagDraft, setTagDraft] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
    return () => dialog?.close();
  }, []);

  const isDirty = Boolean(file || preview || name || category || tags.length);
  const requestClose = () => {
    if (!isDirty || window.confirm('Закрыть окно и потерять несохранённые изменения?')) onClose();
  };

  const setSelectedFile = (nextFile: File | null) => {
    setFile(nextFile);
    setName(nextFile ? getPatternNameFromFile(nextFile.name) : '');
    setPreview(null);
    setOriginalCells([]);
    setGridWidth('');
    setGridHeight('');
    setError('');
  };

  const recognize = async () => {
    if (!file) return;
    if (isEdited && !window.confirm('Переформирование сбросит ручные правки. Продолжить?')) return;
    setError('');
    try {
      let width = Number(gridWidth);
      let height = Number(gridHeight);
      if (!width || !height) {
        setStatus('Определяем размер…');
        try {
          const size = await detectImageSize(file);
          width = size.width;
          height = size.height;
          setGridWidth(String(width));
          setGridHeight(String(height));
        } catch (sizeError) {
          setError(`${String(sizeError)}. Введите ширину и высоту вручную.`);
          return;
        }
      }
      setStatus('Строим паттерн…');
      const result = await generatePatternPreview(file, {
        width,
        height,
        threshold: Number(threshold),
        fillThreshold: Number(fillThreshold),
      });
      setPreview(result);
      setOriginalCells(result.cells.map((row) => [...row]));
      setThreshold(String(result.threshold));
      setFillThreshold(String(result.fillThreshold));
      setIsEdited(false);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : String(requestError));
    } finally {
      setStatus('');
    }
  };

  const suggestedTags = useMemo(() => availableTags.map((tag) => tag.name), [availableTags]);
  const parametersValid =
    Number(threshold) >= 0 &&
    Number(threshold) <= 255 &&
    Number(fillThreshold) >= 0 &&
    Number(fillThreshold) <= 1 &&
    (!gridWidth || (Number(gridWidth) >= 1 && Number(gridWidth) <= 500)) &&
    (!gridHeight || (Number(gridHeight) >= 1 && Number(gridHeight) <= 500));
  const addTag = () => {
    const next = tagDraft.trim();
    if (next && !tags.some((tag) => tag.toLocaleLowerCase('ru') === next.toLocaleLowerCase('ru'))) {
      setTags((current) => [...current, next]);
    }
    setTagDraft('');
  };

  const save = async () => {
    if (!preview || !name.trim() || !category) return;
    setIsSaving(true);
    setError('');
    try {
      const cells = normalizePatternTransparency(preview.cells);
      const pattern = await createPattern({ name, category, tags, width: preview.width, height: preview.height, cells });
      onCreated(pattern);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : String(saveError));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <dialog ref={dialogRef} className="pattern-create-dialog" onCancel={(event) => { event.preventDefault(); requestClose(); }}>
      <form method="dialog" className="pattern-create-modal" onSubmit={(event) => event.preventDefault()}>
        <header><div><h2>Добавить паттерн</h2><p>Шаг {step === 'recognition' ? '1 из 2: распознавание' : '2 из 2: описание'}</p></div><button type="button" aria-label="Закрыть" onClick={requestClose}>×</button></header>
        {step === 'recognition' ? (
          <div className="pattern-create-content">
            <label className="pattern-create-file">Изображение<input type="file" accept="image/png,image/jpeg" onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} /></label>
            <div className="pattern-parameters">
              <label>Ширина сетки<input type="number" min="1" max="500" value={gridWidth} onChange={(event) => setGridWidth(event.target.value)} /></label>
              <label>Высота сетки<input type="number" min="1" max="500" value={gridHeight} onChange={(event) => setGridHeight(event.target.value)} /></label>
              <label>Threshold<input type="number" min="0" max="255" value={threshold} onChange={(event) => setThreshold(event.target.value)} /></label>
              <label>Fill threshold<input type="number" min="0" max="1" step="0.01" value={fillThreshold} onChange={(event) => setFillThreshold(event.target.value)} /></label>
            </div>
            <button type="button" disabled={!file || Boolean(status) || !parametersValid} onClick={recognize}>{preview ? 'Переформировать' : 'Распознать'}</button>
            {status ? <p role="status">{status}</p> : null}
            {preview ? <><div className="pattern-result-heading"><label>Масштаб<input type="range" min="8" max="24" value={previewZoom} onChange={(event) => setPreviewZoom(Number(event.target.value))} /></label><button type="button" disabled={!isEdited} onClick={() => { setPreview({ ...preview, cells: originalCells.map((row) => [...row]) }); setIsEdited(false); }}>Сбросить ручные изменения</button></div><PatternGridEditor cells={preview.cells} zoom={previewZoom} onChange={(cells) => { setPreview({ ...preview, cells }); setIsEdited(true); }} /></> : null}
          </div>
        ) : (
          <div className="pattern-create-content pattern-metadata">
            <label>Имя<input autoFocus maxLength={255} value={name} onChange={(event) => setName(event.target.value)} /></label>
            <label>Категория<select value={category} onChange={(event) => setCategory(event.target.value)}><option value="">Выберите категорию</option>{categories.map((item) => <option key={item.slug} value={item.slug}>{item.name}</option>)}</select></label>
            <label>Теги<input list="create-pattern-tags" value={tagDraft} onChange={(event) => setTagDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); addTag(); } }} /><datalist id="create-pattern-tags">{suggestedTags.map((tag) => <option key={tag} value={tag} />)}</datalist></label>
            <button type="button" onClick={addTag}>Добавить тег</button>
            <div className="pattern-tag-chips">{tags.map((tag) => <button type="button" className="pattern-tag-chip" key={tag} onClick={() => setTags((current) => current.filter((item) => item !== tag))}>{tag} ×</button>)}</div>
          </div>
        )}
        {error ? <p className="pattern-create-error" role="alert">{error}</p> : null}
        <footer>{step === 'metadata' ? <button type="button" onClick={() => setStep('recognition')}>Назад</button> : <span />}{step === 'recognition' ? <button type="button" disabled={!preview} onClick={() => { if (preview) { setPreview({ ...preview, cells: normalizePatternTransparency(preview.cells) }); setStep('metadata'); } }}>Далее</button> : <button type="button" disabled={!name.trim() || !category || isSaving} onClick={save}>{isSaving ? 'Сохраняем…' : 'Сохранить'}</button>}</footer>
      </form>
    </dialog>
  );
}
