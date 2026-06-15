from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter():
    results = search_listings("tee", size="M", max_price=100)
    assert all("m" in item["size"].lower() for item in results)


def test_search_no_size_filter():
    results_with = search_listings("vintage", size="M", max_price=100)
    results_without = search_listings("vintage", size=None, max_price=100)
    assert len(results_without) >= len(results_with)


def test_search_best_match_first():
    results = search_listings("vintage graphic tee streetwear", size=None, max_price=100)
    assert len(results) > 1


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def test_suggest_outfit_with_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    suggestion = suggest_outfit(results[0], get_example_wardrobe())
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0


def test_suggest_outfit_empty_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    suggestion = suggest_outfit(results[0], get_empty_wardrobe())
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def test_create_fit_card_returns_caption():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    outfit = suggest_outfit(results[0], get_example_wardrobe())
    caption = create_fit_card(outfit, results[0])
    assert isinstance(caption, str)
    assert len(caption) > 0


def test_create_fit_card_empty_outfit():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    caption = create_fit_card("", results[0])
    assert caption == "Cannot generate a fit card without an outfit suggestion."


def test_create_fit_card_whitespace_outfit():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    caption = create_fit_card("   ", results[0])
    assert caption == "Cannot generate a fit card without an outfit suggestion."


def test_create_fit_card_varies():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    outfit = suggest_outfit(results[0], get_example_wardrobe())
    caption1 = create_fit_card(outfit, results[0])
    caption2 = create_fit_card(outfit, results[0])
    assert caption1 != caption2
