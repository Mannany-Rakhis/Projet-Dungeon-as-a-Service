import pytest

from app.domain.heroes import Guerrier, Mage, Voleur, creer_heros


@pytest.mark.parametrize(
    ("hero", "expected_damage"),
    [
        (Guerrier(force=6, agilite=2, intelligence=2), (14, False)),
        (Mage(force=2, agilite=2, intelligence=6), (19, False)),
    ],
)
def test_guerrier_and_mage_damage(hero, expected_damage) -> None:
    assert hero.calculer_degats() == expected_damage


def test_warrior_armor_never_reduces_damage_below_one() -> None:
    warrior = Guerrier(force=6, agilite=2, intelligence=2)

    assert warrior.subir_degats(10) == 9
    assert warrior.subir_degats(1) == 1
    assert warrior.subir_degats(0) == 1


def test_thief_critical_damage_when_random_roll_is_critical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    thief = Voleur(force=2, agilite=6, intelligence=2)
    monkeypatch.setattr("app.domain.heroes.random.randint", lambda low, high: low)

    assert thief.calculer_degats() == (28, True)


def test_thief_normal_damage_when_random_roll_is_not_critical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    thief = Voleur(force=2, agilite=6, intelligence=2)
    monkeypatch.setattr("app.domain.heroes.random.randint", lambda low, high: high)

    assert thief.calculer_degats() == (14, False)


@pytest.mark.parametrize(
    ("hero", "expected_hp"),
    [
        (Guerrier(force=6, agilite=2, intelligence=2), 32),
        (Mage(force=2, agilite=2, intelligence=6), 24),
        (Voleur(force=2, agilite=6, intelligence=2), 24),
    ],
)
def test_maximum_hp_is_based_on_strength(hero, expected_hp) -> None:
    assert hero.pv_max == expected_hp


def test_unknown_hero_class_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Classe de héros inconnue"):
        creer_heros("paladin", force=4, agilite=3, intelligence=3)
