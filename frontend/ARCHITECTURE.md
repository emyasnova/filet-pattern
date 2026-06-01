# ARCHITECTURE.md

## Общая идея

Приложение реализуется как frontend-only React-приложение.

Слои:

```text
UI → Application → Domain
UI → Infrastructure
Application → Infrastructure
```

Главный принцип: операции над клетками и матрицами не должны быть размазаны по React-компонентам.

## Рекомендуемая структура

```text
src/
  app/
    App.tsx
    App.css

  domain/
    cell.ts
    pattern.ts
    canvas.ts
    matrix.ts
    transformations.ts

  application/
    applyPatternToCanvas.ts
    resizeCanvas.ts
    toggleCanvasCell.ts
    createEmptyCanvas.ts
    validatePattern.ts
    validateCanvasFile.ts

  infrastructure/
    patternRepository.ts
    downloadJson.ts
    readJsonFile.ts
    exportCanvasToPng.ts

  ui/
    components/
      Layout/
      Toolbar/
      CanvasGrid/
      PatternPanel/
      PatternCard/
      PatternPreview/
      SizeControls/
      ErrorMessage/
    hooks/
      useCanvasState.ts
      usePatterns.ts
      useDragPattern.ts
    styles/

  main.tsx
```

Структуру можно адаптировать, но разделение ответственности нужно сохранить.

## Domain

### `cell.ts`

Типы клеток:

```ts
export type PatternCell = 0 | 1 | null;
export type CanvasCell = 0 | 1;
```

### `pattern.ts`

Тип мотива:

```ts
export interface Pattern {
  id: string;
  char?: string;
  name?: string;
  width: number;
  height: number;
  cells: PatternCell[][];
}
```

### `canvas.ts`

Тип рабочей области:

```ts
export interface CanvasState {
  width: number;
  height: number;
  cells: CanvasCell[][];
}
```

### `transformations.ts`

Чистые функции:

```ts
rotatePatternClockwise(pattern): Pattern
flipPatternHorizontal(pattern): Pattern
flipPatternVertical(pattern): Pattern
```

Требование: функции не мутируют исходный объект.

## Application

### `createEmptyCanvas.ts`

Создает пустую рабочую область заданного размера.

### `resizeCanvas.ts`

Изменяет размер рабочей области.

Правила:

- старые клетки сохраняются в пределах нового размера;
- новые клетки заполняются `0`;
- лишние клетки обрезаются.

### `toggleCanvasCell.ts`

Переключает одну клетку `0 ↔ 1`.

### `applyPatternToCanvas.ts`

Вставляет мотив на рабочую область.

Сигнатура может быть примерно такой:

```ts
applyPatternToCanvas(
  canvas: CanvasState,
  pattern: Pattern,
  startRow: number,
  startCol: number
): CanvasState
```

Правила вставки:

- `1` из мотива записывает `1`;
- `0` из мотива записывает `0`;
- `null` ничего не меняет;
- выход за границы рабочей области обрезается;
- исходный canvas не мутируется.

### `validatePattern.ts`

Проверяет JSON-мотивы.

### `validateCanvasFile.ts`

Проверяет JSON-файл рабочей области перед загрузкой.

## Infrastructure

### `patternRepository.ts`

Отвечает за загрузку мотивов из:

```text
/public/patterns/index.json
```

Ожидаемый формат index:

```json
{
  "patterns": ["B.json", "flower.json"]
}
```

Алгоритм:

1. Загрузить `/patterns/index.json`.
2. Для каждого имени файла загрузить `/patterns/{fileName}`.
3. Провалидировать мотив.
4. Вернуть список валидных мотивов и список ошибок, если они есть.

### `downloadJson.ts`

Скачивает текущую рабочую область как JSON-файл.

### `readJsonFile.ts`

Читает выбранный пользователем JSON-файл.

### `exportCanvasToPng.ts`

Создает PNG через HTMLCanvasElement.

Рекомендуемые параметры:

- размер клетки для экспорта: например 12 px;
- поля сверху/снизу для текста с размерами;
- белый фон;
- черные заполненные клетки;
- тонкая серая сетка;
- более заметные линии каждые 10 клеток.

## UI

### `CanvasGrid`

Отображает рабочую область.

Отвечает за:

- отображение клеток;
- клик по клетке;
- drag-over;
- drop;
- preview вставки.

Не должен содержать сложную бизнес-логику вставки мотива — для этого используется application-функция.

### `PatternPanel`

Отображает список карточек мотивов.

### `PatternCard`

Отображает один мотив и кнопки трансформации.

Важно: состояние трансформированного мотива должно храниться на уровне карточки или в структуре состояния панели, чтобы каждая карточка могла иметь собственную текущую версию.

### `Toolbar`

Содержит кнопки:

- “Сгенерировать изображение”;
- “Сохранить JSON”;
- “Загрузить JSON”;
- “Очистить”.

### `SizeControls`

Поля изменения ширины и высоты рабочей области.

## Drag-and-drop

Можно использовать native HTML Drag and Drop API.

Важно:

- при начале drag нужно сохранить id текущего мотива;
- при drag-over рабочей области нужно вычислять клетку под курсором;
- preview должен строиться на основе текущего transformed-состояния мотива;
- при drop вызывается `applyPatternToCanvas`.

Альтернатива: использовать pointer events, если native drag-and-drop окажется неудобным. Для MVP сначала использовать native API.

## Производительность

Сетка 100 × 100 — это 10 000 клеток. React может справиться, но нужно избегать лишних перерендеров.

Рекомендации:

- вынести клетку в простой компонент или использовать CSS grid;
- не хранить лишнее состояние в каждой клетке;
- preview вычислять аккуратно;
- по возможности мемоизировать тяжелые вычисления.

Если производительность будет плохой, можно перейти к отрисовке рабочей области через `<canvas>`, но для MVP начинаем с DOM/CSS grid.
