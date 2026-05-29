import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Banner } from '@/components/Banner';
import { ApiError, getRecipe } from '@/lib/api';
import type { Ingredient, RecipeOut } from '@/lib/types';
import { colors, fontSizes, radii, spacing } from '@/theme';

function ingredientLine(ing: Ingredient): string {
  const parts: string[] = [];
  if (ing.quantity !== null && ing.quantity !== undefined) {
    parts.push(String(ing.quantity));
  }
  if (ing.unit && ing.unit !== 'whole') {
    parts.push(ing.unit);
  }
  parts.push(ing.name);
  return parts.join(' ');
}

export default function RecipeDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [recipe, setRecipe] = useState<RecipeOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const numericId = Number(id);
    if (!Number.isFinite(numericId)) {
      setError('Invalid recipe.');
      setLoading(false);
      return;
    }
    getRecipe(numericId)
      .then((data) => {
        if (mounted) {
          setRecipe(data);
        }
      })
      .catch((err: unknown) => {
        if (mounted) {
          setError(
            err instanceof ApiError ? err.message : 'Could not load recipe.',
          );
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [id]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.gradientStart} />
      </View>
    );
  }

  if (error || !recipe) {
    return (
      <View style={styles.errorWrap}>
        <Banner message={error ?? 'Recipe not found.'} tone="error" />
      </View>
    );
  }

  const meta: string[] = [];
  if (recipe.servings !== null && recipe.servings !== undefined) {
    meta.push(`${recipe.servings} servings`);
  }
  if (recipe.prepTime !== null && recipe.prepTime !== undefined) {
    meta.push(`Prep ${recipe.prepTime} min`);
  }
  if (recipe.cookTime !== null && recipe.cookTime !== undefined) {
    meta.push(`Cook ${recipe.cookTime} min`);
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.title}>{recipe.title}</Text>
      {meta.length > 0 ? (
        <Text style={styles.meta}>{meta.join('  •  ')}</Text>
      ) : null}
      {recipe.description ? (
        <Text style={styles.description}>{recipe.description}</Text>
      ) : null}

      <Text style={styles.sectionTitle}>Ingredients</Text>
      {recipe.ingredients.length === 0 ? (
        <Text style={styles.muted}>No ingredients listed.</Text>
      ) : (
        recipe.ingredients.map((ing, index) => (
          <View key={index} style={styles.ingredientRow}>
            <View style={styles.bullet} />
            <Text style={styles.ingredientText}>{ingredientLine(ing)}</Text>
          </View>
        ))
      )}

      <Text style={styles.sectionTitle}>Instructions</Text>
      {recipe.instructions.length === 0 ? (
        <Text style={styles.muted}>No instructions listed.</Text>
      ) : (
        recipe.instructions
          .slice()
          .sort((a, b) => a.stepNumber - b.stepNumber)
          .map((step) => (
            <View key={step.stepNumber} style={styles.stepRow}>
              <View style={styles.stepBadge}>
                <Text style={styles.stepBadgeText}>{step.stepNumber}</Text>
              </View>
              <Text style={styles.stepText}>{step.text}</Text>
            </View>
          ))
      )}

      {recipe.sourceUrl ? (
        <Text style={styles.source} numberOfLines={1}>
          Source: {recipe.sourceUrl}
        </Text>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  errorWrap: {
    flex: 1,
    backgroundColor: colors.background,
    padding: spacing.lg,
    justifyContent: 'center',
  },
  title: {
    color: colors.text,
    fontSize: fontSizes.xxl,
    fontWeight: '800',
  },
  meta: {
    color: colors.gradientStart,
    fontSize: fontSizes.md,
    fontWeight: '600',
    marginTop: spacing.sm,
  },
  description: {
    color: colors.textMuted,
    fontSize: fontSizes.md,
    marginTop: spacing.md,
    lineHeight: 22,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: fontSizes.lg,
    fontWeight: '700',
    marginTop: spacing.xl,
    marginBottom: spacing.md,
  },
  muted: {
    color: colors.textMuted,
    fontSize: fontSizes.md,
  },
  ingredientRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  bullet: {
    width: 6,
    height: 6,
    borderRadius: radii.pill,
    backgroundColor: colors.gradientStart,
    marginRight: spacing.md,
  },
  ingredientText: {
    color: colors.text,
    fontSize: fontSizes.md,
    flex: 1,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  stepBadge: {
    width: 26,
    height: 26,
    borderRadius: radii.pill,
    backgroundColor: colors.gradientEnd,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  stepBadgeText: {
    color: colors.onGradient,
    fontWeight: '700',
    fontSize: fontSizes.sm,
  },
  stepText: {
    color: colors.text,
    fontSize: fontSizes.md,
    flex: 1,
    lineHeight: 22,
  },
  source: {
    color: colors.textMuted,
    fontSize: fontSizes.sm,
    marginTop: spacing.xl,
  },
});
