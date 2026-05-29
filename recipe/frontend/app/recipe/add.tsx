import { useRouter } from 'expo-router';
import { useMemo, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Banner } from '@/components/Banner';
import { GradientButton, OutlineButton } from '@/components/GradientButton';
import { ImportSheet } from '@/components/ImportSheet';
import { IngredientRow } from '@/components/IngredientRow';
import { InstructionRow } from '@/components/InstructionRow';
import { LoadingOverlay } from '@/components/LoadingOverlay';
import { TextField } from '@/components/TextField';
import { ApiError, createRecipe } from '@/lib/api';
import {
  emptyForm,
  emptyIngredient,
  emptyInstruction,
  formFromDraft,
  formToPayload,
  ingredientNeedsReview,
  type RecipeForm,
} from '@/lib/form';
import type { ParseResponse } from '@/lib/types';
import { colors, fontSizes, spacing } from '@/theme';

export default function AddRecipeScreen() {
  const router = useRouter();
  const [form, setForm] = useState<RecipeForm>(emptyForm);
  const [importVisible, setImportVisible] = useState(false);
  const [unmappedUnits, setUnmappedUnits] = useState<string[]>([]);
  const [lowConfidence, setLowConfidence] = useState(false);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const handleParsed = (result: ParseResponse) => {
    setForm(formFromDraft(result.draft));
    setUnmappedUnits(result.meta.unmappedUnits);
    setLowConfidence(result.meta.confidence === 'low');
    setWarnings(result.meta.warnings);
    setImportVisible(false);
  };

  // --- field helpers --------------------------------------------------------
  const setField = <K extends keyof RecipeForm>(key: K, value: RecipeForm[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const updateIngredient = (
    index: number,
    next: RecipeForm['ingredients'][number],
  ) =>
    setForm((prev) => ({
      ...prev,
      ingredients: prev.ingredients.map((ing, i) => (i === index ? next : ing)),
    }));

  const addIngredient = () =>
    setForm((prev) => ({
      ...prev,
      ingredients: [...prev.ingredients, emptyIngredient()],
    }));

  const removeIngredient = (index: number) =>
    setForm((prev) => ({
      ...prev,
      ingredients:
        prev.ingredients.length > 1
          ? prev.ingredients.filter((_, i) => i !== index)
          : [emptyIngredient()],
    }));

  const updateInstruction = (
    index: number,
    next: RecipeForm['instructions'][number],
  ) =>
    setForm((prev) => ({
      ...prev,
      instructions: prev.instructions.map((step, i) =>
        i === index ? next : step,
      ),
    }));

  const addInstruction = () =>
    setForm((prev) => ({
      ...prev,
      instructions: [...prev.instructions, emptyInstruction()],
    }));

  const removeInstruction = (index: number) =>
    setForm((prev) => ({
      ...prev,
      instructions:
        prev.instructions.length > 1
          ? prev.instructions.filter((_, i) => i !== index)
          : [emptyInstruction()],
    }));

  // --- save -----------------------------------------------------------------
  const canSave = useMemo(
    () => form.title.trim() !== '' && !saving,
    [form.title, saving],
  );

  const handleSave = async () => {
    if (form.title.trim() === '') {
      setSaveError('Add a title before saving.');
      return;
    }
    setSaveError(null);
    setSaving(true);
    try {
      await createRecipe(formToPayload(form));
      router.replace('/');
    } catch (err) {
      setSaveError(
        err instanceof ApiError ? err.message : 'Could not save the recipe.',
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.flex}
    >
      <ScrollView
        style={styles.screen}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <Pressable
          style={styles.importBar}
          onPress={() => setImportVisible(true)}
          accessibilityRole="button"
        >
          <View style={styles.importIcon}>
            <Text style={styles.importIconText}>⇩</Text>
          </View>
          <View style={styles.importTextWrap}>
            <Text style={styles.importTitle}>Import recipe</Text>
            <Text style={styles.importSubtitle}>
              Paste a link or recipe text to auto-fill
            </Text>
          </View>
        </Pressable>

        {lowConfidence ? (
          <Banner message="We couldn't fully parse this — please review before saving." />
        ) : null}
        {warnings.length > 0 ? (
          <Banner message={warnings.join('\n')} />
        ) : null}
        {saveError ? <Banner message={saveError} tone="error" /> : null}

        <Text style={styles.sectionTitle}>Details</Text>
        <TextField
          label="Title"
          placeholder="Recipe title"
          value={form.title}
          onChangeText={(v) => setField('title', v)}
        />
        <TextField
          label="Description"
          placeholder="Optional description"
          value={form.description}
          onChangeText={(v) => setField('description', v)}
          multiline
        />
        <View style={styles.numericRow}>
          <TextField
            label="Servings"
            placeholder="0"
            keyboardType="numeric"
            value={form.servings}
            onChangeText={(v) => setField('servings', v)}
            containerStyle={styles.numericField}
          />
          <TextField
            label="Prep (min)"
            placeholder="0"
            keyboardType="numeric"
            value={form.prepTime}
            onChangeText={(v) => setField('prepTime', v)}
            containerStyle={styles.numericField}
          />
          <TextField
            label="Cook (min)"
            placeholder="0"
            keyboardType="numeric"
            value={form.cookTime}
            onChangeText={(v) => setField('cookTime', v)}
            containerStyle={styles.numericFieldLast}
          />
        </View>

        <Text style={styles.sectionTitle}>Ingredients</Text>
        {form.ingredients.map((ing, index) => (
          <IngredientRow
            key={index}
            value={ing}
            flagged={ingredientNeedsReview(ing, unmappedUnits)}
            onChange={(next) => updateIngredient(index, next)}
            onRemove={() => removeIngredient(index)}
          />
        ))}
        <OutlineButton
          title="+ Add ingredient"
          onPress={addIngredient}
          style={styles.addBtn}
        />

        <Text style={styles.sectionTitle}>Instructions</Text>
        {form.instructions.map((step, index) => (
          <InstructionRow
            key={index}
            index={index}
            value={step}
            onChange={(next) => updateInstruction(index, next)}
            onRemove={() => removeInstruction(index)}
          />
        ))}
        <OutlineButton
          title="+ Add step"
          onPress={addInstruction}
          style={styles.addBtn}
        />

        <GradientButton
          title="Save Recipe"
          onPress={handleSave}
          disabled={!canSave}
          loading={saving}
          style={styles.saveBtn}
        />
      </ScrollView>

      <ImportSheet
        visible={importVisible}
        onClose={() => setImportVisible(false)}
        onParsed={handleParsed}
      />
      <LoadingOverlay visible={saving} message="Saving recipe…" />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
    backgroundColor: colors.background,
  },
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  importBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.gradientStart,
    borderRadius: 12,
    padding: spacing.lg,
    marginBottom: spacing.lg,
  },
  importIcon: {
    width: 40,
    height: 40,
    borderRadius: 999,
    backgroundColor: colors.gradientStart,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  importIconText: {
    color: colors.onGradient,
    fontSize: fontSizes.lg,
    fontWeight: '800',
  },
  importTextWrap: {
    flex: 1,
  },
  importTitle: {
    color: colors.text,
    fontSize: fontSizes.lg,
    fontWeight: '700',
  },
  importSubtitle: {
    color: colors.textMuted,
    fontSize: fontSizes.sm,
    marginTop: 2,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: fontSizes.lg,
    fontWeight: '700',
    marginTop: spacing.lg,
    marginBottom: spacing.md,
  },
  numericRow: {
    flexDirection: 'row',
  },
  numericField: {
    flex: 1,
    marginRight: spacing.sm,
  },
  numericFieldLast: {
    flex: 1,
  },
  addBtn: {
    marginTop: spacing.xs,
  },
  saveBtn: {
    marginTop: spacing.xl,
  },
});
