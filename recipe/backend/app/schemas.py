from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

from app.config import get_settings
from app.units import UNIT_SET


class CamelModel(BaseModel):
    """Base model that serializes to camelCase but also accepts snake_case."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
class UserCreate(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(CamelModel):
    id: int
    email: EmailStr


class Token(CamelModel):
    access_token: str
    token_type: str = "bearer"


# --------------------------------------------------------------------------- #
# Recipe (canonical) — used by POST /api/recipes
# --------------------------------------------------------------------------- #
class IngredientIn(CamelModel):
    name: str = Field(min_length=1, max_length=300)
    quantity: Optional[float] = None
    unit: str
    raw: Optional[str] = None

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        if v not in UNIT_SET:
            raise ValueError(f"unit must be one of {sorted(UNIT_SET)}")
        return v


class InstructionIn(CamelModel):
    step_number: int = Field(ge=1)
    text: str = Field(min_length=1)


class RecipeCreate(CamelModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    servings: Optional[int] = Field(default=None, ge=1, le=100)
    prep_time: Optional[int] = Field(default=None, ge=0, le=6000)
    cook_time: Optional[int] = Field(default=None, ge=0, le=6000)
    source_url: Optional[str] = Field(default=None, max_length=2048)
    ingredients: list[IngredientIn] = Field(default_factory=list)
    instructions: list[InstructionIn] = Field(default_factory=list)


class IngredientOut(CamelModel):
    name: str
    quantity: Optional[float] = None
    unit: str
    raw: Optional[str] = None


class InstructionOut(CamelModel):
    step_number: int
    text: str


class RecipeOut(CamelModel):
    id: int
    title: str
    description: Optional[str] = None
    servings: Optional[int] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    source_url: Optional[str] = None
    ingredients: list[IngredientOut] = Field(default_factory=list)
    instructions: list[InstructionOut] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Parse (draft) — used by POST /api/recipes/parse
# --------------------------------------------------------------------------- #
class ParseRequest(CamelModel):
    text: Optional[str] = None
    url: Optional[str] = None

    @field_validator("text")
    @classmethod
    def text_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > get_settings().max_text_length:
            raise ValueError(
                f"text exceeds maximum length of {get_settings().max_text_length} characters"
            )
        return v

    @field_validator("url")
    @classmethod
    def url_syntax(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("url must be a valid http(s) URL")
        return v

    @model_validator(mode="after")
    def exactly_one(self) -> "ParseRequest":
        has_text = bool(self.text and self.text.strip())
        has_url = bool(self.url and self.url.strip())
        if has_text == has_url:
            raise ValueError("exactly one of 'text' or 'url' must be provided")
        return self


class ParsedIngredient(CamelModel):
    name: str
    quantity: Optional[float] = None
    unit: str
    raw: str

    @field_validator("unit")
    @classmethod
    def coerce_unit(cls, v: str) -> str:
        # Loose by design: coerce anything unknown to the fallback unit.
        return v if v in UNIT_SET else "whole"


class ParsedInstruction(CamelModel):
    step_number: int
    text: str


class ParsedRecipeDraft(CamelModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: list[ParsedIngredient] = Field(default_factory=list)
    instructions: list[ParsedInstruction] = Field(default_factory=list)
    servings: Optional[int] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    source_url: Optional[str] = None


ParseMethod = Literal["structured_data", "llm", "llm_fallback"]
Confidence = Literal["high", "medium", "low"]


class ParseMeta(CamelModel):
    parse_method: ParseMethod
    confidence: Confidence
    warnings: list[str] = Field(default_factory=list)
    unmapped_units: list[str] = Field(default_factory=list)


class ParseResponse(CamelModel):
    draft: ParsedRecipeDraft
    meta: ParseMeta


# --------------------------------------------------------------------------- #
# Standardized error envelope (app-wide)
# --------------------------------------------------------------------------- #
class ErrorBody(BaseModel):
    code: str
    message: str
    fields: Optional[dict[str, str]] = None


class ErrorResponse(BaseModel):
    error: ErrorBody
