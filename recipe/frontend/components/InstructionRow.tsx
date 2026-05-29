import { Pressable, StyleSheet, Text, View } from 'react-native';

import { TextField } from '@/components/TextField';
import type { InstructionRowData } from '@/lib/form';
import { colors, fontSizes, radii, spacing } from '@/theme';

interface InstructionRowProps {
  index: number;
  value: InstructionRowData;
  onChange: (next: InstructionRowData) => void;
  onRemove: () => void;
}

export function InstructionRow({
  index,
  value,
  onChange,
  onRemove,
}: InstructionRowProps) {
  return (
    <View style={styles.container}>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>{index + 1}</Text>
      </View>
      <View style={styles.field}>
        <TextField
          placeholder={`Step ${index + 1}`}
          multiline
          value={value.text}
          onChangeText={(text) => onChange({ text })}
          containerStyle={styles.noMargin}
        />
      </View>
      <Pressable
        onPress={onRemove}
        accessibilityRole="button"
        accessibilityLabel="Remove step"
        style={styles.removeBtn}
      >
        <Text style={styles.removeText}>✕</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  badge: {
    width: 28,
    height: 28,
    borderRadius: radii.pill,
    backgroundColor: colors.gradientEnd,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.sm,
    marginRight: spacing.sm,
  },
  badgeText: {
    color: colors.onGradient,
    fontWeight: '700',
    fontSize: fontSizes.sm,
  },
  field: {
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
});
