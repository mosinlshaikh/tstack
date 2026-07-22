import base64

import pytest

from tstack.secure_cli import _public_key, build_parser


def test_public_key_accepts_raw_and_base64(tmp_path) -> None:
    raw = bytes(range(32))
    raw_path = tmp_path / "public.raw"
    raw_path.write_bytes(raw)
    assert _public_key(raw_path) == raw

    encoded_path = tmp_path / "public.b64"
    encoded_path.write_bytes(base64.b64encode(raw))
    assert _public_key(encoded_path) == raw


def test_public_key_rejects_invalid_length(tmp_path) -> None:
    path = tmp_path / "bad.key"
    path.write_text(base64.b64encode(b"too-short").decode("ascii"), encoding="utf-8")
    with pytest.raises(ValueError, match="32 bytes"):
        _public_key(path)


def test_secure_cli_requires_subcommand() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
