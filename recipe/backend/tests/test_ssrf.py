import pytest

from app.errors import AppError
from app.parsing.ssrf import assert_safe_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/recipe",
        "http://localhost/recipe",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata
        "http://10.0.0.5/x",
        "http://192.168.1.10/x",
        "http://172.16.5.4/x",
        "http://[::1]/x",
        "http://0.0.0.0/x",
    ],
)
def test_blocks_internal_addresses(url):
    with pytest.raises(AppError) as exc:
        assert_safe_url(url)
    assert exc.value.code == "URL_NOT_ALLOWED"
    assert exc.value.status_code == 400


@pytest.mark.parametrize("url", ["ftp://example.com/x", "file:///etc/passwd", "gopher://x/"])
def test_blocks_non_http_schemes(url):
    with pytest.raises(AppError) as exc:
        assert_safe_url(url)
    assert exc.value.code == "URL_NOT_ALLOWED"


def test_allows_public_literal_ip():
    # A public literal IP passes (no DNS needed).
    assert assert_safe_url("http://93.184.216.34/recipe") == "93.184.216.34"
