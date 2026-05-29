# UX Design — Recipe Box (mobile, expo-router)

Dark theme with a gold gradient as the primary accent. React Native + expo-router
+ TypeScript. Source in `frontend/`.

## Visual language
- Background `#121212`, surface `#1E1E1E`, primary text `#F5F5F5`, muted `#A0A0A0`.
- Primary button: gold gradient `['#F5C242', '#E0992E']`, dark text, 12px radius
  (`components/GradientButton.tsx`, via `expo-linear-gradient`).
- Warning/review accent: amber `#F0A500`. Error: `#FF6B6B`.
- Tokens centralized in `frontend/theme.ts`.

## Screens (`frontend/app/`)
- `login.tsx` — email + password; Login and Create account. Stores JWT.
- `index.tsx` — recipe list: cards with title, servings, prep/cook times.
  Pull-to-refresh, FAB → Add Recipe, logout.
- `recipe/[id].tsx` — detail: title, description, meta, ingredients, numbered steps.
- `recipe/add.tsx` — **Add Recipe + Import** (the key screen, below).

## Add Recipe + Import flow (spec §7)

1. **Import affordance** at the top opens a sheet (`ImportSheet`) with a multiline
   paste field ("Paste link or text") and a gold **Parse** button.
2. **Detect mode**: input starting with `http` → sent as `url`, otherwise `text`.
   → `POST /api/recipes/parse`. A loading overlay covers the call (a few seconds,
   especially the LLM path).
3. **Review state**: on success the form is pre-filled from `draft`.
   - Ingredient rows whose `unit` is in `meta.unmappedUnits` **or** whose `quantity`
     is null get an **amber accent border**.
   - `meta.confidence === "low"` → non-blocking amber banner: *"We couldn't fully
     parse this — please review before saving."* Parser `warnings` also surface.
   - The original line (`ingredients[].raw`) shows as helper text under each row.
4. **Save** is separate: the existing **Save Recipe** button calls
   `POST /api/recipes`. Parsing never auto-saves.

### §8 — Unit dropdown
The ingredient unit picker (`components/UnitPicker.tsx`) lists exactly the 12
canonical units, including the extended `lb` and `fl_oz`:

```
cups · tbsp · tsp · g · oz · ml · L · kg · whole · pinch · lb · fl_oz
```

## Error → message mapping (`lib/parseErrors.ts`)
| code                | message                                                                   |
|---------------------|---------------------------------------------------------------------------|
| `UNPARSEABLE` / `FETCH_FAILED` | "We couldn't read a recipe from that. Try pasting the recipe text directly." |
| `URL_NOT_ALLOWED`   | "That link can't be imported."                                            |
| `PARSER_UNAVAILABLE`| "Import is temporarily unavailable, please try again."                    |
| `INVALID_INPUT`     | "Please paste some recipe text or a link."                                |
| (default)           | the server's `error.message`                                              |
