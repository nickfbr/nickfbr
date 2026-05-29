# Recipe Box — Frontend

A React Native (Expo SDK 51, expo-router, TypeScript) app for saving and
importing recipes. Dark theme with a gold gradient primary action. The
centerpiece is the **Import recipe** (paste-to-parse) flow on the Add Recipe
screen.

## Requirements

- Node 18+ (tested on Node 22)
- npm
- The Expo Go app on a device, or an Android/iOS simulator, for previewing

## Install

```bash
cd frontend
npm install
```

## Run

```bash
npx expo start
```

Then press `a` (Android), `i` (iOS), or `w` (web), or scan the QR code with
Expo Go.

Useful scripts:

| Script            | What it does                |
| ----------------- | --------------------------- |
| `npm start`       | Start the Expo dev server   |
| `npm run android` | Start + open Android        |
| `npm run ios`     | Start + open iOS            |
| `npm run web`     | Start + open web            |
| `npm run tsc`     | Type-check (`tsc --noEmit`) |

## Point at the backend

The API base URL comes from `EXPO_PUBLIC_API_URL` (default
`http://localhost:8000`). Copy the example env file and edit as needed:

```bash
cp .env.example .env
# .env
# EXPO_PUBLIC_API_URL=http://localhost:8000
```

When running on a physical device, `localhost` refers to the phone, not your
machine — use your computer's LAN IP, e.g.
`EXPO_PUBLIC_API_URL=http://192.168.1.20:8000`.

## Project layout

```
frontend/
├── app/                     # expo-router routes
│   ├── _layout.tsx          # Stack nav, dark theme, auth gate
│   ├── login.tsx            # email/password login + register
│   ├── index.tsx            # recipe list + FAB to add
│   └── recipe/
│       ├── [id].tsx         # recipe detail
│       └── add.tsx          # Add Recipe form + Import (paste-to-parse)
├── components/              # GradientButton, TextField, IngredientRow, …
├── lib/                     # api client, types, form model, storage
└── theme.ts                 # colors, spacing, radii, unit enum
```

## Auth

A JWT is stored with `expo-secure-store` on native (falling back to
AsyncStorage on web). The root layout redirects to `/login` when no token is
present and attaches `Authorization: Bearer <token>` to recipe requests.
