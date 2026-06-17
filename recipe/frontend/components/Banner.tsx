import { StyleSheet, Text, View } from 'react-native';

import { colors, fontSizes, radii, spacing } from '@/theme';

type BannerTone = 'warning' | 'error';

interface BannerProps {
  message: string;
  tone?: BannerTone;
}

export function Banner({ message, tone = 'warning' }: BannerProps) {
  const accent = tone === 'error' ? colors.error : colors.amber;
  return (
    <View style={[styles.container, { borderColor: accent }]}>
      <View style={[styles.bar, { backgroundColor: accent }]} />
      <Text style={[styles.text, { color: accent }]}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderRadius: radii.md,
    paddingVertical: spacing.md,
    paddingRight: spacing.md,
    marginBottom: spacing.md,
    overflow: 'hidden',
  },
  bar: {
    width: 4,
    alignSelf: 'stretch',
    marginRight: spacing.md,
  },
  text: {
    flex: 1,
    fontSize: fontSizes.sm,
    fontWeight: '600',
  },
});
