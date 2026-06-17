/**
 * Editable form-row models. Numeric fields are held as strings while editing
 * and converted to numbers (or null) on save.
 */
import type { Unit } from '@/theme';
import type {
  Ingredient,
  Instruction,
  ParseDraft,
  RecipeCreate,
} from './types';

export interface IngredientRowData {
  name: string;
  quantity: string;
  unit: Unit | string;
  raw: string | null;
}

export interface InstructionRowData {
  text: string;
}

export interface RecipeForm {
  title: string;
  description: string;
  servings: string;
  prepTime: string;
  cookTime: string;
  sourceUrl: string;
  ingredients: IngredientRowData[];
  instructions: InstructionRowData[];
}

export function emptyIngredient(): IngredientRowData {
  return { name: '', quantity: '', unit: '', raw: null };
}

export function emptyInstruction(): InstructionRowData {
  return { text: '' };
}

export function emptyForm(): RecipeForm {
  return {
    title: '',
    description: '',
    servings: '',
    prepTime: '',
    cookTime: '',
    sourceUrl: '',
    ingredients: [emptyIngredient()],
    instructions: [emptyInstruction()],
  };
}

function numToStr(value: number | null): string {
  return value === null || value === undefined ? '' : String(value);
}

export function formFromDraft(draft: ParseDraft): RecipeForm {
  return {
    title: draft.title ?? '',
    description: draft.description ?? '',
    servings: numToStr(draft.servings),
    prepTime: numToStr(draft.prepTime),
    cookTime: numToStr(draft.cookTime),
    sourceUrl: draft.sourceUrl ?? '',
    ingredients:
      draft.ingredients.length > 0
        ? draft.ingredients.map((ing) => ({
            name: ing.name,
            quantity: numToStr(ing.quantity),
            unit: ing.unit,
            raw: ing.raw ?? null,
          }))
        : [emptyIngredient()],
    instructions:
      draft.instructions.length > 0
        ? draft.instructions
            .slice()
            .sort((a, b) => a.stepNumber - b.stepNumber)
            .map((step) => ({ text: step.text }))
        : [emptyInstruction()],
  };
}

function parseNumberOrNull(value: string): number | null {
  const trimmed = value.trim();
  if (trimmed === '') {
    return null;
  }
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formToPayload(form: RecipeForm): RecipeCreate {
  const ingredients: Ingredient[] = form.ingredients
    .filter((ing) => ing.name.trim() !== '')
    .map((ing) => ({
      name: ing.name.trim(),
      quantity: parseNumberOrNull(ing.quantity),
      unit: ing.unit,
      raw: ing.raw && ing.raw.trim() !== '' ? ing.raw : null,
    }));

  const instructions: Instruction[] = form.instructions
    .filter((step) => step.text.trim() !== '')
    .map((step, index) => ({
      stepNumber: index + 1,
      text: step.text.trim(),
    }));

  const description = form.description.trim();
  const sourceUrl = form.sourceUrl.trim();

  return {
    title: form.title.trim(),
    description: description === '' ? null : description,
    servings: parseNumberOrNull(form.servings),
    prepTime: parseNumberOrNull(form.prepTime),
    cookTime: parseNumberOrNull(form.cookTime),
    sourceUrl: sourceUrl === '' ? null : sourceUrl,
    ingredients,
    instructions,
  };
}

/**
 * An ingredient row should be flagged for review when its unit was unmapped by
 * the parser, or when it has no quantity.
 */
export function ingredientNeedsReview(
  ing: IngredientRowData,
  unmappedUnits: string[],
): boolean {
  const quantityMissing = ing.quantity.trim() === '';
  const unitUnmapped = ing.unit !== '' && unmappedUnits.includes(ing.unit);
  return quantityMissing || unitUnmapped;
}
