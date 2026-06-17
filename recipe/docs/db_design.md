# Database Design — Recipe Box

PostgreSQL in production; SQLite for local dev/tests. Schema is managed with
Alembic (`backend/alembic/versions/`). SQLAlchemy 2.0 models live in
`backend/app/models.py`.

## Tables

### users
| column          | type           | notes                          |
|-----------------|----------------|--------------------------------|
| id              | int PK         |                                |
| email           | varchar(320)   | unique, indexed                |
| hashed_password | varchar(255)   | pbkdf2_sha256 (passlib)        |
| created_at      | timestamptz    | server default now()           |

### recipes
| column      | type          | notes                                   |
|-------------|---------------|-----------------------------------------|
| id          | int PK        |                                         |
| owner_id    | int FK→users  | indexed, ON DELETE CASCADE              |
| title       | varchar(300)  | required                                |
| description | text          | nullable                                |
| servings    | int           | nullable, clamped 1–100 on parse        |
| prep_time   | int           | nullable, minutes                       |
| cook_time   | int           | nullable, minutes                       |
| source_url  | varchar(2048) | nullable — carries imported source URL  |
| created_at  | timestamptz   | server default now()                    |

> **`source_url`** was added (spec §10 follow-up) so a draft's `sourceUrl`
> round-trips through `POST /api/recipes`. Photo/image import remains out of scope.

### ingredients
| column    | type         | notes                              |
|-----------|--------------|------------------------------------|
| id        | int PK       |                                    |
| recipe_id | int FK       | indexed, ON DELETE CASCADE         |
| name      | varchar(300) | required                           |
| quantity  | float        | nullable                           |
| unit      | varchar(16)  | one of the canonical units (below) |
| raw       | text         | nullable — original ingredient line|

### instructions
| column      | type | notes                       |
|-------------|------|-----------------------------|
| id          | int PK |                           |
| recipe_id   | int FK | indexed, ON DELETE CASCADE|
| step_number | int    | 1..N, re-sequenced        |
| text        | text   | required                  |

## Canonical unit enum

Single source of truth: `backend/app/units.py` (`UNITS`). The API schema, parser,
and the frontend dropdown all derive from this list.

```
cups, tbsp, tsp, g, oz, ml, L, kg, whole, pinch, lb, fl_oz
```

**Decision (spec §6):** the enum was extended with **`lb`** and **`fl_oz`** because
US recipes rely on them heavily. Anything the parser cannot map to this list is
coerced to `whole` and surfaced in `meta.unmappedUnits` so the user can correct it
in the Add Recipe form.

## Migrations

```bash
cd backend
alembic upgrade head          # apply
alembic revision -m "msg"     # new migration (autogenerate after model edits)
```
