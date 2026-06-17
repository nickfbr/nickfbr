import { useRouter } from 'expo-router';
import { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Banner } from '@/components/Banner';
import { GradientButton, OutlineButton } from '@/components/GradientButton';
import { TextField } from '@/components/TextField';
import { ApiError, login, register } from '@/lib/api';
import { colors, fontSizes, spacing } from '@/theme';

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<'login' | 'register' | null>(null);

  const submit = async (mode: 'login' | 'register') => {
    if (email.trim() === '' || password === '') {
      setError('Enter your email and password.');
      return;
    }
    setError(null);
    setBusy(mode);
    try {
      if (mode === 'login') {
        await login(email.trim(), password);
      } else {
        await register(email.trim(), password);
      }
      router.replace('/');
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Something went wrong. Please try again.',
      );
    } finally {
      setBusy(null);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.header}>
            <Text style={styles.brand}>Recipe Box</Text>
            <Text style={styles.tagline}>Sign in to save and import recipes.</Text>
          </View>

          {error ? <Banner message={error} tone="error" /> : null}

          <TextField
            label="Email"
            placeholder="you@example.com"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="email-address"
            textContentType="emailAddress"
          />
          <TextField
            label="Password"
            placeholder="••••••••"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            textContentType="password"
          />

          <GradientButton
            title="Log in"
            onPress={() => submit('login')}
            loading={busy === 'login'}
            disabled={busy !== null}
            style={styles.primary}
          />
          <OutlineButton
            title="Create account"
            onPress={() => submit('register')}
            disabled={busy !== null}
            style={styles.secondary}
          />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.background,
  },
  flex: {
    flex: 1,
  },
  content: {
    padding: spacing.xl,
    flexGrow: 1,
    justifyContent: 'center',
  },
  header: {
    marginBottom: spacing.xxl,
    alignItems: 'center',
  },
  brand: {
    color: colors.gradientStart,
    fontSize: fontSizes.xxl,
    fontWeight: '800',
  },
  tagline: {
    color: colors.textMuted,
    fontSize: fontSizes.md,
    marginTop: spacing.sm,
  },
  primary: {
    marginTop: spacing.sm,
  },
  secondary: {
    marginTop: spacing.md,
  },
});
