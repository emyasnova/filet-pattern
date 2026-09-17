// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import * as repository from '../../../infrastructure/patternRepository';
import { PatternPanel } from './PatternPanel';

vi.mock('../../../infrastructure/patternRepository', async (importOriginal) => ({
  ...await importOriginal<typeof repository>(),
  loadPublicConfig: vi.fn(),
  loadPatterns: vi.fn(),
  loadCategories: vi.fn(),
  loadTags: vi.fn(),
  detectImageSize: vi.fn(),
  generatePatternPreview: vi.fn(),
  createPattern: vi.fn(),
}));

beforeEach(() => {
  vi.resetAllMocks();
  // jsdom does not implement the native dialog lifecycle.
  Object.defineProperties(HTMLDialogElement.prototype, {
    showModal: { configurable: true, value: function (this: HTMLDialogElement) { this.open = true; } },
    close: { configurable: true, value: function (this: HTMLDialogElement) { this.open = false; } },
  });
  vi.mocked(repository.loadPublicConfig).mockResolvedValue({ patternCreationEnabled: true });
  vi.mocked(repository.loadPatterns).mockResolvedValue({ patterns: [], errors: [] });
  vi.mocked(repository.loadCategories).mockResolvedValue([{ slug: 'ornament', name: 'Орнамент' }]);
  vi.mocked(repository.loadTags).mockResolvedValue([]);
  vi.mocked(repository.detectImageSize).mockResolvedValue({ width: 1, height: 1 });
  vi.mocked(repository.generatePatternPreview).mockResolvedValue({
    width: 1, height: 1, threshold: 128, fillThreshold: 0.35, cells: [[1]],
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function renderPanel() {
  return render(<PatternPanel onPatternDragStart={vi.fn()} onPatternDragEnd={vi.fn()} />);
}

async function openImport() {
  renderPanel();
  fireEvent.click(await screen.findByRole('button', { name: 'Добавить паттерн' }));
  expect(screen.getByRole('dialog')).toBeTruthy();
  fireEvent.change(screen.getByLabelText('Изображение'), {
    target: { files: [new File(['image'], 'rose.png', { type: 'image/png' })] },
  });
}

describe('pattern creation availability', () => {
  it('hides import until configuration is loaded, then allows opening the form', async () => {
    let resolve!: (config: { patternCreationEnabled: boolean }) => void;
    vi.mocked(repository.loadPublicConfig).mockReturnValue(new Promise((done) => { resolve = done; }));
    renderPanel();
    expect(screen.queryByRole('button', { name: 'Добавить паттерн' })).toBeNull();
    expect(screen.queryByRole('dialog')).toBeNull();
    await act(async () => resolve({ patternCreationEnabled: true }));
    fireEvent.click(screen.getByRole('button', { name: 'Добавить паттерн' }));
    expect(screen.getByRole('dialog')).toBeTruthy();
  });

  it.each(['disabled', 'config error'] as const)('keeps the catalog available with %s', async (state) => {
    if (state === 'disabled') {
      vi.mocked(repository.loadPublicConfig).mockResolvedValue({ patternCreationEnabled: false });
    } else {
      vi.mocked(repository.loadPublicConfig).mockRejectedValue(new Error('Unavailable'));
    }
    renderPanel();
    await screen.findByText('Мотивы не найдены');
    expect(screen.queryByRole('button', { name: 'Добавить паттерн' })).toBeNull();
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(screen.getByRole('searchbox', { name: 'Поиск' })).toBeTruthy();
    expect(repository.loadPatterns).toHaveBeenCalled();
    expect(repository.loadCategories).toHaveBeenCalled();
    expect(repository.loadTags).toHaveBeenCalled();
  });

  it.each(['size', 'preview', 'save'] as const)('closes import and shows a neutral notice after %s returns 403', async (stage) => {
    const error = new repository.ApiRequestError(403, 'Pattern creation is currently unavailable');
    if (stage === 'size') vi.mocked(repository.detectImageSize).mockRejectedValue(error);
    if (stage === 'preview') vi.mocked(repository.generatePatternPreview).mockRejectedValue(error);
    if (stage === 'save') vi.mocked(repository.createPattern).mockRejectedValue(error);
    await openImport();
    fireEvent.click(screen.getByRole('button', { name: 'Распознать' }));
    if (stage === 'save') {
      const next = screen.getByRole('button', { name: 'Далее' }) as HTMLButtonElement;
      await waitFor(() => expect(next.disabled).toBe(false));
      fireEvent.click(next);
      fireEvent.change(screen.getByLabelText('Категория', { selector: '.pattern-metadata select' }), {
        target: { value: 'ornament' },
      });
      fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }));
    }
    await screen.findByText('Добавление паттернов сейчас недоступно.');
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Добавить паттерн' })).toBeNull();
    expect(screen.queryByText(/Введите ширину и высоту вручную/)).toBeNull();
    if (stage === 'size') expect(repository.generatePatternPreview).not.toHaveBeenCalled();
    if (stage !== 'save') expect(repository.createPattern).not.toHaveBeenCalled();
  });

  it('allows manual dimensions after an ordinary detection error', async () => {
    vi.mocked(repository.detectImageSize).mockRejectedValue(new repository.ApiRequestError(422, 'No grid'));
    await openImport();
    fireEvent.click(screen.getByRole('button', { name: 'Распознать' }));
    await screen.findByText(/Введите ширину и высоту вручную/);
    expect(screen.getByRole('dialog')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Ширина сетки'), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Высота сетки'), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Распознать' }));
    await waitFor(() => expect(repository.generatePatternPreview).toHaveBeenCalledOnce());
    expect(repository.detectImageSize).toHaveBeenCalledOnce();
  });
});
