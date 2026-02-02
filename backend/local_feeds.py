"""
Local feeds aggregator to complement Google Places API.
Fetches events and local content from RSS/Atom, Facebook (optional), and Eventbrite (optional).
All items are normalized to the same shape as recommendation items for merging.
"""

import os
import re
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

try:
    import requests
except ImportError:
    requests = None

# Optional: Facebook Graph API base
FACEBOOK_GRAPH = "https://graph.facebook.com/v18.0"
# Optional: Eventbrite API
EVENTBRITE_API = "https://www.eventbriteapi.com/v3"
# Optional: Manus AI agent for personalized local feed
MANUS_API_BASE = "https://api.manus.ai/v1"


def profile_to_prompt(profile):
    """
    Convert user preference dict to a natural-language prompt for personalized
    local weekend recommendations (e.g. for Manus or other agents).
    """
    location = "San Francisco, CA"
    if profile:
        loc = profile.get("location") or {}
        if isinstance(loc, dict):
            location = loc.get("formatted_address") or loc.get("input") or loc.get("value") or location
        else:
            location = str(loc) if loc else location
    group_labels = {
        "solo": "myself (solo)",
        "couple": "me and my partner (couple)",
        "family": "my family with kids",
        "friends": "me and my friends",
    }
    interest_labels = {
        "nature": "nature, parks, outdoor",
        "arts_culture": "arts, culture, museums",
        "food_drinks": "food, restaurants, drinks",
        "adventure": "adventure, sports",
        "learning": "learning, science",
        "entertainment": "entertainment, shows",
        "relaxation": "relaxation, wellness",
        "shopping": "shopping, markets",
        "events": "local events, festivals",
    }
    energy_labels = {"relaxing": "relaxing", "moderate": "moderate", "active": "active"}
    budget_labels = {"free": "free only", "low": "budget-friendly", "moderate": "moderate", "any": "any budget"}
    group = group_labels.get(profile.get("group_type"), "myself")
    interests = profile.get("interests") or []
    interest_str = ", ".join(interest_labels.get(i, i) for i in interests) or "various activities"
    energy = energy_labels.get(profile.get("energy_level"), "moderate")
    budget = budget_labels.get(profile.get("budget"), "moderate")
    travel_ranges = profile.get("travel_time_ranges") or ["15-30"]
    travel_str = ", ".join(str(r) for r in travel_ranges) + " min" if travel_ranges else "30 min"
    constraints = []
    if profile.get("group_type") == "family":
        constraints.append("must be kid-friendly")
    if profile.get("accessibility"):
        constraints.append("accessibility: " + ", ".join(profile["accessibility"]))
    if profile.get("avoid"):
        constraints.append("avoid: " + ", ".join(profile["avoid"]))
    constraint_str = "\n**Constraints:** " + "; ".join(constraints) if constraints else ""
    return (
        "Find 5 personalized local weekend recommendations (events, places, or activities) "
        f"for someone in **{location}**. "
        f"Planning for: {group}. Interests: {interest_str}. "
        f"Activity level: {energy}. Budget: {budget}. Max travel time: {travel_str}. "
        f"{constraint_str}\n\n"
        "Search local news, event listings, and community sources for this weekend. "
        "Reply with ONLY a valid JSON array of 5 objects, no other text. Each object must have: "
        '"title" (string), "category" (string, e.g. events/parks/food), "explanation" (string, 1 sentence), '
        '"address" (string or empty), "link" (string URL or empty), "distance_miles" (number, optional), '
        '"travel_time_min" (number, optional), "price_flag" (string: free/$/$$/$$$, optional).'
    )


def _fetch_url(url, timeout=10, headers=None):
    """Fetch URL and return bytes or None."""
    headers = headers or {}
    if "User-Agent" not in headers:
        headers["User-Agent"] = "WeekendPlanner/1.0 (Local Feeds)"
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (URLError, HTTPError, OSError) as e:
        print(f"[LOCAL_FEEDS] Fetch error {url}: {e}")
        return None


def _parse_rss_or_atom(raw_bytes, feed_url, source_label):
    """
    Parse RSS 2.0 or Atom 1.0 and return list of dicts:
    { title, link, description, pub_date, location_str, source, source_url }
    """
    if not raw_bytes:
        return []
    items = []
    try:
        root = ET.fromstring(raw_bytes)
    except ET.ParseError as e:
        print(f"[LOCAL_FEEDS] XML parse error for {feed_url}: {e}")
        return []

    # RSS 2.0: <rss><channel><item>...
    channel = root.find("channel")
    if channel is not None:
        for item in channel.findall("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            pub_el = item.find("pubDate")
            title = (title_el.text or "").strip() if title_el is not None else ""
            link = (link_el.text or "").strip() if link_el is not None else ""
            if not title and not link:
                continue
            desc = ""
            if desc_el is not None and desc_el.text:
                desc = desc_el.text.strip()
            elif desc_el is not None and len(desc_el):
                desc = ET.tostring(desc_el, encoding="unicode", method="text")[:500]
            pub_date = (pub_el.text or "").strip() if pub_el is not None else ""
            items.append({
                "title": title or "Untitled",
                "link": link,
                "description": desc,
                "pub_date": pub_date,
                "location_str": None,
                "source": source_label,
                "source_url": feed_url,
            })
        return items

    # Atom 1.0: <feed xmlns="..."><entry>...
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall(".//atom:entry", ns) or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    if not entries:
        entries = root.findall(".//entry")
    for entry in entries:
        def text(el, default=""):
            if el is None:
                return default
            return (el.text or "").strip() or default

        title_el = entry.find("atom:title", ns) or entry.find("{http://www.w3.org/2005/Atom}title") or entry.find("title")
        link_el = entry.find("atom:link", ns) or entry.find("{http://www.w3.org/2005/Atom}link") or entry.find("link")
        link = ""
        if link_el is not None:
            link = link_el.get("href") or text(link_el)
        title = text(title_el) if title_el is not None else ""
        if not title and not link:
            continue
        summary_el = entry.find("atom:summary", ns) or entry.find("{http://www.w3.org/2005/Atom}summary") or entry.find("summary")
        desc = text(summary_el) if summary_el is not None else ""
        updated_el = entry.find("atom:updated", ns) or entry.find("{http://www.w3.org/2005/Atom}updated") or entry.find("updated")
        pub_date = text(updated_el) if updated_el is not None else ""
        items.append({
            "title": title or "Untitled",
            "link": link,
            "description": desc,
            "pub_date": pub_date,
            "location_str": None,
            "source": source_label,
            "source_url": feed_url,
        })
    return items


def fetch_rss_feed(feed_url, source_label=None, timeout=10):
    """
    Fetch a single RSS or Atom feed and return normalized items.
    source_label: optional name (e.g. "Axios Local", "Facebook Local") for display.
    """
    if not feed_url or not feed_url.strip():
        return []
    feed_url = feed_url.strip()
    label = source_label or re.sub(r"^https?://", "", feed_url).split("/")[0]
    raw = _fetch_url(feed_url, timeout=timeout)
    return _parse_rss_or_atom(raw, feed_url, label)


def fetch_all_rss_feeds(feed_configs, timeout=10):
    """
    feed_configs: list of dicts { "url": "...", "label": "Axios Local" } or list of URL strings.
    Returns list of normalized feed items from all feeds.
    """
    all_items = []
    for cfg in feed_configs:
        if isinstance(cfg, str):
            url, label = cfg, None
        else:
            url = (cfg or {}).get("url") or (cfg or {}).get("url")
            label = (cfg or {}).get("label")
        items = fetch_rss_feed(url, source_label=label, timeout=timeout)
        for it in items:
            it["source"] = it.get("source") or label or "RSS"
        all_items.extend(items)
    return all_items


def fetch_facebook_events_near(lat, lng, distance_meters, access_token, limit=10):
    """
    Optional: use Facebook Graph API to find places near (lat, lng), then get their events.
    Requires FACEBOOK_ACCESS_TOKEN with permissions for place search and events.
    Returns list of normalized items { title, link, description, ... }.
    """
    if not access_token or not requests:
        return []
    try:
        # Search places near location
        search_url = f"{FACEBOOK_GRAPH}/search"
        params = {
            "type": "place",
            "center": f"{lat},{lng}",
            "distance": min(int(distance_meters), 50000),
            "fields": "id,name,location",
            "access_token": access_token,
            "limit": 20,
        }
        r = requests.get(search_url, params=params, timeout=10)
        if r.status_code != 200:
            print(f"[LOCAL_FEEDS] Facebook search error: {r.status_code}")
            return []
        data = r.json()
        places = data.get("data", [])
        if not places:
            return []

        events_found = []
        for place in places[:10]:
            if len(events_found) >= limit:
                break
            place_id = place.get("id")
            place_name = place.get("name", "")
            events_url = f"{FACEBOOK_GRAPH}/{place_id}/events"
            ep = {
                "fields": "id,name,description,start_time,end_time,place,link",
                "access_token": access_token,
                "limit": 5,
            }
            er = requests.get(events_url, params=ep, timeout=8)
            if er.status_code != 200:
                continue
            ed = er.json()
            for ev in ed.get("data", [])[:3]:
                start = ev.get("start_time", "")
                events_found.append({
                    "title": ev.get("name", "Event"),
                    "link": ev.get("link") or f"https://www.facebook.com/events/{ev.get('id', '')}",
                    "description": (ev.get("description") or "")[:500],
                    "pub_date": start,
                    "location_str": place_name,
                    "source": "Facebook Local",
                    "source_url": "https://www.facebook.com/events",
                    "place_id": ev.get("id"),
                })
        return events_found[:limit]
    except Exception as e:
        print(f"[LOCAL_FEEDS] Facebook error: {e}")
        return []


def fetch_eventbrite_events(lat, lng, radius_km, token, limit=10):
    """
    Optional: Eventbrite API - search events by location.
    Requires EVENTBRITE_TOKEN (private token). Returns normalized items.
    """
    if not token or not requests:
        return []
    try:
        url = f"{EVENTBRITE_API}/events/search/"
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "location.within": f"{radius_km}km",
            "expand": "venue",
        }
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code != 200:
            print(f"[LOCAL_FEEDS] Eventbrite error: {r.status_code}")
            return []
        data = r.json()
        events = data.get("events", [])
        items = []
        for ev in events[:limit]:
            name = ev.get("name", {}).get("text", "Event")
            url_ev = ev.get("url", "")
            desc = (ev.get("description", {}).get("text", "") or "")[:500]
            start = ev.get("start", {}).get("local", "")
            venue = ev.get("venue", {}) or {}
            address = venue.get("address", {}) or {}
            loc_str = address.get("localized_address_display") or venue.get("name", "")
            items.append({
                "title": name,
                "link": url_ev,
                "description": desc,
                "pub_date": start,
                "location_str": loc_str,
                "source": "Eventbrite",
                "source_url": "https://www.eventbrite.com",
                "place_id": ev.get("id"),
            })
        return items
    except Exception as e:
        print(f"[LOCAL_FEEDS] Eventbrite error: {e}")
        return []


def normalize_feed_item_to_recommendation(item, index, user_lat, user_lng, week_str, geocode_fn=None):
    """
    Turn a raw feed item into the same shape as Google Places recommendations
    so they can be merged and sorted. geocode_fn(location_str) -> (lat, lng) optional.
    """
    title = item.get("title", "Local event")
    link = item.get("link", "")
    source = item.get("source", "Local feed")
    location_str = item.get("location_str") or ""
    lat, lng = None, None
    if geocode_fn and location_str:
        try:
            coords = geocode_fn(location_str)
            if coords:
                lat, lng = coords
        except Exception:
            pass
    if lat is None:
        lat, lng = user_lat, user_lng  # no distance penalty if we can't geocode
    from math import radians, sin, cos, sqrt, atan2
    # Use provided distance/travel_time (e.g. from Manus) when present
    if item.get("distance_miles") is not None and isinstance(item.get("distance_miles"), (int, float)):
        distance_miles = float(item["distance_miles"])
        travel_time_min = item.get("travel_time_min")
        if travel_time_min is None or not isinstance(travel_time_min, (int, float)):
            travel_time_min = max(5, int(round((distance_miles / 25) * 60)))
        else:
            travel_time_min = max(5, int(travel_time_min))
    else:
        R = 3959  # miles
        lat1, lng1 = radians(user_lat), radians(user_lng)
        lat2, lng2 = radians(lat), radians(lng)
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance_miles = R * c
        travel_time_min = max(5, int(round((distance_miles / 25) * 60)))
    place_id = item.get("place_id") or f"feed_{hashlib.md5((link or title).encode()).hexdigest()[:12]}"
    return {
        "rec_id": f"lf_{week_str}_{index}",
        "type": "event",
        "place_id": place_id,
        "title": title,
        "category": "events",
        "distance_miles": round(distance_miles, 1),
        "travel_time_min": travel_time_min,
        "price_flag": (item.get("price_flag") or "$").strip() if isinstance(item.get("price_flag"), str) else "$",
        "kid_friendly": False,
        "indoor_outdoor": "indoor",
        "explanation": f"From {source}",
        "source_url": link,
        "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lng}" if lat and lng else link,
        "address": location_str or "",
        "rating": 0,
        "total_ratings": 0,
        "photo_url": None,
        "feed_source": source,
        "feed_item": True,
    }


def _parse_manus_output_text(text):
    """Extract JSON array of recommendations from Manus agent output (may be in markdown code block)."""
    if not text or not text.strip():
        return []
    text = text.strip()
    import json
    # Try to find JSON array in code block or raw
    for pattern in (r"```(?:json)?\s*([\s\S]*?)```", r"\[\s*\{[\s\S]*\}\s*\]"):
        m = re.search(pattern, text)
        if m:
            raw = m.group(1).strip() if m.lastindex and m.lastindex >= 1 else m.group(0)
            try:
                data = json.loads(raw)
                if isinstance(data, list):
                    return data
            except (json.JSONDecodeError, TypeError):
                pass
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def fetch_manus_personalized_feed(profile, api_key, poll_interval=3, poll_timeout=90):
    """
    Call Manus API with user preference as prompt; poll until task completes;
    parse output into list of raw items { title, link, description, location_str, source }.
    """
    if not api_key or not requests:
        return []
    prompt = profile_to_prompt(profile)
    try:
        r = requests.post(
            f"{MANUS_API_BASE}/tasks",
            headers={"accept": "application/json", "content-type": "application/json", "API_KEY": api_key},
            json={"prompt": prompt, "agentProfile": "manus-1.6"},
            timeout=15,
        )
        if r.status_code != 200:
            print(f"[LOCAL_FEEDS] Manus create task error: {r.status_code} {r.text[:200]}")
            return []
        data = r.json()
        task_id = data.get("task_id")
        if not task_id:
            print("[LOCAL_FEEDS] Manus response missing task_id")
            return []
        # Poll until completed or timeout
        elapsed = 0
        while elapsed < poll_timeout:
            tr = requests.get(
                f"{MANUS_API_BASE}/tasks/{task_id}",
                headers={"accept": "application/json", "API_KEY": api_key},
                timeout=10,
            )
            if tr.status_code != 200:
                break
            task = tr.json()
            status = task.get("status", "")
            if status == "completed":
                output = task.get("output") or []
                all_text = []
                for msg in output:
                    for c in msg.get("content") or []:
                        if c.get("type") == "output_text" and c.get("text"):
                            all_text.append(c["text"])
                text = "\n".join(all_text)
                arr = _parse_manus_output_text(text)
                raw_items = []
                for i, obj in enumerate(arr):
                    if not isinstance(obj, dict):
                        continue
                    title = obj.get("title") or obj.get("name") or ""
                    if not title:
                        continue
                    raw_items.append({
                        "title": title,
                        "link": obj.get("link") or obj.get("url") or "",
                        "description": obj.get("explanation") or obj.get("description") or "",
                        "location_str": obj.get("address") or "",
                        "source": "Manus",
                        "source_url": "https://manus.im",
                        "distance_miles": obj.get("distance_miles"),
                        "travel_time_min": obj.get("travel_time_min"),
                        "price_flag": obj.get("price_flag") or "$",
                    })
                return raw_items
            if status == "failed":
                print(f"[LOCAL_FEEDS] Manus task failed: {task.get('error', '')[:200]}")
                return []
            import time
            time.sleep(poll_interval)
            elapsed += poll_interval
        print("[LOCAL_FEEDS] Manus task timed out")
        return []
    except Exception as e:
        print(f"[LOCAL_FEEDS] Manus error: {e}")
        return []


def get_local_feed_config():
    """
    Read config from environment.
    LOCAL_FEED_URLS: comma-separated RSS/Atom URLs (e.g. https://api.axios.com/feed/top/)
    LOCAL_FEED_LABELS: optional comma-separated labels (same order as URLs)
    FACEBOOK_ACCESS_TOKEN: optional token for Facebook events
    EVENTBRITE_TOKEN: optional token for Eventbrite
    MANUS_API_KEY: optional token for Manus AI personalized local feed
    """
    urls_str = os.environ.get("LOCAL_FEED_URLS", "").strip()
    labels_str = os.environ.get("LOCAL_FEED_LABELS", "").strip()
    urls = [u.strip() for u in urls_str.split(",") if u.strip()]
    labels = [l.strip() for l in labels_str.split(",") if l.strip()]
    feed_configs = []
    for i, url in enumerate(urls):
        feed_configs.append({"url": url, "label": labels[i] if i < len(labels) else None})
    return {
        "feed_configs": feed_configs,
        "facebook_token": os.environ.get("FACEBOOK_ACCESS_TOKEN", "").strip() or None,
        "eventbrite_token": os.environ.get("EVENTBRITE_TOKEN", "").strip() or None,
        "manus_api_key": os.environ.get("MANUS_API_KEY", "").strip() or None,
    }


def get_local_feed_recommendations(profile, user_lat, user_lng, geocode_fn=None, max_items=5,
                                   max_travel_min=None, max_radius_miles=None, week_str=None):
    """
    Fetch from all configured local feeds (RSS, Facebook, Eventbrite), normalize to
    recommendation items, filter by travel/radius if set, and return up to max_items.
    """
    from datetime import datetime
    week_str = week_str or f"{datetime.now().year}-{datetime.now().isocalendar()[1]:02d}"
    config = get_local_feed_config()
    raw_items = []

    # RSS/Atom feeds
    if config["feed_configs"]:
        try:
            rss_items = fetch_all_rss_feeds(config["feed_configs"], timeout=8)
            raw_items.extend(rss_items)
        except Exception as e:
            print(f"[LOCAL_FEEDS] RSS error: {e}")

    # Facebook events (optional)
    if config["facebook_token"]:
        try:
            radius_m = (max_radius_miles or 25) * 1609
            fb_items = fetch_facebook_events_near(
                user_lat, user_lng, min(int(radius_m), 50000),
                config["facebook_token"], limit=10
            )
            raw_items.extend(fb_items)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Facebook error: {e}")

    # Eventbrite (optional)
    if config["eventbrite_token"]:
        try:
            radius_km = (max_radius_miles or 25) * 1.609
            eb_items = fetch_eventbrite_events(
                user_lat, user_lng, min(radius_km, 50), config["eventbrite_token"], limit=10
            )
            raw_items.extend(eb_items)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Eventbrite error: {e}")

    # Manus AI personalized local feed (optional): convert user preference to prompt, get recommendations
    if config.get("manus_api_key"):
        try:
            manus_items = fetch_manus_personalized_feed(profile, config["manus_api_key"], poll_interval=3, poll_timeout=90)
            raw_items.extend(manus_items)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Manus error: {e}")

    if not raw_items:
        return []

    # Normalize to recommendation shape and filter by distance/travel
    recs = []
    for i, item in enumerate(raw_items):
        rec = normalize_feed_item_to_recommendation(
            item, i, user_lat, user_lng, week_str, geocode_fn=geocode_fn
        )
        if max_travel_min is not None and rec.get("travel_time_min", 0) > max_travel_min:
            continue
        if max_radius_miles is not None and rec.get("distance_miles", 0) > max_radius_miles:
            continue
        recs.append(rec)
    recs.sort(key=lambda x: (x.get("distance_miles", 999), x.get("title", "")))
    return recs[:max_items]
