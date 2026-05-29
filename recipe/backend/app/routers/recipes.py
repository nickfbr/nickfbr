from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.errors import AppError
from app.models import Ingredient, Instruction, Recipe, User
from app.parsing.service import parse as parse_recipe
from app.rate_limit import parse_rate_limiter
from app.schemas import ParseRequest, ParseResponse, RecipeCreate, RecipeOut

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("", response_model=list[RecipeOut])
def list_recipes(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[Recipe]:
    return list(
        db.scalars(
            select(Recipe).where(Recipe.owner_id == user.id).order_by(Recipe.created_at.desc())
        )
    )


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(
    recipe_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Recipe:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None or recipe.owner_id != user.id:
        raise AppError("NOT_FOUND", "Recipe not found.", status_code=404)
    return recipe


@router.post("", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
def create_recipe(
    payload: RecipeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Recipe:
    recipe = Recipe(
        owner_id=user.id,
        title=payload.title,
        description=payload.description,
        servings=payload.servings,
        prep_time=payload.prep_time,
        cook_time=payload.cook_time,
        source_url=payload.source_url,
        ingredients=[
            Ingredient(name=i.name, quantity=i.quantity, unit=i.unit, raw=i.raw)
            for i in payload.ingredients
        ],
        instructions=[
            Instruction(step_number=idx + 1, text=s.text)
            for idx, s in enumerate(payload.instructions)
        ],
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@router.post("/parse", response_model=ParseResponse)
def parse_recipe_endpoint(
    payload: ParseRequest, user: User = Depends(get_current_user)
) -> ParseResponse:
    # Stateless: never writes to the DB. Rate-limited per user (§6).
    parse_rate_limiter.check(f"user:{user.id}")
    return parse_recipe(payload)
