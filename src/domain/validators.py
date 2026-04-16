from urllib.parse import urlparse


def validate_http_https_url(url: str, field_name: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"{field_name} must use http or https scheme")


def validate_context_urls(context: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(context, dict):
        return errors

    for key, value in context.items():
        if isinstance(value, str) and value.startswith(("http://", "https://", "ftp://", "file://")):
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"}:
                errors.append(f"context field '{key}' uses unsupported URL scheme '{parsed.scheme}'")
    return errors
