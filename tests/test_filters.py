import pytest

from content_filters import is_adult_category


def test_is_adult_category_positive():
    assert is_adult_category("Adults Only")
    assert is_adult_category("+18 Filme")
    assert is_adult_category("xxx channel")


def test_is_adult_category_negative():
    assert not is_adult_category("News Channel")
    assert not is_adult_category("Sports Live")
