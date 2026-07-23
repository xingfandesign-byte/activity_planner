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
