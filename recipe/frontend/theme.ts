/**
 * App theme: dark surfaces with a gold gradient primary accent.
 */

export const colors = {
  background: '#121212',
  surface: '#1E1E1E',
  surfaceAlt: '#262626',
  border: '#333333',
  text: '#F5F5F5',
  textMuted: '#A0A0A0',
  amber: '#F0A500',
  error: '#FF6B6B',
  // Primary gold gradient + the dark text that sits on top of it.
  gradientStart: '#F5C242',
  gradientEnd: '#E0992E',
  onGradient: '#1A1A1A',
} as const;

export const gradientColors: readonly [string, string] = [
  colors.gradientStart,
  colors.gradientEnd,
];

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radii = {
  sm: 6,
  md: 8,
  lg: 12,
  xl: 16,
  pill: 999,
} as const;

export const fontSizes = {
  sm: 13,
  md: 15,
  lg: 18,
  xl: 22,
  xxl: 28,
} as const;

/** The 12 canonical ingredient units the API accepts. */
export const UNITS = [
  'cups',
  'tbsp',
  'tsp',
  'g',
  'oz',
  'ml',
  'L',
  'kg',
  'whole',
  'pinch',
  'lb',
  'fl_oz',
] as const;

export type Unit = (typeof UNITS)[number];
