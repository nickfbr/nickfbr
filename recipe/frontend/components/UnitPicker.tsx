import { useState } from 'react';
import {
  FlatList,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { UNITS, colors, fontSizes, radii, spacing, type Unit } from '@/theme';

interface UnitPickerProps {
  value: string;
  onChange: (unit: Unit) => void;
  flagged?: boolean;
}

export function UnitPicker({ value, onChange, flagged = false }: UnitPickerProps) {
  const [open, setOpen] = useState(false);
  const borderColor = flagged ? colors.amber : colors.border;

  return (
    <>
      <Pressable
        onPress={() => setOpen(true)}
        accessibilityRole="button"
        style={[styles.trigger, { borderColor }]}
      >
        <Text style={[styles.triggerText, !value && styles.placeholder]}>
          {value || 'unit'}
        </Text>
        <Text style={styles.caret}>▾</Text>
      </Pressable>

      <Modal visible={open} transparent animationType="fade">
        <Pressable style={styles.backdrop} onPress={() => setOpen(false)}>
          <View style={styles.sheet}>
            <Text style={styles.sheetTitle}>Unit</Text>
            <FlatList
              data={UNITS}
              keyExtractor={(item) => item}
              renderItem={({ item }) => {
                const selected = item === value;
                return (
                  <Pressable
                    onPress={() => {
                      onChange(item);
                      setOpen(false);
                    }}
                    style={[styles.option, selected && styles.optionSelected]}
                  >
                    <Text
                      style={[
                        styles.optionText,
                        selected && styles.optionTextSelected,
                      ]}
                    >
                      {item}
                    </Text>
                  </Pressable>
                );
              }}
            />
          </View>
        </Pressable>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  trigger: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderRadius: radii.md,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.md,
    minHeight: 48,
  },
  triggerText: {
    color: colors.text,
    fontSize: fontSizes.md,
  },
  placeholder: {
    color: colors.textMuted,
  },
  caret: {
    color: colors.textMuted,
    fontSize: fontSizes.sm,
    marginLeft: spacing.xs,
  },
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    paddingHorizontal: spacing.xl,
  },
  sheet: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    paddingVertical: spacing.md,
    maxHeight: '60%',
  },
  sheetTitle: {
    color: colors.textMuted,
    fontSize: fontSizes.sm,
    fontWeight: '700',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
    textTransform: 'uppercase',
  },
  option: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
  },
  optionSelected: {
    backgroundColor: colors.surfaceAlt,
  },
  optionText: {
    color: colors.text,
    fontSize: fontSizes.md,
  },
  optionTextSelected: {
    color: colors.gradientStart,
    fontWeight: '700',
  },
});
