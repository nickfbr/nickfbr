/**
 * Thin typed client over the Recipe Box backend.
 *
 * - Base URL comes from EXPO_PUBLIC_API_URL (default http://localhost:8000).
 * - Holds a JWT in memory and persists it via lib/storage.
 * - All backend errors arrive as { error: { code, message, fields? } } and
 *   are surfaced as ApiError.
 */
import { clearToken, loadToken, saveToken } from './storage';
import type {
  AuthResponse,
  ApiErrorEnvelope,
  ParseResponse,
  RecipeCreate,
  RecipeOut,
} from './types';

const BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  code: string;
  fields?: Record<string, unknown>;

  constructor(code: string, message: string, fields?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.fields = fields;
  }
}

let inMemoryToken: string | null = null;

export async function initAuth(): Promise<string | null> {
  inMemoryToken = await loadToken();
  return inMemoryToken;
}

export function getToken(): string | null {
  return inMemoryToken;
}

async function setToken(token: string): Promise<void> {
  inMemoryToken = token;
  await saveToken(token);
}

export async function logout(): Promise<void> {
  inMemoryToken = null;
  await clearToken();
}

function isErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  return (
    typeof value === 'object' &&
    value !== null &&
    'error' in value &&
    typeof (value as { error: unknown }).error === 'object' &&
    (value as { error: unknown }).error !== null
  );
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, auth = true } = options;

  const headers: Record<string, string> = {
    Accept: 'application/json',
  };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  if (auth && inMemoryToken) {
    headers.Authorization = `Bearer ${inMemoryToken}`;
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      'NETWORK_ERROR',
      'Could not reach the server. Check your connection and try again.',
    );
  }

  const text = await response.text();
  let payload: unknown = undefined;
  if (text.length > 0) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = undefined;
    }
  }

  if (!response.ok) {
    if (isErrorEnvelope(payload)) {
      const { code, message, fields } = payload.error;
      throw new ApiError(code, message, fields);
    }
    throw new ApiError(
      'HTTP_ERROR',
      `Request failed with status ${response.status}.`,
    );
  }

  return payload as T;
}

// --- Auth -------------------------------------------------------------------

export async function register(email: string, password: string): Promise<string> {
  const data = await request<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: { email, password },
    auth: false,
  });
  await setToken(data.accessToken);
  return data.accessToken;
}

export async function login(email: string, password: string): Promise<string> {
  const data = await request<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: { email, password },
    auth: false,
  });
  await setToken(data.accessToken);
  return data.accessToken;
}

// --- Recipes ----------------------------------------------------------------

export function listRecipes(): Promise<RecipeOut[]> {
  return request<RecipeOut[]>('/api/recipes');
}

export function getRecipe(id: number): Promise<RecipeOut> {
  return request<RecipeOut>(`/api/recipes/${id}`);
}

export function createRecipe(payload: RecipeCreate): Promise<RecipeOut> {
  return request<RecipeOut>('/api/recipes', {
    method: 'POST',
    body: payload,
  });
}

export function parseRecipe(input: { text?: string; url?: string }): Promise<ParseResponse> {
  return request<ParseResponse>('/api/recipes/parse', {
    method: 'POST',
    body: input,
  });
}
