import { Link, useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Banner } from '@/components/Banner';
import { ApiError, listRecipes, logout } from '@/lib/api';
import type { RecipeOut } from '@/lib/types';
import { colors, fontSizes, radii, spacing } from '@/theme';

function formatTime(minutes: number | null): string | null {
  if (minutes === null || minutes === undefined) {
    return null;
  }
  return `${minutes} min`;
}

function RecipeCard({ recipe }: { recipe: RecipeOut }) {
  const meta: string[] = [];
  if (recipe.servings !== null && recipe.servings !== undefined) {
    meta.push(`${recipe.servings} servings`);
  }
  const prep = formatTime(recipe.prepTime);
  if (prep) {
    meta.push(`Prep ${prep}`);
  }
  const cook = formatTime(recipe.cookTime);
  if (cook) {
    meta.push(`Cook ${cook}`);
  }

  return (
    <Link href={`/recipe/${recipe.id}`} asChild>
      <Pressable
        style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
      >
        <Text style={styles.cardTitle} numberOfLines={2}>
          {recipe.title}
        </Text>
        {recipe.description ? (
          <Text style={styles.cardDescription} numberOfLines={2}>
            {recipe.description}
          </Text>
        ) : null}
        {meta.length > 0 ? (
          <Text style={styles.cardMeta}>{meta.join('  •  ')}</Text>
        ) : null}
      </Pressable>
    </Link>
  );
}

export default function RecipeListScreen() {
  const router = useRouter();
  const [recipes, setRecipes] = useState<RecipeOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await listRecipes();
      setRecipes(data);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Could not load recipes.',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const handleLogout = async () => {
    await logout();
    router.replace('/login');
  };

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.gradientStart} />
        </View>
      ) : (
        <FlatList
          data={recipes}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => <RecipeCard recipe={item} />}
          ListHeaderComponent={
            error ? <Banner message={error} tone="error" /> : null
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyTitle}>No recipes yet</Text>
              <Text style={styles.emptyText}>
                Tap the + button to add or import your first recipe.
              </Text>
            </View>
          }
          refreshing={loading}
          onRefresh={load}
        />
      )}

      <Pressable
        style={styles.logout}
        onPress={handleLogout}
        accessibilityLabel="Log out"
      >
        <Text style={styles.logoutText}>Log out</Text>
      </Pressable>

      <Pressable
        style={({ pressed }) => [styles.fab, pressed && styles.fabPressed]}
        onPress={() => router.push('/recipe/add')}
        accessibilityRole="button"
        accessibilityLabel="Add recipe"
      >
        <Text style={styles.fabIcon}>+</Text>
      </Pressable>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.background,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  list: {
    padding: spacing.lg,
    paddingBottom: 96,
    flexGrow: 1,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardPressed: {
    opacity: 0.8,
  },
  cardTitle: {
    color: colors.text,
    fontSize: fontSizes.lg,
    fontWeight: '700',
  },
  cardDescription: {
    color: colors.textMuted,
    fontSize: fontSizes.sm,
    marginTop: spacing.xs,
  },
  cardMeta: {
    color: colors.gradientStart,
    fontSize: fontSizes.sm,
    marginTop: spacing.sm,
    fontWeight: '600',
  },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: spacing.xxl,
  },
  emptyTitle: {
    color: colors.text,
    fontSize: fontSizes.lg,
    fontWeight: '700',
  },
  emptyText: {
    color: colors.textMuted,
    fontSize: fontSizes.md,
    textAlign: 'center',
    marginTop: spacing.sm,
    paddingHorizontal: spacing.xl,
  },
  logout: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.lg,
  },
  logoutText: {
    color: colors.textMuted,
    fontSize: fontSizes.sm,
  },
  fab: {
    position: 'absolute',
    right: spacing.xl,
    bottom: spacing.xl,
    width: 60,
    height: 60,
    borderRadius: radii.pill,
    backgroundColor: colors.gradientStart,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 6,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
  },
  fabPressed: {
    opacity: 0.85,
  },
  fabIcon: {
    color: colors.onGradient,
    fontSize: 32,
    fontWeight: '700',
    lineHeight: 36,
  },
});
