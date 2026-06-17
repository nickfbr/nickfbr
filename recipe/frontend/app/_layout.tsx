import {
  DarkTheme,
  ThemeProvider,
  type Theme,
} from '@react-navigation/native';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { getToken, initAuth } from '@/lib/api';
import { colors } from '@/theme';

const navTheme: Theme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    background: colors.background,
    card: colors.surface,
    text: colors.text,
    border: colors.border,
    primary: colors.gradientStart,
  },
};

export default function RootLayout() {
  const [ready, setReady] = useState(false);
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    let mounted = true;
    initAuth().finally(() => {
      if (mounted) {
        setReady(true);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  // Auth gate: redirect to /login when there is no token, away from /login
  // once authenticated. Re-checks the live token on each navigation.
  useEffect(() => {
    if (!ready) {
      return;
    }
    const hasToken = getToken() !== null;
    const onLogin = segments[0] === 'login';
    if (!hasToken && !onLogin) {
      router.replace('/login');
    } else if (hasToken && onLogin) {
      router.replace('/');
    }
  }, [ready, segments, router]);

  if (!ready) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={colors.gradientStart} />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <ThemeProvider value={navTheme}>
        <StatusBar style="light" />
        <Stack
          screenOptions={{
            headerStyle: { backgroundColor: colors.surface },
            headerTintColor: colors.text,
            headerTitleStyle: { color: colors.text },
            contentStyle: { backgroundColor: colors.background },
          }}
        >
          <Stack.Screen name="login" options={{ headerShown: false }} />
          <Stack.Screen name="index" options={{ title: 'Recipe Box' }} />
          <Stack.Screen
            name="recipe/add"
            options={{ title: 'Add Recipe', presentation: 'modal' }}
          />
          <Stack.Screen name="recipe/[id]" options={{ title: 'Recipe' }} />
        </Stack>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
});
