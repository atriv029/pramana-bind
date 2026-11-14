import pytest

from pramana_bind.retreat import (NTuple, Relations, equivocation, gap,
                                  implied_credence, retreat)

N1 = NTuple(paksa="adults", sadhya="causes", quantifier="all", modality="certain", hetu="h")


def test_identical_is_zero():
    assert retreat(N1, N1, Relations()) == 0.0


def test_full_retreat_is_one():
    n2 = N1.model_copy(update={"quantifier": "one", "modality": "possible"})
    rel = Relations(paksa="different", sadhya="replaced", hetu="new")
    assert retreat(N1, n2, rel) == pytest.approx(1.0)


def test_partial_and_strengthening_not_counted():
    n2 = N1.model_copy(update={"quantifier": "most", "modality": "probable"})
    r = retreat(N1, n2, Relations(paksa="subset_superset", sadhya="weakening"))
    assert r == pytest.approx(0.2 * (0.5 + 0.5 + 1 / 3 + 0.5))
    assert retreat(n2, N1, Relations()) == 0.0


def test_weights_validated():
    with pytest.raises(ValueError):
        retreat(N1, N1, Relations(), {"p": 1.0})


def test_equivocation_and_gap():
    assert equivocation(0.6, acknowledged=True) == 0.0
    assert equivocation(0.6, acknowledged=False) == 0.6
    i = implied_credence("a", [lambda a: (True, 90), lambda a: (True, 70)])
    assert i == pytest.approx(0.8)
    assert gap(i, 0.3) == pytest.approx(0.5)
