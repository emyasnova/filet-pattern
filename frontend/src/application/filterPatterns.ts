import type { Pattern, PatternCategory } from '../domain/pattern';

export const PATTERN_CATEGORY_LABELS: Record<PatternCategory, string> = {
  alphabet: 'Алфавит',
  frame: 'Рамки',
  object: 'Объекты',
  ornament: 'Орнаменты',
  uncategorized: 'Без категории',
};

export const PATTERN_CATEGORY_OPTIONS: PatternCategory[] = [
  'alphabet',
  'frame',
  'object',
  'ornament',
  'uncategorized',
];

export interface PatternFilters {
  category: PatternCategory | 'all';
  query: string;
  tags: string[];
}

export function filterPatterns(
  patterns: Pattern[],
  filters: PatternFilters,
): Pattern[] {
  const normalizedQuery = normalizeSearchValue(filters.query);
  const normalizedTags = filters.tags.map(normalizeSearchValue);

  return patterns.filter((pattern) => {
    if (filters.category !== 'all' && pattern.category !== filters.category) {
      return false;
    }

    if (
      normalizedTags.length > 0 &&
      !normalizedTags.every((tag) =>
        pattern.tags.some((patternTag) => normalizeSearchValue(patternTag) === tag),
      )
    ) {
      return false;
    }

    if (!normalizedQuery) {
      return true;
    }

    return getPatternSearchValues(pattern).some((value) =>
      normalizeSearchValue(value).includes(normalizedQuery),
    );
  });
}

export function getAvailablePatternTags(patterns: Pattern[]): string[] {
  return [...new Set(patterns.flatMap((pattern) => pattern.tags))]
    .filter(Boolean)
    .sort((left, right) => left.localeCompare(right, 'ru'));
}

function getPatternSearchValues(pattern: Pattern): string[] {
  return [
    pattern.id,
    pattern.char ?? '',
    pattern.name ?? '',
    pattern.category,
    PATTERN_CATEGORY_LABELS[pattern.category],
    ...pattern.tags,
  ];
}

function normalizeSearchValue(value: string): string {
  return value.trim().toLocaleLowerCase('ru');
}
