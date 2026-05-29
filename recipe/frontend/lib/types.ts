import type { Unit } from '@/theme';

export interface Ingredient {
  name: string;
  quantity: number | null;
  unit: Unit | string;
  raw: string | null;
}

export interface Instruction {
  stepNumber: number;
  text: string;
}

export interface RecipeCreate {
  title: string;
  description: string | null;
  servings: number | null;
  prepTime: number | null;
  cookTime: number | null;
  sourceUrl: string | null;
  ingredients: Ingredient[];
  instructions: Instruction[];
}

export interface RecipeOut extends RecipeCreate {
  id: number;
}

export interface ParseDraft {
  title: string | null;
  description: string | null;
  ingredients: Array<{
    name: string;
    quantity: number | null;
    unit: Unit | string;
    raw: string;
  }>;
  instructions: Instruction[];
  servings: number | null;
  prepTime: number | null;
  cookTime: number | null;
  sourceUrl: string | null;
}

export type ParseMethod = 'structured_data' | 'llm' | 'llm_fallback';
export type Confidence = 'high' | 'medium' | 'low';

export interface ParseMeta {
  parseMethod: ParseMethod;
  confidence: Confidence;
  warnings: string[];
  unmappedUnits: string[];
}

export interface ParseResponse {
  draft: ParseDraft;
  meta: ParseMeta;
}

export interface AuthResponse {
  accessToken: string;
  tokenType: string;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    fields?: Record<string, unknown>;
  };
}
