import { Pressable, StyleSheet, Text, View } from 'react-native';

import { TextField } from '@/components/TextField';
import { UnitPicker } from '@/components/UnitPicker';
import type { IngredientRowData } from '@/lib/form';
import { colors, fontSizes, radii, spacing, type Unit } from '@/theme';

interface IngredientRowProps {
  value: IngredientRowData;
  flagged?: boolean;
  onChange: (next: IngredientRowData) => void;
  onRemove: () => void;
}

export function IngredientRow({
  value,
  flagged = false,
  onChange,
  onRemove,
}: IngredientRowProps) {
  return (
    <View style={[styles.container, flagged && styles.flagged]}>
      <View style={styles.topRow}>
        <View style={styles.nameField}>
          <TextField
            placeholder="Ingredient"
            value={value.name}
            onChangeText={(name) => onChange({ ...value, name })}
            containerStyle={styles.noMargin}
          />
        </View>
        <Pressable
          onPress={onRemove}
          accessibilityRole="button"
          accessibilityLabel="Remove ingredient"
          style={styles.removeBtn}
        >
          <Text style={styles.removeText}>✕</Text>
        </Pressable>
      </View>

      <View style={styles.metaRow}>
        <View style={styles.qtyField}>
          <TextField
            placeholder="Qty"
            keyboardType="numeric"
            value={value.quantity}
            onChangeText={(quantity) => onChange({ ...value, quantity })}
            containerStyle={styles.noMargin}
            flagged={flagged && value.quantity.trim() === ''}
          />
        </View>
        <View style={styles.unitField}>
          <UnitPicker
            value={value.unit}
            onChange={(unit: Unit) => onChange({ ...value, unit })}
            flagged={flagged}
          />
        </View>
      </View>

      {value.raw ? (
        <Text style={styles.raw} numberOfLines={2}>
          From: {value.raw}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surfaceAlt,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  flagged: {
    borderColor: colors.amber,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  nameField: {
    flex: 1,
  },
  noMargin: {
    marginBottom: 0,
  },
  removeBtn: {
    marginLeft: spacing.sm,
    width: 36,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
  },
  removeText: {
    color: colors.textMuted,
    fontSize: fontSizes.lg,
  },
  metaRow: {
    flexDirection: 'row',
    marginTop: spacing.sm,
  },
  qtyField: {
    width: 96,
    marginRight: spacing.sm,
  },
  unitField: {
    flex: 1,
  },
  raw: {
    color: colors.textMuted,
    fontSize: fontSizes.sm,
    marginTop: spacing.sm,
    fontStyle: 'italic',
  },
});
