import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Banner } from '@/components/Banner';
import { GradientButton } from '@/components/GradientButton';
import { TextField } from '@/components/TextField';
import { parseRecipe } from '@/lib/api';
import { friendlyParseError } from '@/lib/parseErrors';
import type { ParseResponse } from '@/lib/types';
import { colors, fontSizes, radii, spacing } from '@/theme';

interface ImportSheetProps {
  visible: boolean;
  onClose: () => void;
  onParsed: (result: ParseResponse) => void;
}

export function ImportSheet({ visible, onClose, onParsed }: ImportSheetProps) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setInput('');
    setError(null);
    setLoading(false);
  };

  const handleClose = () => {
    if (loading) {
      return;
    }
    reset();
    onClose();
  };

  const handleParse = async () => {
    const trimmed = input.trim();
    if (trimmed === '') {
      setError('Please paste some recipe text or a link.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const payload = trimmed.toLowerCase().startsWith('http')
        ? { url: trimmed }
        : { text: trimmed };
      const result = await parseRecipe(payload);
      reset();
      onParsed(result);
    } catch (err) {
      setError(friendlyParseError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={handleClose}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <Pressable style={styles.backdrop} onPress={handleClose} />
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <Text style={styles.title}>Import recipe</Text>
          <Text style={styles.subtitle}>
            Paste a recipe link or the full recipe text and we&apos;ll fill in
            the form for you.
          </Text>

          {error ? <Banner message={error} tone="error" /> : null}

          <TextField
            placeholder="Paste link or text"
            value={input}
            onChangeText={setInput}
            multiline
            autoFocus
            editable={!loading}
            containerStyle={styles.field}
          />

          {loading ? (
            <View style={styles.loadingBox}>
              <ActivityIndicator color={colors.gradientStart} />
              <Text style={styles.loadingText}>
                Reading the recipe… this can take a few seconds.
              </Text>
            </View>
          ) : (
            <GradientButton title="Parse" onPress={handleParse} />
          )}

          <Pressable
            onPress={handleClose}
            disabled={loading}
            style={styles.cancel}
          >
            <Text style={styles.cancelText}>Cancel</Text>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
  },
  sheet: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radii.xl,
    borderTopRightRadius: radii.xl,
    padding: spacing.xl,
    paddingBottom: spacing.xxl,
  },
  handle: {
    alignSelf: 'center',
    width: 40,
    height: 4,
    borderRadius: radii.pill,
    backgroundColor: colors.border,
    marginBottom: spacing.lg,
  },
  title: {
    color: colors.text,
    fontSize: fontSizes.xl,
    fontWeight: '700',
    marginBottom: spacing.xs,
  },
  subtitle: {
    color: colors.textMuted,
    fontSize: fontSizes.sm,
    marginBottom: spacing.lg,
  },
  field: {
    marginBottom: spacing.lg,
  },
  loadingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.md,
  },
  loadingText: {
    color: colors.textMuted,
    fontSize: fontSizes.sm,
    marginLeft: spacing.md,
    flexShrink: 1,
  },
  cancel: {
    alignItems: 'center',
    paddingVertical: spacing.md,
    marginTop: spacing.sm,
  },
  cancelText: {
    color: colors.textMuted,
    fontSize: fontSizes.md,
  },
});
