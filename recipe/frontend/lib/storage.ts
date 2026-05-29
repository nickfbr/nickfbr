/**
 * Token persistence. Prefers expo-secure-store on native; falls back to
 * AsyncStorage (e.g. web, or if SecureStore is unavailable).
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const TOKEN_KEY = 'auth_token';

const canUseSecureStore = Platform.OS !== 'web';

export async function saveToken(token: string): Promise<void> {
  if (canUseSecureStore) {
    try {
      await SecureStore.setItemAsync(TOKEN_KEY, token);
      return;
    } catch {
      // fall through to AsyncStorage
    }
  }
  await AsyncStorage.setItem(TOKEN_KEY, token);
}

export async function loadToken(): Promise<string | null> {
  if (canUseSecureStore) {
    try {
      const value = await SecureStore.getItemAsync(TOKEN_KEY);
      if (value !== null) {
        return value;
      }
    } catch {
      // fall through to AsyncStorage
    }
  }
  return AsyncStorage.getItem(TOKEN_KEY);
}

export async function clearToken(): Promise<void> {
  if (canUseSecureStore) {
    try {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
    } catch {
      // ignore
    }
  }
  await AsyncStorage.removeItem(TOKEN_KEY);
}
