import random
from itertools import pairwise

import pytest

from core.levels import PROMPTS_PER_LEVEL, generate_prompts, parse_levels, stars_for_misses
from storage.store import load_levels


def test_tc30_prompt_generation_many_seeds() -> None:
    for level in load_levels():
        for seed in range(300):
            prompts = generate_prompts(level, random.Random(seed))
            assert len(prompts) == level.prompt_count
            assert set(prompts) == set(level.notes)
            assert all(a != b for a, b in pairwise(prompts))


def test_tc19_level1_has_six_prompts_of_do_re_mi() -> None:
    level1 = load_levels()[0]
    prompts = generate_prompts(level1, random.Random(1))
    assert len(prompts) == PROMPTS_PER_LEVEL
    assert {p.name for p in prompts} == {"C4", "D4", "E4"}


def test_level3_extends_prompts_to_cover_all_notes() -> None:
    # Spec conflict: 8 notes cannot all appear in 6 prompts.
    assert load_levels()[2].prompt_count == 8


@pytest.mark.parametrize(
    ("misses", "stars"),
    [(0, 3), (2, 3), (3, 2), (6, 2), (7, 1), (20, 1)],
)
def test_tc31_tc32_tc33_stars(misses: int, stars: int) -> None:
    assert stars_for_misses(misses) == stars


def test_parse_rejects_bad_data() -> None:
    with pytest.raises(ValueError):
        parse_levels([{"number": 2, "theme": "x", "notes": ["C4", "D4"]}])
    with pytest.raises(ValueError):
        parse_levels([{"number": 1, "theme": "x", "notes": ["C4"]}])
