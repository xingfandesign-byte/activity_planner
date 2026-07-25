"""
Tests for recommendation scoring, personalization loop, and db persistence.
Run from backend/: venv/bin/python -m pytest test_recommendations.py -v
"""
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

# Must be set before importing app/db: db reads DATABASE_URL at import time,
# and app spawns cache-warming threads at import time unless disabled.
os.environ['DATABASE_URL'] = os.path.join(tempfile.gettempdir(), 'activity_planner_test_import.db')
os.environ['DISABLE_WARM_CACHE_ON_IMPORT'] = '1'

import pytest

import db
import app
from local_feeds import _infer_kid_friendly


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    """Point db.py at a fresh temp database for each test."""
    monkeypatch.setattr(db, 'DB_PATH', str(tmp_path / 'test.db'))
    db.init_db()
    return db


def _score(item, prefs=None, user_affinity=None, **kwargs):
    return app._score_recommendation_item(item, prefs or {}, user_affinity or {}, **kwargs)


# ---------- 1. Whole-word preference matching ----------

def test_preference_match_whole_word():
    prefs = {'interests': ['arts_culture']}
    # "art" appears only as a substring of "Stewart" -> no match
    item = {"title": "Stewart Street Fair", "category": "events", "type": "event"}
    _, parts = _score(item, prefs)
    assert "preference_match" not in parts

    # "Art" as a whole word -> match
    item2 = {"title": "Art walk downtown", "category": "events", "type": "event"}
    _, parts2 = _score(item2, prefs)
    assert parts2["preference_match"] == 9


# ---------- 2. Rating fairness ----------

def test_rating_neutral_midpoint_when_unrated():
    item = {"title": "Some event", "category": "events", "type": "event"}
    _, parts = _score(item)
    assert parts["rating"] == 9


def test_rating_scored_when_present():
    item = {"title": "Some place", "category": "events", "type": "event", "rating": 5.0}
    _, parts = _score(item)
    assert parts["rating"] == 15


# ---------- 3. Unknown price neutrality ----------

def test_budget_unknown_price_no_part():
    prefs = {'budget': {'max': 0}}  # normalizes to 'free'
    item = {"title": "Mystery event", "category": "events", "type": "event"}  # no price_flag
    _, parts = _score(item, prefs)
    assert "budget" not in parts


def test_budget_priced_item_free_preference():
    prefs = {'budget': {'max': 0}}
    item = {"title": "Pricey event", "category": "events", "type": "event", "price_flag": "$$"}
    _, parts = _score(item, prefs)
    assert parts["budget"] == -24


def test_budget_free_item_bonus():
    prefs = {'budget': {'max': 0}}
    item = {"title": "Free event", "category": "events", "type": "event", "price_flag": "free"}
    _, parts = _score(item, prefs)
    assert parts["budget"] == 8


# ---------- 4. kid_friendly tri-state ----------

def test_family_group_fit_tristate():
    prefs = {'group_type': 'family'}
    base = {"title": "Some event", "category": "events", "type": "event"}
    _, parts = _score(dict(base, kid_friendly=None), prefs)
    assert parts.get("group_fit", 0) == 0
    _, parts = _score(dict(base, kid_friendly=True), prefs)
    assert parts["group_fit"] == 14
    _, parts = _score(dict(base, kid_friendly=False), prefs)
    assert parts["group_fit"] == -10


def test_infer_kid_friendly():
    assert _infer_kid_friendly("Family storytime at library") is True
    assert _infer_kid_friendly("21+ cocktail crawl") is False
    assert _infer_kid_friendly("Jazz night") is None


# ---------- 5. Canonical category taxonomy ----------

def test_affinity_applies_across_taxonomies():
    # Google/mock-style affinity key "parks" must match feed-style category "nature"
    item = {"title": "Nature walk", "category": "nature", "type": "event"}
    _, parts = _score(item, user_affinity={"parks": 1.0})
    assert parts["affinity"] == 18.0


# ---------- 6. Soft novelty penalty ----------

def test_novelty_penalty_recently_served():
    now = datetime.now()
    item = {"title": "Repeat event", "category": "events", "type": "event", "place_id": "p1"}
    fresh_score, _ = _score(item, now=now, recent_map={})
    seen_score, seen_parts = _score(item, now=now, recent_map={"p1": now - timedelta(days=3)})
    assert seen_parts["novelty"] == -20
    assert fresh_score - seen_score == pytest.approx(20)


# ---------- 7. db layer ----------

def test_saved_and_visited_persist_category(fresh_db):
    fresh_db.add_saved('u1', 'place1', category='nature')
    fresh_db.add_visited('u1', 'place2', category='museums')
    assert fresh_db.get_saved_list('u1')[0]['category'] == 'nature'
    assert fresh_db.get_visited_list('u1')[0]['category'] == 'museums'


def test_recent_recommendation_dedup(fresh_db):
    fresh_db.add_recent_recommendation('u1', 'place1', 'rec_a', '2026-29', category='nature')
    fresh_db.add_recent_recommendation('u1', 'place1', 'rec_b', '2026-29', category='nature')
    recs = fresh_db.get_recent_recommendations_list('u1')
    assert len(recs) == 1
    assert recs[0]['rec_id'] == 'rec_a'
    assert recs[0]['category'] == 'nature'
    # A different week is a new impression
    fresh_db.add_recent_recommendation('u1', 'place1', 'rec_c', '2026-30', category='nature')
    assert len(fresh_db.get_recent_recommendations_list('u1')) == 2


def test_affinity_cache_invalidated_by_saved_and_click(fresh_db):
    fresh_db.set_affinity_cache('u1', {'nature': 0.5})
    assert fresh_db.get_affinity_cache('u1') == {'nature': 0.5}
    fresh_db.add_saved('u1', 'place1', category='nature')
    assert fresh_db.get_affinity_cache('u1') is None

    fresh_db.set_affinity_cache('u1', {'nature': 0.5})
    fresh_db.add_click('u1', 'place1', category='nature')
    assert fresh_db.get_affinity_cache('u1') is None


# ---------- 8. Time decay on interactions ----------

def test_affinity_time_decay(fresh_db):
    user = 'u1'
    now = datetime.now()
    old = now - timedelta(days=180)
    conn = sqlite3.connect(fresh_db.DB_PATH)
    conn.executemany(
        "INSERT INTO feedback (user_id, place_id, feedback_type, category, created_at) VALUES (?, ?, ?, ?, ?)",
        [
            (user, 'p_recent', 'thumbs_up', 'nature', now.isoformat()),
            (user, 'p_old', 'thumbs_up', 'food_drink', old.isoformat()),
            (user, 'p_control', 'thumbs_up', 'shopping', now.isoformat()),
        ],
    )
    conn.commit()
    conn.close()

    scores = app.get_user_affinity_scores(user)
    assert scores['nature'] > 0
    assert scores['food_drink'] > 0
    # Same signal, different age: recent thumbs_up beats 180-day-old one
    assert scores['nature'] > scores['food_drink']
    # Control: same signal and same recency scores identically
    assert scores['nature'] == scores['shopping']


# ---------- 9. Email digest unification ----------

def test_digest_items_use_main_engine(monkeypatch):
    """get_weekend_digest_items returns the top slice of the main engine's ranked items."""
    calls = {}
    fake_items = [{"title": f"Item {i}", "place_id": f"p{i}", "rec_id": f"r{i}"} for i in range(8)]

    def fake_get_recommendations(user_id, prefs):
        calls['args'] = (user_id, prefs)
        return fake_items, ['fake']

    monkeypatch.setattr(app, 'get_recommendations', fake_get_recommendations)
    prefs = {'home_location': {'lat': 34.05, 'lng': -118.24}}
    items = app.get_weekend_digest_items('u1', prefs, max_items=5)
    assert calls['args'] == ('u1', prefs)
    assert items == fake_items[:5]


def test_digest_location_prefers_home_location():
    """home_location (the key PUT /v1/preferences saves) wins over the legacy 'location' key."""
    prefs = {
        'home_location': {'lat': 34.05, 'lng': -118.24},
        'location': {'lat': 37.33, 'lng': -121.88},
    }
    assert app._digest_user_lat_lng(prefs) == (34.05, -118.24)
    # Legacy key still honored when home_location is absent
    assert app._digest_user_lat_lng({'location': {'lat': 37.33, 'lng': -121.88}}) == (37.33, -121.88)
    # No location -> main pipeline's default (SF), no geocoding/network involved
    assert app._digest_user_lat_lng({}) == (37.7749, -122.4194)


def test_why_picked_unknown_price_not_labeled_free():
    assert 'Free' not in app._why_picked({"title": "Mystery event", "category": "events", "price_flag": None})
    assert 'Free' in app._why_picked({"title": "Park day", "category": "parks", "price_flag": "free"})


# ---------- 10. Backend hardening fixes ----------

def test_filter_loads_visited_once_per_batch(monkeypatch, fresh_db):
    """Visited places are loaded with a single query per filter run, not per candidate."""
    fresh_db.add_visited('u1', 'p_visited', category='parks')
    calls = []
    real_get = db.get_visited_list

    def spy(user_id):
        calls.append(user_id)
        return real_get(user_id)

    monkeypatch.setattr(app.db, 'get_visited_list', spy)
    items = [
        {"title": "Been There", "place_id": "p_visited", "type": "place", "address": "1 Main St"},
        {"title": "New Spot A", "place_id": "p_a", "type": "place", "address": "2 Main St"},
        {"title": "New Spot B", "place_id": "p_b", "type": "place", "address": "3 Main St"},
    ]
    filtered, stats = app._filter_recommendation_candidates(items, {}, 'u1')
    assert [i['place_id'] for i in filtered] == ['p_a', 'p_b']
    assert stats['visited'] == 1
    assert len(calls) == 1


def _img_items():
    return [
        {"title": "Alpha", "photo_url": "http://img/Alpha"},  # short-circuits, no fetch
        {"title": "Bravo"},
        {"title": "Charlie"},
        {"title": "Delta"},
    ]


def _patch_image_search(monkeypatch, delays):
    import time as _time
    app.image_search_cache.clear()
    monkeypatch.setattr(app, 'GOOGLE_PLACES_API_KEY', None)

    def fake_search(query, event_url=None, timeout=3):
        _time.sleep(delays.get(query, 0))
        return (f"http://img/{query}", "test")

    monkeypatch.setattr(app, 'search_free_image', fake_search)


def test_image_enrichment_preserves_rank_order(monkeypatch, fresh_db):
    """Completed results are mapped back to their original item, not appended in completion order."""
    _patch_image_search(monkeypatch, {"Bravo": 0.3, "Charlie": 0.1, "Delta": 0.2})
    out = app.enrich_items_with_images(_img_items(), max_time_seconds=10)
    assert [i['title'] for i in out] == ["Alpha", "Bravo", "Charlie", "Delta"]
    for item in out:
        assert item['photo_url'] == f"http://img/{item['title']}"


def test_image_enrichment_timeout_no_dupes_or_drops(monkeypatch, fresh_db):
    """On timeout, unfinished items pass through unchanged — no duplicates, no drops."""
    _patch_image_search(monkeypatch, {"Bravo": 0.2, "Charlie": 1.0, "Delta": 1.0})
    out = app.enrich_items_with_images(_img_items(), max_time_seconds=0.5)
    assert [i['title'] for i in out] == ["Alpha", "Bravo", "Charlie", "Delta"]
    assert out[0]['photo_url'] == "http://img/Alpha"
    assert out[1]['photo_url'] == "http://img/Bravo"
    assert 'photo_url' not in out[2]
    assert 'photo_url' not in out[3]


def test_warm_cache_spawns_single_background_refresh(monkeypatch, fresh_db):
    """Concurrent requests against a stale cache claim the refresh slot atomically."""
    import threading as _th
    import time as _time

    calls = []

    def fake_live(user_id, prefs, cache_key):
        calls.append(cache_key)
        _time.sleep(0.1)
        return [{"title": "Fresh", "place_id": "pf", "rec_id": "rf"}], ["fake"]

    monkeypatch.setattr(app, '_fetch_recommendations_live', fake_live)
    prefs = {'home_location': {'lat': 1.0, 'lng': 2.0}}
    key = app._get_warm_cache_key('u1', prefs)
    with app._warm_cache_lock:
        app._warm_cache.clear()
        app._background_refresh_in_progress.clear()
        app._warm_cache[key] = {
            'items': [{"title": "Old", "place_id": "po", "rec_id": "ro"}],
            'sources': ['fake'],
            'timestamp': datetime.now() - timedelta(seconds=300),  # stale: 180 < age < 600
        }
    try:
        threads = [_th.Thread(target=app.get_recommendations, args=('u1', prefs)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # Wait for the background refresh to finish
        for _ in range(100):
            with app._warm_cache_lock:
                if not app._background_refresh_in_progress:
                    break
            _time.sleep(0.02)
        assert len(calls) == 1
    finally:
        with app._warm_cache_lock:
            app._warm_cache.clear()
            app._background_refresh_in_progress.clear()
