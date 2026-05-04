"""Tests for engine numeric coercion helpers (yt-dlp JSON edge cases)."""

from __future__ import annotations

import math

from jre_vidget.engine import _coerce_float, _coerce_int


def test_coerce_int_accepts_int_and_finite_float() -> None:
    assert _coerce_int(42) == 42
    assert _coerce_int(3.9) == 3


def test_coerce_int_rejects_bool_string_none() -> None:
    assert _coerce_int(True) is None
    assert _coerce_int(False) is None
    assert _coerce_int("12") is None
    assert _coerce_int(None) is None


def test_coerce_int_rejects_non_finite_float() -> None:
    assert _coerce_int(float("nan")) is None
    assert _coerce_int(float("inf")) is None
    assert _coerce_int(-float("inf")) is None


def test_coerce_float_accepts_int_and_finite_float() -> None:
    assert _coerce_float(0) == 0.0
    assert _coerce_float(2.5) == 2.5


def test_coerce_float_rejects_bool() -> None:
    assert _coerce_float(True) is None


def test_coerce_float_rejects_non_finite() -> None:
    assert _coerce_float(math.nan) is None
    assert _coerce_float(math.inf) is None
