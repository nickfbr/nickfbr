"""Endpoint tests for POST /api/recipes/parse and the parse -> save integration.

External effects are mocked: httpx via respx, the scraper and LLM via monkeypatch.
"""

import httpx
import pytest
import respx

from app.parsing import service

# A literal public IP avoids real DNS resolution under respx.
PUBLIC_URL = "http://93.184.216.34/recipe"

LLM_RECIPE = {
    "title": "Brown Butter Caramels",
    "description": "Soft, salted caramels.",
    "ingredients": [
        {"name": "butter", "quantity": 1.0, "unit": "cups", "raw": "1 cup butter"},
        {"name": "brown sugar", "quantity": 2.25, "unit": "cups", "raw": "2 1/4 cups brown sugar"},
        {"name": "salt", "quantity": 0.125, "unit": "tsp", "raw": "1/8 tsp salt"},
    ],
    "instructions": [
        {"stepNumber": 1, "text": "Melt the butter."},
        {"stepNumber": 2, "text": "Add sugar and boil to 237F."},
    ],
    "servings": 24,
    "prepTime": 10,
    "cookTime": 30,
}


def test_requires_exactly_one_of_text_or_url(auth_client):
    # neither
    r = auth_client.post("/api/recipes/parse", json={})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_INPUT"
    # both
    r = auth_client.post("/api/recipes/parse", json={"text": "x", "url": "http://x.com"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_INPUT"


def test_requires_auth(client):
    r = client.post("/api/recipes/parse", json={"text": "hi"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_text_too_long(auth_client):
    r = auth_client.post("/api/recipes/parse", json={"text": "a" * 20001})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_INPUT"


def test_bad_url_syntax(auth_client):
    r = auth_client.post("/api/recipes/parse", json={"url": "not-a-url"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_INPUT"


def test_text_parse_via_llm(auth_client, monkeypatch):
    monkeypatch.setattr(service, "parse_with_llm", lambda text: dict(LLM_RECIPE))
    r = auth_client.post("/api/recipes/parse", json={"text": "some recipe text"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["parseMethod"] == "llm"
    assert body["meta"]["confidence"] == "high"
    assert body["draft"]["title"] == "Brown Butter Caramels"
    assert len(body["draft"]["ingredients"]) == 3
    # steps are re-sequenced 1..N
    assert [s["stepNumber"] for s in body["draft"]["instructions"]] == [1, 2]


def test_unparseable_text(auth_client, monkeypatch):
    monkeypatch.setattr(
        service, "parse_with_llm", lambda text: {"title": None, "ingredients": [], "instructions": []}
    )
    r = auth_client.post("/api/recipes/parse", json={"text": "lorem ipsum"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "UNPARSEABLE"


def test_unmapped_units_flagged(auth_client, monkeypatch):
    data = {
        "title": "Garlic Thing",
        "ingredients": [
            {"name": "garlic", "quantity": 2, "unit": "clove", "raw": "2 cloves garlic"},
            {"name": "flour", "quantity": 1, "unit": "cups", "raw": "1 cup flour"},
        ],
        "instructions": [{"stepNumber": 1, "text": "Mix."}],
    }
    monkeypatch.setattr(service, "parse_with_llm", lambda text: data)
    r = auth_client.post("/api/recipes/parse", json={"text": "x"})
    assert r.status_code == 200
    body = r.json()
    assert "clove" in body["meta"]["unmappedUnits"]
    # the offending ingredient's unit was coerced to whole
    units = {i["name"]: i["unit"] for i in body["draft"]["ingredients"]}
    assert units["garlic"] == "whole"


@respx.mock
def test_url_structured_data(auth_client, monkeypatch):
    respx.get(PUBLIC_URL).mock(
        return_value=httpx.Response(200, html="<html>recipe</html>")
    )
    monkeypatch.setattr(
        service,
        "scrape",
        lambda html, url: {
            "title": "Pancakes",
            "ingredients": ["2 cups flour", "1 can condensed milk"],
            "instructions": ["Mix.", "Cook."],
            "servings": 4,
            "total_time": 20,
            "prep_time": None,
            "cook_time": None,
        },
    )
    r = auth_client.post("/api/recipes/parse", json={"url": PUBLIC_URL})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["parseMethod"] == "structured_data"
    assert body["draft"]["sourceUrl"] == PUBLIC_URL
    assert body["draft"]["servings"] == 4
    assert "can" in body["meta"]["unmappedUnits"]


@respx.mock
def test_url_redirect_to_internal_blocked(auth_client):
    respx.get(PUBLIC_URL).mock(
        return_value=httpx.Response(302, headers={"location": "http://169.254.169.254/"})
    )
    r = auth_client.post("/api/recipes/parse", json={"url": PUBLIC_URL})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "URL_NOT_ALLOWED"


@respx.mock
def test_url_non_html_fails(auth_client):
    respx.get(PUBLIC_URL).mock(
        return_value=httpx.Response(200, json={"not": "html"})
    )
    r = auth_client.post("/api/recipes/parse", json={"url": PUBLIC_URL})
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "FETCH_FAILED"


def test_url_to_internal_address_blocked(auth_client):
    r = auth_client.post("/api/recipes/parse", json={"url": "http://169.254.169.254/"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "URL_NOT_ALLOWED"


def test_parse_then_save_integration(auth_client, monkeypatch):
    """The draft from /parse must be accepted by POST /api/recipes unchanged."""
    monkeypatch.setattr(service, "parse_with_llm", lambda text: dict(LLM_RECIPE))
    parsed = auth_client.post("/api/recipes/parse", json={"text": "recipe"}).json()
    draft = parsed["draft"]

    # Build the canonical create body straight from the draft (same camelCase shape).
    create_body = {
        "title": draft["title"],
        "description": draft["description"],
        "servings": draft["servings"],
        "prepTime": draft["prepTime"],
        "cookTime": draft["cookTime"],
        "sourceUrl": draft["sourceUrl"],
        "ingredients": draft["ingredients"],
        "instructions": draft["instructions"],
    }
    created = auth_client.post("/api/recipes", json=create_body)
    assert created.status_code == 201, created.text
    saved = created.json()
    assert saved["id"] > 0
    assert saved["title"] == "Brown Butter Caramels"
    assert len(saved["ingredients"]) == 3
    assert [s["stepNumber"] for s in saved["instructions"]] == [1, 2]
