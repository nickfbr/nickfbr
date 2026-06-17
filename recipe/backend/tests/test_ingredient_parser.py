import pytest

from app.parsing.ingredient_parser import parse_ingredient_line


def test_simple_quantity_unit_name():
    p = parse_ingredient_line("2 cups all-purpose flour, sifted")
    assert p.quantity == 2.0
    assert p.unit == "cups"
    assert p.name == "all-purpose flour, sifted"
    assert p.raw == "2 cups all-purpose flour, sifted"
    assert p.unmapped_unit is None


def test_mixed_number():
    p = parse_ingredient_line("1 1/2 cups sugar")
    assert p.quantity == 1.5
    assert p.unit == "cups"
    assert p.name == "sugar"


@pytest.mark.parametrize(
    "line,qty",
    [
        ("½ cup milk", 0.5),
        ("¾ tsp salt", 0.75),
        ("1½ cups water", 1.5),
        ("⅓ cup oil", pytest.approx(1 / 3)),
    ],
)
def test_unicode_fractions(line, qty):
    p = parse_ingredient_line(line)
    assert p.quantity == qty


def test_range_takes_lower_bound():
    p = parse_ingredient_line("2-3 cloves garlic, minced")
    assert p.quantity == 2.0
    # "cloves" is a known measure word not in the enum -> flagged.
    assert p.unit == "whole"
    assert p.unmapped_unit == "cloves"
    assert p.name == "garlic, minced"
    # The original range is preserved in raw.
    assert p.raw == "2-3 cloves garlic, minced"


def test_range_with_to_keyword():
    p = parse_ingredient_line("2 to 4 tablespoons butter")
    assert p.quantity == 2.0
    assert p.unit == "tbsp"
    assert p.name == "butter"


def test_unit_synonyms():
    assert parse_ingredient_line("3 tbsp olive oil").unit == "tbsp"
    assert parse_ingredient_line("1 tablespoon honey").unit == "tbsp"
    assert parse_ingredient_line("250 g flour").unit == "g"
    assert parse_ingredient_line("1 lb ground beef").unit == "lb"  # extended enum
    assert parse_ingredient_line("8 fl oz milk").unit == "fl_oz"


def test_case_sensitive_T_vs_t():
    assert parse_ingredient_line("1 T butter").unit == "tbsp"
    assert parse_ingredient_line("1 t vanilla").unit == "tsp"


def test_count_noun_is_not_a_unit():
    p = parse_ingredient_line("2 eggs")
    assert p.quantity == 2.0
    assert p.unit == "whole"
    assert p.name == "eggs"
    assert p.unmapped_unit is None


def test_unmapped_measure_word_flagged():
    p = parse_ingredient_line("1 can sweetened condensed milk")
    assert p.unit == "whole"
    assert p.unmapped_unit == "can"
    assert p.name == "sweetened condensed milk"


def test_no_quantity():
    p = parse_ingredient_line("Salt to taste")
    assert p.quantity is None
    assert p.unit == "whole"
    assert p.name == "Salt to taste"


def test_empty_line():
    p = parse_ingredient_line("")
    assert p.quantity is None
    assert p.name == ""
