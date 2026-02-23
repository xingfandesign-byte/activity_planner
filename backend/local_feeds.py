"""
Local feeds aggregator to complement Google Places API.
Fetches events and local content from RSS/Atom, Facebook (optional), and Eventbrite (optional).
All items are normalized to the same shape as recommendation items for merging.
"""

import os
import re
import hashlib
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
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
# Optional: Meetup API
MEETUP_API = "https://api.meetup.com"
# Optional: Luma API
LUMA_API = "https://api.lu.ma/public/v1"
# 510families.com RSS feed for family events
FAMILIES_510_RSS = "https://www.510families.com/calendar/feed/"

# New data source API keys (optional - gracefully degrade when not set)
YELP_API_KEY = os.environ.get("YELP_API_KEY", "").strip() or None
TICKETMASTER_API_KEY = os.environ.get("TICKETMASTER_API_KEY", "").strip() or None
TRIPADVISOR_API_KEY = os.environ.get("TRIPADVISOR_API_KEY", "").strip() or None

# Cache for crawled event descriptions
_description_cache = {}  # key: url -> {"description": str, "timestamp": datetime}
DESCRIPTION_CACHE_TTL_SECONDS = 86400  # 24 hours


def fetch_event_description(url, timeout=5):
    """
    Fetch an event page and extract a rich description.
    Uses multiple strategies: Open Graph, meta description, article content.
    Returns extracted description or None if failed.
    """
    if not url or not requests:
        return None
    
    # Check cache first
    cache_key = url
    if cache_key in _description_cache:
        cached = _description_cache[cache_key]
        age = (datetime.now() - cached["timestamp"]).total_seconds()
        if age < DESCRIPTION_CACHE_TTL_SECONDS:
            print(f"[CRAWL] Cache hit for {url[:50]}...")
            return cached["description"]
    
    try:
        print(f"[CRAWL] Fetching {url[:60]}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code != 200:
            print(f"[CRAWL] Failed with status {resp.status_code}")
            return None
        
        html = resp.text
        description = None
        
        # Strategy 1: Open Graph description (og:description)
        og_match = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if not og_match:
            og_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:description["\']', html, re.IGNORECASE)
        if og_match:
            description = og_match.group(1).strip()
            if len(description) > 50:
                print(f"[CRAWL] Found og:description ({len(description)} chars)")
        
        # Strategy 2: Meta description
        if not description or len(description) < 50:
            meta_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not meta_match:
                meta_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description["\']', html, re.IGNORECASE)
            if meta_match:
                meta_desc = meta_match.group(1).strip()
                if len(meta_desc) > len(description or ''):
                    description = meta_desc
                    print(f"[CRAWL] Found meta description ({len(description)} chars)")
        
        # Strategy 3: Look for event-specific content patterns
        if not description or len(description) < 50:
            # Try to find description in common event page patterns
            patterns = [
                r'<div[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</div>',
                r'<div[^>]*class=["\'][^"\']*event-details[^"\']*["\'][^>]*>(.*?)</div>',
                r'<div[^>]*class=["\'][^"\']*event-description[^"\']*["\'][^>]*>(.*?)</div>',
                r'<p[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</p>',
                r'<article[^>]*>(.*?)</article>',
            ]
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1)
                    # Strip HTML tags
                    content = re.sub(r'<[^>]+>', ' ', content)
                    # Clean up whitespace
                    content = re.sub(r'\s+', ' ', content).strip()
                    # Decode HTML entities
                    content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
                    if len(content) > 50 and len(content) > len(description or ''):
                        description = content[:1000]  # Limit to 1000 chars
                        print(f"[CRAWL] Found content via pattern ({len(description)} chars)")
                        break
        
        # Cache result
        _description_cache[cache_key] = {
            "description": description,
            "timestamp": datetime.now()
        }
        
        return description
        
    except requests.exceptions.Timeout:
        print(f"[CRAWL] Timeout fetching {url[:50]}...")
        return None
    except Exception as e:
        print(f"[CRAWL] Error fetching {url[:50]}: {e}")
        return None


def profile_to_prompt(profile):
    """
    Convert user preference dict to a natural-language prompt for personalized
    local activity recommendations.
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
    group_type = profile.get("group_type")
    
    if group_type == "family":
        constraints.append("MUST be kid-friendly and family-appropriate")
        constraints.append("NO singles events, speed dating, nightclubs, bars, or adult-only venues")
    elif group_type == "couple":
        constraints.append("NO singles events, speed dating, or matchmaking events (this is for couples)")
        constraints.append("NO kids story times, toddler activities, or children-only events")
    elif group_type in ("solo", "friends"):
        constraints.append("NO kids story times, toddler activities, mommy-and-me, or children-only events")
    
    if profile.get("accessibility"):
        constraints.append("accessibility: " + ", ".join(profile["accessibility"]))
    if profile.get("avoid"):
        constraints.append("avoid: " + ", ".join(profile["avoid"]))
    constraint_str = "\n**Constraints:** " + "; ".join(constraints) if constraints else ""
    return (
        "Find 5 personalized local activity recommendations (events, places, or activities) "
        f"for someone in **{location}**. "
        f"Planning for: {group}. Interests: {interest_str}. "
        f"Activity level: {energy}. Budget: {budget}. Max travel time: {travel_str}. "
        f"{constraint_str}\n\n"
        "Search local news, event listings, and community sources. "
        "Reply with ONLY a valid JSON array of 5 objects, no other text. Each object must have: "
        '"title" (string), "category" (string, e.g. events/parks/food), "explanation" (string, 1 sentence), '
        '"address" (string with full address for distance calculation), "link" (string URL or empty), '
        '"distance_miles" (number), "travel_time_min" (number), "price_flag" (string: free/$/$$/$$$), '
        '"kid_friendly" (boolean, true if suitable for children).'
    )


def _fetch_url(url, timeout=4, headers=None):
    """Fetch URL and return bytes or None."""
    headers = headers or {}
    if "User-Agent" not in headers:
        headers["User-Agent"] = "ActivityPlanner/1.0 (Local Feeds)"
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
            
            # Handle titles with nested elements (like <li>)
            title = ""
            if title_el is not None:
                if title_el.text:
                    title = title_el.text.strip()
                else:
                    # Title might have nested elements - extract full text
                    title = ET.tostring(title_el, encoding="unicode", method="text").strip()
            
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


def fetch_rss_feed(feed_url, source_label=None, timeout=4):
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


def fetch_all_rss_feeds(feed_configs, timeout=4):
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
        r = requests.get(search_url, params=params, timeout=4)
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
            er = requests.get(events_url, params=ep, timeout=4)
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
        r = requests.get(url, params=params, headers=headers, timeout=4)
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


def fetch_luma_events(lat, lng, radius_miles=25, limit=10):
    """
    Fetch events from Luma (lu.ma) by searching the discover page.
    Luma doesn't have a public location-based API, so we scrape the discover page.
    """
    if not requests:
        return []
    try:
        import json
        
        # Try Luma's discover page with location slugs
        cities = ["sf", "oakland", "berkeley", "bay-area"]
        items = []
        
        for city in cities[:2]:  # Try first 2 cities
            url = f"https://lu.ma/{city}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Accept": "text/html,application/xhtml+xml",
            }
            r = requests.get(url, headers=headers, timeout=4, allow_redirects=True)
            if r.status_code != 200:
                continue
            
            # Look for __NEXT_DATA__ which contains event data
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>([^<]+)</script>', r.text)
            if match:
                try:
                    data = json.loads(match.group(1))
                    data_obj = data.get("props", {}).get("pageProps", {}).get("initialData", {}).get("data", {})
                    events = data_obj.get("events", []) + data_obj.get("featured_events", [])
                    
                    for ev in events[:limit * 2]:
                        # Event data is nested: ev.event contains the actual event info
                        event_data = ev.get("event", {}) if isinstance(ev, dict) else {}
                        if not event_data:
                            continue
                        
                        name = event_data.get("name", "")
                        if not name:
                            continue
                        
                        url_slug = event_data.get("url", "")
                        url_ev = f"https://lu.ma/{url_slug}" if url_slug else ""
                        
                        start = event_data.get("start_at", "")
                        geo = event_data.get("geo_address_info", {}) or {}
                        loc_str = geo.get("city_state") or geo.get("city") or ""
                        
                        # Get calendar/host info
                        calendar = ev.get("calendar", {}) or {}
                        host_name = calendar.get("name", "")
                        desc = f"Hosted by {host_name}" if host_name else "Luma event"
                        
                        items.append({
                            "title": name,
                            "link": url_ev,
                            "description": desc,
                            "pub_date": start,
                            "location_str": loc_str or f"{city.upper()}, CA",
                            "source": "Luma",
                            "source_url": url_ev,
                            "place_id": f"luma_{event_data.get('api_id', '')}",
                        })
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    print(f"[LOCAL_FEEDS] Luma parse error for {city}: {e}")
                    continue
            
            if len(items) >= limit:
                break
        
        # Dedupe by title
        seen = set()
        unique_items = []
        for item in items:
            title_key = item.get("title", "").lower()
            if title_key not in seen:
                seen.add(title_key)
                unique_items.append(item)
        
        print(f"[LOCAL_FEEDS] Luma: fetched {len(unique_items)} events")
        return unique_items[:limit]
    except Exception as e:
        print(f"[LOCAL_FEEDS] Luma error: {e}")
        return []


def fetch_meetup_events(lat, lng, radius_miles=25, categories=None, limit=10):
    """
    Fetch events from Meetup API (GraphQL) by location.
    Uses Meetup's public GraphQL endpoint for event discovery.
    """
    if not requests:
        return []
    try:
        # Meetup GraphQL endpoint
        url = "https://www.meetup.com/gql"
        
        # GraphQL query for nearby events
        query = """
        query($lat: Float!, $lon: Float!, $radius: Int!, $first: Int!) {
            rankedEvents(filter: {lat: $lat, lon: $lon, radius: $radius}, first: $first) {
                edges {
                    node {
                        id
                        title
                        description
                        dateTime
                        eventUrl
                        venue {
                            name
                            address
                            city
                            state
                        }
                        group {
                            name
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "lat": lat,
            "lon": lng,
            "radius": int(radius_miles * 1.6),  # Convert to km
            "first": limit,
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        }
        
        r = requests.post(url, json={"query": query, "variables": variables}, headers=headers, timeout=4)
        if r.status_code != 200:
            print(f"[LOCAL_FEEDS] Meetup GraphQL error: {r.status_code}")
            return _scrape_meetup_events(lat, lng, limit)
        
        data = r.json()
        edges = data.get("data", {}).get("rankedEvents", {}).get("edges", [])
        items = []
        for edge in edges[:limit]:
            ev = edge.get("node", {})
            venue = ev.get("venue", {}) or {}
            loc_parts = [venue.get("name"), venue.get("address"), venue.get("city"), venue.get("state")]
            loc_str = ", ".join([p for p in loc_parts if p])
            group_name = (ev.get("group", {}) or {}).get("name", "")
            desc = (ev.get("description", "") or "")[:500]
            if group_name:
                desc = f"[{group_name}] {desc}"
            items.append({
                "title": ev.get("title", "Meetup Event"),
                "link": ev.get("eventUrl", ""),
                "description": desc,
                "pub_date": ev.get("dateTime", ""),
                "location_str": loc_str,
                "source": "Meetup",
                "source_url": ev.get("eventUrl", "https://www.meetup.com"),
                "place_id": f"meetup_{ev.get('id', '')}",
            })
        print(f"[LOCAL_FEEDS] Meetup: fetched {len(items)} events")
        return items
    except Exception as e:
        print(f"[LOCAL_FEEDS] Meetup error: {e}")
        return _scrape_meetup_events(lat, lng, limit)


def _scrape_meetup_events(lat, lng, limit=10):
    """Fallback: scrape Meetup find page for local events."""
    try:
        url = f"https://www.meetup.com/find/?location={lat}%2C{lng}&source=EVENTS"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code != 200:
            return []
        items = []
        # Look for JSON-LD or embedded data
        import json
        for match in re.finditer(r'<script type="application/ld\+json">([^<]+)</script>', r.text):
            try:
                data = json.loads(match.group(1))
                if isinstance(data, list):
                    for ev in data[:limit]:
                        if ev.get("@type") == "Event":
                            loc = ev.get("location", {})
                            loc_str = ""
                            if isinstance(loc, dict):
                                addr = loc.get("address", {})
                                if isinstance(addr, dict):
                                    loc_str = addr.get("streetAddress", "")
                            items.append({
                                "title": ev.get("name", "Meetup"),
                                "link": ev.get("url", ""),
                                "description": (ev.get("description", "") or "")[:300],
                                "location_str": loc_str,
                                "source": "Meetup",
                                "source_url": ev.get("url", ""),
                            })
            except (json.JSONDecodeError, TypeError):
                continue
        return items[:limit]
    except Exception as e:
        print(f"[LOCAL_FEEDS] Meetup scrape error: {e}")
        return []


def fetch_510families_events(limit=15):
    """
    Fetch family-friendly events from 510families.com via their RSS feed.
    These are local East Bay family events.
    """
    if not requests:
        return []
    try:
        # Use requests library to handle SSL properly
        headers = {"User-Agent": "ActivityPlanner/1.0 (Local Feeds)"}
        r = requests.get(FAMILIES_510_RSS, headers=headers, timeout=4, verify=True)
        if r.status_code != 200:
            print(f"[LOCAL_FEEDS] 510families RSS error: {r.status_code}")
            return []
        
        # Parse RSS
        items = _parse_rss_or_atom(r.content, FAMILIES_510_RSS, "510families")
        
        # Clean up items - titles have <li> tags, descriptions have HTML
        for item in items:
            # Clean title - remove <li> tags and decode HTML entities
            title = item.get("title", "")
            title = re.sub(r'</?li>', '', title).strip()
            try:
                import html as _html
                title = _html.unescape(title)
            except Exception:
                pass
            item["title"] = title or "510families Event"
            
            # Extract location from description (format: "Date<br>Venue<br>Address<br>City")
            desc = item.get("description", "")
            desc_clean = re.sub(r'</?li>', '', desc)
            try:
                desc_clean = _html.unescape(desc_clean)
            except Exception:
                pass
            parts = re.split(r'<br\s*/?>', desc_clean)
            if len(parts) >= 4:
                item["location_str"] = f"{parts[1].strip()}, {parts[3].strip()}"
            elif len(parts) >= 2:
                item["location_str"] = parts[1].strip()
            else:
                item["location_str"] = "East Bay, CA"
            
            item["kid_friendly"] = True
            item["source"] = "510families"
            item["category"] = "family"
        
        print(f"[LOCAL_FEEDS] 510families: fetched {len(items)} events from RSS")
        return items[:limit]
    except Exception as e:
        print(f"[LOCAL_FEEDS] 510families error: {e}")
        return []


def is_inappropriate_for_group(item, group_type):
    """
    Check if an item is inappropriate for the given group type.
    Returns True if the item should be filtered out.
    
    group_type: "solo", "couple", "family", "friends"
    """
    title_lower = (item.get("title", "") or "").lower()
    description_lower = (item.get("description", "") or "").lower()
    category_lower = (item.get("category", "") or "").lower()
    combined = f"{title_lower} {description_lower} {category_lower}"
    
    # Keywords for family-oriented kids activities (only show for families)
    kids_only_keywords = [
        "story time", "storytime", "story hour",
        "toddler time", "baby time", "mommy and me",
        "kids craft", "children's craft",
        "preschool", "kindergarten",
    ]
    
    # Keywords that indicate singles/dating events (filter for couples AND families)
    singles_dating_keywords = [
        "speed dating", "singles", "single mingle", "singles mixer",
        "dating event", "meet singles",
        "matchmaking", "find love", "looking for love",
    ]
    
    # Keywords that indicate adult-only content (filter for families only)
    adult_only_keywords = [
        "adult only", "adults only",
        "21+", "21 and over", "18+", "bar crawl", "pub crawl",
        "wine tasting", "beer tasting", "happy hour", "cocktail party",
        "nightclub", "late night party", "after dark",
        "brewery tour", "winery tour", "distillery tour",
    ]
    
    # Keywords for business/professional events (filter for families)
    business_professional_keywords = [
        "startup", "startups", "pitch", "pitching", "investor",
        "networking", "mixer", "mix &", "professional",
        "entrepreneur", "founders", "venture capital", "vc ",
        "business networking", "tech meetup", "industry",
        "conference", "summit", "workshop for professionals",
        "b2b", "saas", "fintech",
    ]
    
    # Keywords for personal/individual development events (filter for families)
    personal_development_keywords = [
        "journaling", "self-reflection", "self reflection",
        "eq-journaling", "eq journaling", "emotional intelligence",
        "meditation retreat", "silent retreat",
        "personal growth workshop", "self-help",
        "therapy session", "support group",
        "mindfulness for adults", "adult meditation",
    ]
    
    # For solo, couple, friends: filter out kids-only activities
    if group_type in ("solo", "couple", "friends"):
        for keyword in kids_only_keywords:
            if keyword in combined:
                return True
    
    # For couples: also filter out singles/dating events
    if group_type == "couple":
        for keyword in singles_dating_keywords:
            if keyword in combined:
                return True
    
    # For families: filter out singles/dating, adult-only, business/professional, and personal development events
    if group_type == "family":
        for keyword in singles_dating_keywords:
            if keyword in combined:
                return True
        for keyword in adult_only_keywords:
            if keyword in combined:
                return True
        for keyword in business_professional_keywords:
            if keyword in combined:
                return True
        for keyword in personal_development_keywords:
            if keyword in combined:
                return True
    
    return False


def _fuzzy_title_key(title):
    """Generate a fuzzy key for deduplication — strips noise words, punctuation, whitespace."""
    t = (title or "").lower()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    # Remove common noise words
    noise = {'the', 'a', 'an', 'at', 'in', 'on', 'for', 'of', 'and', 'to', 'with', 'free', 'new'}
    words = [w for w in t.split() if w not in noise and len(w) > 1]
    return ' '.join(sorted(words))


def _is_past_event(item):
    """Return True if the event date is clearly in the past."""
    event_date = item.get("event_date") or item.get("pub_date") or ""
    if not event_date:
        return False
    try:
        from datetime import datetime
        # Try ISO format
        dt = datetime.fromisoformat(event_date.replace('Z', '+00:00').split('+')[0].split('T')[0])
        return dt.date() < datetime.now().date()
    except (ValueError, TypeError, AttributeError):
        return False


def rank_and_dedupe_recommendations(items, user_interests=None, max_items=5, group_type=None):
    """
    Rank and deduplicate recommendations from multiple sources.
    Scoring factors:
    - Has distance/location data (strong bonus — items without are less useful)
    - Relevance to user interests (category match)
    - Distance (closer is better)
    - Source diversity (balance different sources)
    - Freshness (upcoming events preferred, past events filtered)
    - Group-appropriateness (filter content based on group type)
    """
    if not items:
        return []
    
    # Filter out inappropriate content based on group type
    if group_type:
        filtered_items = []
        for item in items:
            if is_inappropriate_for_group(item, group_type):
                print(f"[RANK] Filtering out '{item.get('title')}' - not appropriate for {group_type}")
            else:
                filtered_items.append(item)
        items = filtered_items
        print(f"[RANK] After {group_type} filter: {len(items)} items remaining")
    
    # Filter out past events
    before_count = len(items)
    items = [item for item in items if not _is_past_event(item)]
    if len(items) < before_count:
        print(f"[RANK] Filtered {before_count - len(items)} past events")
    
    user_interests = user_interests or []
    interest_categories = {
        "arts_culture": ["arts", "culture", "art", "museum", "gallery", "theater", "music"],
        "nature": ["nature", "park", "outdoor", "hiking", "garden", "trail"],
        "food_drink": ["food", "restaurant", "dining", "cafe", "bar", "brewery", "wine"],
        "food_drinks": ["food", "restaurant", "dining", "cafe", "bar", "brewery", "wine"],
        "fitness": ["fitness", "sports", "yoga", "gym", "run", "bike"],
        "adventure": ["adventure", "sports", "active", "climb", "kayak", "hike"],
        "learning": ["learning", "workshop", "class", "lecture", "education", "science", "library"],
        "shopping": ["shopping", "market", "boutique", "store", "flea"],
        "nightlife": ["nightlife", "club", "bar", "concert", "live music"],
        "family": ["family", "kids", "children", "family-friendly", "playground"],
        "events": ["event", "festival", "fair", "celebration", "community"],
        "entertainment": ["entertainment", "show", "theater", "music", "concert", "comedy"],
        "relaxation": ["relaxation", "spa", "meditation", "yoga", "wellness", "garden"],
    }
    
    # Build set of relevant keywords from user interests
    relevant_keywords = set()
    for interest in user_interests:
        relevant_keywords.update(interest_categories.get(interest, [interest]))
    
    # Score each item
    scored_items = []
    seen_fuzzy_titles = set()
    source_counts = {}
    
    for item in items:
        title_lower = (item.get("title", "") or "").lower()
        
        # Fuzzy dedup — skip items with very similar titles
        fuzzy_key = _fuzzy_title_key(title_lower)
        if fuzzy_key in seen_fuzzy_titles:
            continue
        seen_fuzzy_titles.add(fuzzy_key)
        
        score = 50  # Base score
        
        # Strong bonus for items with actual distance data (+30)
        has_distance = item.get("distance_miles") is not None and isinstance(item.get("distance_miles"), (int, float))
        if has_distance:
            score += 30
        else:
            score -= 20  # Penalize items with no location data
        
        # Interest relevance (+20 for match, +10 for partial)
        category = (item.get("category", "") or "").lower()
        description = (item.get("description", "") or "").lower()
        title_and_desc = f"{title_lower} {description} {category}"
        
        match_count = 0
        for keyword in relevant_keywords:
            if keyword in title_and_desc:
                match_count += 1
        if match_count >= 2:
            score += 25
        elif match_count == 1:
            score += 15
        
        # Distance bonus (closer is better, max +20 for very close)
        if has_distance:
            distance = item.get("distance_miles", 10)
            if distance <= 5:
                score += 15
            elif distance <= 10:
                score += 10
            elif distance <= 20:
                score += 5
            else:
                score -= min(distance - 20, 15)
        
        # Source diversity bonus (max 4 per source before penalty)
        source = item.get("feed_source") or item.get("source", "Unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
        if source_counts[source] > 4:
            score -= 8 * (source_counts[source] - 4)
        
        # Kid-friendly bonus if family group
        if group_type == "family" and item.get("kid_friendly"):
            score += 15
        elif "family" in user_interests and item.get("kid_friendly"):
            score += 10
        
        # Free events get a small bonus
        price = (item.get("price_flag", "") or "").lower()
        if price == "free":
            score += 5
        
        # Bonus for items with event dates (timely content is more actionable)
        if item.get("event_date"):
            score += 5
        
        scored_items.append((score, item))
    
    # Sort by score (descending)
    scored_items.sort(key=lambda x: -x[0])
    
    # Return top items, ensuring source diversity
    result = []
    final_source_counts = {}
    
    # Calculate max items per source based on total requested
    max_per_source_initial = max(4, max_items // 3)
    
    # First pass: add top items from each source (with diversity limit)
    for score, item in scored_items:
        source = item.get("feed_source") or item.get("source", "Unknown")
        if final_source_counts.get(source, 0) >= max_per_source_initial:
            continue
        final_source_counts[source] = final_source_counts.get(source, 0) + 1
        result.append(item)
        if len(result) >= max_items:
            break
    
    # Second pass: fill remaining slots with any high-scoring items (no source limit)
    if len(result) < max_items:
        for score, item in scored_items:
            if item in result:
                continue
            result.append(item)
            if len(result) >= max_items:
                break
    
    return result


def _detect_location_type(location_str):
    """
    Detect the type of location string.
    Returns: "specific_address", "venue_name", "city_only", "district", or "none"
    """
    if not location_str or not location_str.strip():
        return "none"
    
    loc = location_str.strip().lower()
    
    import re
    
    # Check for specific address patterns (has street number followed by street suffix)
    # Handles: "4000 Middlefield Road", "379-389 Colusa Ave", "123 Main St"
    street_suffixes = r'\b(st|street|ave|avenue|blvd|boulevard|rd|road|dr|drive|way|lane|ln|ct|court|pl|place|pkwy|parkway|cir|circle|ter|terrace|hwy|highway)\b'
    
    # Pattern 1: Number at start followed eventually by a street suffix
    # e.g., "4000 Middlefield Road, T2, Palo Alto, CA"
    if re.search(r'^[\d][\d\-]*\s+.*' + street_suffixes, loc):
        return "specific_address"
    
    # Pattern 2: Street suffix anywhere with a number nearby
    # e.g., "379-389 Colusa Ave, Kensington"
    if re.search(r'[\d][\d\-]*\s+[\w\s]+' + street_suffixes, loc):
        return "specific_address"
    
    # Pattern 3: Just has a street suffix with some words before it
    # e.g., "Colusa Ave" or "Main Street"
    if re.search(r'\w+\s+' + street_suffixes, loc):
        # But make sure it's not just a city name like "Park Ave, New York"
        # Check if there's a number somewhere
        if re.search(r'\d', loc):
            return "specific_address"
    
    # Check for district/area keywords
    district_keywords = ["district", "area", "neighborhood", "quarter", "zone"]
    if any(kw in loc for kw in district_keywords):
        return "district"
    
    # Check for city/state pattern (e.g., "Fremont, CA" or "San Francisco, California")
    if re.search(r'^[a-z\s]+,\s*[a-z]{2}$', loc) or re.search(r'^[a-z\s]+,\s*[a-z]+$', loc):
        return "city_only"
    
    # Check for venue keywords (plaza, center, park, museum, etc.)
    venue_keywords = ["plaza", "center", "centre", "park", "museum", "gallery", "theater", "theatre", 
                      "hall", "arena", "stadium", "market", "mall", "square", "building", "tower",
                      "library", "church", "temple", "pavilion", "preserve", "recreation"]
    if any(kw in loc for kw in venue_keywords):
        return "venue_name"
    
    # Default to venue_name for anything with a proper noun feel
    return "venue_name"


def normalize_feed_item_to_recommendation(item, index, user_lat, user_lng, week_str, geocode_fn=None, user_state=None):
    """
    Turn a raw feed item into the same shape as Google Places recommendations
    so they can be merged and sorted. geocode_fn(location_str) -> (lat, lng) optional.
    
    Distance/travel time handling:
    - Specific addresses: geocode and calculate exact distance
    - Venue names/districts: geocode with user's state context, show exact if found, "n/a" if not
    - City only: show as "estimated" range
    - No location: show as "n/a"
    """
    title = item.get("title", "Local event")
    link = item.get("link", "")
    source = item.get("source", "Local feed")
    location_str = item.get("location_str") or item.get("address") or ""
    # Decode HTML entities in location strings (e.g. &#124; -> |, &#039; -> ', &amp; -> &)
    try:
        import html as _html
        location_str = _html.unescape(location_str)
        title = _html.unescape(title)
    except Exception:
        pass
    lat, lng = None, None
    geocoded = False
    distance_is_estimated = False
    distance_is_na = False
    
    # Detect location type
    location_type = _detect_location_type(location_str)
    print(f"[NORMALIZE] '{title}' location_type={location_type}, location='{location_str}'")
    
    from math import radians, sin, cos, sqrt, atan2
    
    # Handle based on location type
    if location_type == "none":
        # No location info - mark as n/a
        distance_is_na = True
        lat, lng = user_lat, user_lng
        distance_miles = None
        travel_time_min = None
        print(f"[NORMALIZE] No location for '{title}' - distance/travel n/a")
        
    elif location_type == "city_only":
        # City only - try to geocode, show estimated range
        if geocode_fn and location_str:
            try:
                coords = geocode_fn(location_str)
                if coords:
                    lat, lng = coords
                    geocoded = True
            except Exception as e:
                print(f"[NORMALIZE] Geocoding failed for city '{location_str}': {e}")
        
        if geocoded:
            # Calculate distance but mark as estimated (city center, not exact venue)
            R = 3959
            lat1, lng1 = radians(user_lat), radians(user_lng)
            lat2, lng2 = radians(lat), radians(lng)
            dlat = lat2 - lat1
            dlng = lng2 - lng1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance_miles = R * c
            travel_time_min = max(5, int(round((distance_miles / 25) * 60)))
            distance_is_estimated = True
            print(f"[NORMALIZE] City-level distance for '{title}': ~{distance_miles:.1f}mi (estimated)")
        else:
            distance_is_na = True
            lat, lng = user_lat, user_lng
            distance_miles = None
            travel_time_min = None
            
    elif location_type in ("venue_name", "district", "specific_address"):
        # Try geocoding - add state context if not already present
        search_location = location_str
        
        # Clean venue names with pipe separators: "Main | Oakland Public Library" -> "Oakland Public Library"
        import re
        if '|' in search_location:
            # Take the longer part (usually the actual venue name)
            parts = [p.strip() for p in search_location.split('|')]
            search_location = max(parts, key=len)
            print(f"[NORMALIZE] Cleaned pipe separator: '{search_location}'")
        
        # Check if location already has a state abbreviation (e.g., ", CA" or ", NY")
        has_state = bool(re.search(r',\s*[A-Z]{2}\s*(\d{5})?$', location_str.upper()))
        
        if user_state and not has_state:
            # Append user's state to improve geocoding accuracy for any location type
            search_location = f"{location_str}, {user_state}"
            print(f"[NORMALIZE] Adding state context: '{search_location}'")
        
        if geocode_fn:
            try:
                print(f"[NORMALIZE] Attempting to geocode: '{search_location}'")
                coords = geocode_fn(search_location)
                if coords:
                    lat, lng = coords
                    geocoded = True
                    print(f"[NORMALIZE] Geocode SUCCESS: '{search_location}' -> ({lat}, {lng})")
                else:
                    print(f"[NORMALIZE] Geocode returned None for: '{search_location}'")
            except Exception as e:
                print(f"[NORMALIZE] Geocoding EXCEPTION for '{search_location}': {e}")
        else:
            print(f"[NORMALIZE] WARNING: No geocode_fn provided for '{title}'")
        
        if geocoded:
            # Calculate exact distance
            R = 3959
            lat1, lng1 = radians(user_lat), radians(user_lng)
            lat2, lng2 = radians(lat), radians(lng)
            dlat = lat2 - lat1
            dlng = lng2 - lng1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance_miles = R * c
            travel_time_min = max(5, int(round((distance_miles / 25) * 60)))
            print(f"[NORMALIZE] Calculated distance for '{title}': {distance_miles:.1f}mi, {travel_time_min}min")
        else:
            # Couldn't geocode - mark as n/a
            distance_is_na = True
            lat, lng = user_lat, user_lng
            distance_miles = None
            travel_time_min = None
            print(f"[NORMALIZE] Could not geocode '{search_location}' - distance/travel n/a")
    
    # Override with provided distance/travel_time if available
    if item.get("distance_miles") is not None and isinstance(item.get("distance_miles"), (int, float)):
        distance_miles = float(item["distance_miles"])
        travel_time_min = item.get("travel_time_min")
        if travel_time_min is None or not isinstance(travel_time_min, (int, float)):
            travel_time_min = max(5, int(round((distance_miles / 25) * 60)))
        else:
            travel_time_min = max(5, int(travel_time_min))
        distance_is_estimated = False
        distance_is_na = False
        if lat is None:
            lat, lng = user_lat, user_lng
    place_id = item.get("place_id") or f"feed_{hashlib.md5((link or title).encode()).hexdigest()[:12]}"
    # Use description from feed if available, otherwise generic source attribution
    description = (item.get("description") or "").strip()
    
    # Skip description crawling during initial load (adds 1 HTTP request per item, slows recommendations)
    # Crawling can be enabled by passing skip_description_crawl=False
    
    explanation = description if description else f"From {source}"
    
    # Format distance and travel time based on status
    if distance_is_na:
        distance_display = "n/a"
        travel_time_display = "n/a"
        distance_value = None
        travel_time_value = None
    elif distance_is_estimated:
        distance_display = f"~{round(distance_miles, 1)} mi (estimated)"
        travel_time_display = f"~{travel_time_min} min (estimated)"
        distance_value = round(distance_miles, 1)
        travel_time_value = travel_time_min
    else:
        distance_display = f"{round(distance_miles, 1)} mi"
        travel_time_display = f"{travel_time_min} min"
        distance_value = round(distance_miles, 1)
        travel_time_value = travel_time_min
    
    # Get event date from item (may be pub_date, start_at, date, etc.)
    event_date = item.get("pub_date") or item.get("start_at") or item.get("date") or item.get("event_date") or ""
    
    return {
        "rec_id": f"lf_{week_str}_{index}",
        "type": "event",
        "place_id": place_id,
        "title": title,
        "category": item.get("category") or "events",
        "distance_miles": distance_value,
        "travel_time_min": travel_time_value,
        "distance_display": distance_display,
        "travel_time_display": travel_time_display,
        "distance_is_estimated": distance_is_estimated,
        "distance_is_na": distance_is_na,
        "price_flag": (item.get("price_flag") or "$").strip() if isinstance(item.get("price_flag"), str) else "$",
        "kid_friendly": False,
        "indoor_outdoor": "indoor",
        "description": description,
        "explanation": explanation,
        "source_url": link,
        "event_link": link,
        "event_date": event_date,
        "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lng}" if lat and lng else link,
        "address": location_str or "",
        "rating": 0,
        "total_ratings": 0,
        "photo_url": None,
        "feed_source": source,
        "feed_item": True,
    }


# ========== NEW DATA SOURCES ==========

def fetch_yelp_places(user_lat, user_lng, radius_miles=25, categories=None, limit=15):
    """
    Fetch places from Yelp Fusion API by location and interest categories.
    Requires YELP_API_KEY env var. Free tier: 500 calls/day.
    """
    if not YELP_API_KEY or not requests:
        return []
    try:
        # Map our interest categories to Yelp categories
        interest_to_yelp = {
            "nature": "parks,hiking,gardens",
            "outdoor": "parks,hiking,beaches",
            "arts_culture": "museums,galleries,artclasses",
            "food_drink": "restaurants,cafes,bakeries",
            "food_drinks": "restaurants,cafes,bakeries",
            "fitness": "fitness,gyms,yoga",
            "sports": "active,recreation,sports_clubs",
            "learning": "libraries,museums,educationservices",
            "entertainment": "movietheaters,musicvenues,comedy",
            "shopping": "shopping,fleamarkets,bookstores",
            "nightlife": "nightlife,bars,lounges",
            "family": "kids_activities,playgrounds,zoos",
            "relaxation": "spas,hotsprings,meditation",
            "adventure": "active,rafting,climbing",
            "events": "festivals,localflavor",
        }
        yelp_cats = set()
        for interest in (categories or []):
            mapped = interest_to_yelp.get(interest, "")
            if mapped:
                yelp_cats.update(mapped.split(","))
        if not yelp_cats:
            yelp_cats = {"parks", "restaurants", "museums", "arts", "active"}

        radius_meters = min(int(radius_miles * 1609), 40000)
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
        params = {
            "latitude": user_lat,
            "longitude": user_lng,
            "radius": radius_meters,
            "categories": ",".join(list(yelp_cats)[:5]),
            "sort_by": "best_match",
            "limit": min(limit, 50),
        }
        r = requests.get(url, headers=headers, params=params, timeout=4)
        if r.status_code != 200:
            print(f"[LOCAL_FEEDS] Yelp error: {r.status_code}")
            return []
        data = r.json()
        items = []
        yelp_cat_map = {
            "parks": "nature", "hiking": "nature", "gardens": "nature", "beaches": "nature",
            "museums": "arts_culture", "galleries": "arts_culture", "artclasses": "arts_culture",
            "restaurants": "food_drink", "cafes": "food_drink", "bakeries": "food_drink",
            "fitness": "fitness", "gyms": "fitness", "yoga": "fitness",
            "kids_activities": "family", "playgrounds": "family", "zoos": "family",
            "shopping": "shopping", "bookstores": "shopping",
            "nightlife": "nightlife", "bars": "nightlife",
        }
        for biz in data.get("businesses", [])[:limit]:
            loc = biz.get("location", {})
            addr_parts = [loc.get("address1", ""), loc.get("city", ""), loc.get("state", "")]
            address = ", ".join([p for p in addr_parts if p])
            # Map first yelp category to our system
            biz_cats = [c.get("alias", "") for c in biz.get("categories", [])]
            our_cat = "events"
            for bc in biz_cats:
                if bc in yelp_cat_map:
                    our_cat = yelp_cat_map[bc]
                    break
            price_str = biz.get("price", "$") or "$"
            distance_m = biz.get("distance", 0)
            distance_mi = round(distance_m / 1609.34, 1) if distance_m else None
            items.append({
                "title": biz.get("name", ""),
                "link": biz.get("url", ""),
                "description": f"Rating: {biz.get('rating', 'N/A')}★ ({biz.get('review_count', 0)} reviews). {', '.join(biz_cats[:3])}",
                "location_str": address,
                "source": "Yelp",
                "source_url": biz.get("url", "https://www.yelp.com"),
                "category": our_cat,
                "distance_miles": distance_mi,
                "travel_time_min": max(5, int(round((distance_mi / 25) * 60))) if distance_mi else None,
                "price_flag": price_str,
                "kid_friendly": our_cat == "family" or "kids" in " ".join(biz_cats),
            })
        print(f"[LOCAL_FEEDS] Yelp: fetched {len(items)} places")
        return items
    except Exception as e:
        print(f"[LOCAL_FEEDS] Yelp error: {e}")
        return []


def fetch_ticketmaster_events(user_lat, user_lng, radius_miles=25, limit=15):
    """
    Fetch events from Ticketmaster Discovery API.
    Requires TICKETMASTER_API_KEY env var. Free tier: 5000 calls/day.
    """
    if not TICKETMASTER_API_KEY or not requests:
        return []
    try:
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        params = {
            "apikey": TICKETMASTER_API_KEY,
            "latlong": f"{user_lat},{user_lng}",
            "radius": str(min(int(radius_miles), 100)),
            "unit": "miles",
            "size": min(limit, 50),
            "sort": "date,asc",
        }
        r = requests.get(url, params=params, timeout=4)
        if r.status_code != 200:
            print(f"[LOCAL_FEEDS] Ticketmaster error: {r.status_code}")
            return []
        data = r.json()
        events = data.get("_embedded", {}).get("events", [])
        items = []
        for ev in events[:limit]:
            name = ev.get("name", "Event")
            event_url = ev.get("url", "")
            # Date
            dates = ev.get("dates", {}).get("start", {})
            event_date = dates.get("localDate", "") or dates.get("dateTime", "")
            # Venue
            venues = ev.get("_embedded", {}).get("venues", [])
            venue_name = venues[0].get("name", "") if venues else ""
            venue_addr = ""
            if venues:
                addr = venues[0].get("address", {})
                city_info = venues[0].get("city", {})
                state_info = venues[0].get("state", {})
                venue_addr = ", ".join(filter(None, [
                    addr.get("line1", ""),
                    city_info.get("name", ""),
                    state_info.get("stateCode", ""),
                ]))
            # Price
            price_ranges = ev.get("priceRanges", [])
            price_flag = "$"
            if price_ranges:
                min_price = price_ranges[0].get("min", 0)
                if min_price == 0:
                    price_flag = "free"
                elif min_price < 30:
                    price_flag = "$"
                elif min_price < 75:
                    price_flag = "$$"
                else:
                    price_flag = "$$$"
            # Image
            images = ev.get("images", [])
            image_url = images[0].get("url", "") if images else ""
            # Category from classifications
            classifications = ev.get("classifications", [])
            segment = classifications[0].get("segment", {}).get("name", "").lower() if classifications else ""
            our_cat = "events"
            if "music" in segment:
                our_cat = "entertainment"
            elif "sport" in segment:
                our_cat = "fitness"
            elif "arts" in segment or "theatre" in segment:
                our_cat = "arts_culture"
            elif "family" in segment:
                our_cat = "family"
            loc_str = f"{venue_name}, {venue_addr}" if venue_name else venue_addr
            items.append({
                "title": name,
                "link": event_url,
                "description": f"{venue_name}. {event_date}",
                "location_str": loc_str,
                "source": "Ticketmaster",
                "source_url": event_url or "https://www.ticketmaster.com",
                "category": our_cat,
                "event_date": event_date,
                "event_link": event_url,
                "price_flag": price_flag,
                "kid_friendly": our_cat == "family",
                "photo_url": image_url,
            })
        print(f"[LOCAL_FEEDS] Ticketmaster: fetched {len(items)} events")
        return items
    except Exception as e:
        print(f"[LOCAL_FEEDS] Ticketmaster error: {e}")
        return []


def fetch_osm_places(user_lat, user_lng, radius_miles=10, limit=15):
    """
    Fetch POIs from OpenStreetMap via Overpass API. No API key needed.
    Queries parks, playgrounds, museums, libraries, nature reserves, viewpoints.
    """
    if not requests:
        return []
    try:
        from math import radians, cos
        # Build bounding box from radius
        lat_delta = radius_miles / 69.0
        lng_delta = radius_miles / (69.0 * max(cos(radians(user_lat)), 0.01))
        south = user_lat - lat_delta
        north = user_lat + lat_delta
        west = user_lng - lng_delta
        east = user_lng + lng_delta

        # Overpass QL query for interesting POIs
        query = f"""
[out:json][timeout:8];
(
  node["leisure"="park"]({south},{west},{north},{east});
  node["leisure"="playground"]({south},{west},{north},{east});
  node["tourism"="museum"]({south},{west},{north},{east});
  node["amenity"="library"]({south},{west},{north},{east});
  node["leisure"="nature_reserve"]({south},{west},{north},{east});
  node["tourism"="viewpoint"]({south},{west},{north},{east});
  way["leisure"="park"]({south},{west},{north},{east});
  way["leisure"="nature_reserve"]({south},{west},{north},{east});
);
out center {limit * 3};
"""
        url = "https://overpass-api.de/api/interpreter"
        r = requests.post(url, data={"data": query}, timeout=4)
        if r.status_code != 200:
            print(f"[LOCAL_FEEDS] Overpass error: {r.status_code}")
            return []
        data = r.json()
        elements = data.get("elements", [])
        items = []
        from math import radians as rad, sin, cos as cos_f, sqrt, atan2
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name:
                continue
            # Get coordinates (node has lat/lon directly; way has center)
            lat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
            lng = el.get("lon") or (el.get("center", {}) or {}).get("lon")
            if lat is None or lng is None:
                continue
            # Calculate distance
            R = 3959
            la1, lo1 = rad(user_lat), rad(user_lng)
            la2, lo2 = rad(lat), rad(lng)
            dlat = la2 - la1
            dlng = lo2 - lo1
            a = sin(dlat / 2) ** 2 + cos_f(la1) * cos_f(la2) * sin(dlng / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            dist_mi = round(R * c, 1)
            # Map OSM tags to category
            our_cat = "nature"
            if tags.get("tourism") == "museum":
                our_cat = "arts_culture"
            elif tags.get("amenity") == "library":
                our_cat = "learning"
            elif tags.get("leisure") == "playground":
                our_cat = "family"
            elif tags.get("tourism") == "viewpoint":
                our_cat = "nature"
            addr_parts = [tags.get("addr:street", ""), tags.get("addr:city", ""), tags.get("addr:state", "")]
            address = ", ".join([p for p in addr_parts if p]) or f"{lat:.4f}, {lng:.4f}"
            gmaps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
            items.append({
                "title": name,
                "link": gmaps_url,
                "description": f"{tags.get('leisure') or tags.get('tourism') or tags.get('amenity', 'place')}",
                "location_str": address,
                "source": "OpenStreetMap",
                "source_url": gmaps_url,
                "category": our_cat,
                "distance_miles": dist_mi,
                "travel_time_min": max(5, int(round((dist_mi / 25) * 60))),
                "price_flag": "free",
                "kid_friendly": tags.get("leisure") == "playground" or our_cat == "family",
            })
        # Sort by distance, return closest
        items.sort(key=lambda x: x.get("distance_miles", 999))
        print(f"[LOCAL_FEEDS] OSM/Overpass: fetched {len(items[:limit])} places")
        return items[:limit]
    except Exception as e:
        print(f"[LOCAL_FEEDS] OSM/Overpass error: {e}")
        return []


def fetch_eventbrite_public(user_lat, user_lng, radius_miles=25, limit=10):
    """
    Scrape Eventbrite public event search page for local events.
    No API key needed — parses JSON-LD structured data from the page.
    Complement to fetch_eventbrite_events (which needs a token).
    """
    if not requests:
        return []
    try:
        import json as _json
        # Derive a location slug from coordinates via reverse geocode approximation
        # Use a simple city name approach
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
        # Try a generic location-based search
        url = f"https://www.eventbrite.com/d/united-states/events/?lat={user_lat}&lng={user_lng}&radius={int(radius_miles)}mi"
        r = requests.get(url, headers=headers, timeout=4, allow_redirects=True)
        if r.status_code != 200:
            print(f"[LOCAL_FEEDS] Eventbrite public: {r.status_code}")
            return []
        items = []
        # Parse JSON-LD structured data
        for match in re.finditer(r'<script type="application/ld\+json">\s*(\{[^<]+\})\s*</script>', r.text):
            try:
                data = _json.loads(match.group(1))
                if data.get("@type") == "Event" or data.get("@type") == "SocialEvent":
                    loc = data.get("location", {})
                    loc_str = ""
                    if isinstance(loc, dict):
                        loc_name = loc.get("name", "")
                        addr = loc.get("address", {})
                        if isinstance(addr, dict):
                            loc_str = ", ".join(filter(None, [
                                loc_name,
                                addr.get("streetAddress", ""),
                                addr.get("addressLocality", ""),
                                addr.get("addressRegion", ""),
                            ]))
                        elif isinstance(addr, str):
                            loc_str = f"{loc_name}, {addr}" if loc_name else addr
                    items.append({
                        "title": data.get("name", "Event"),
                        "link": data.get("url", ""),
                        "description": (data.get("description", "") or "")[:500],
                        "location_str": loc_str,
                        "source": "Eventbrite",
                        "source_url": data.get("url", "https://www.eventbrite.com"),
                        "category": "events",
                        "event_date": data.get("startDate", ""),
                        "price_flag": "$",
                        "kid_friendly": False,
                    })
            except (_json.JSONDecodeError, TypeError):
                continue
        # Also try parsing event cards from HTML as fallback
        if not items:
            for match in re.finditer(
                r'data-event-id="(\d+)"[^>]*>.*?<h2[^>]*>(.*?)</h2>',
                r.text, re.DOTALL
            ):
                eid = match.group(1)
                title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                if title:
                    items.append({
                        "title": title,
                        "link": f"https://www.eventbrite.com/e/{eid}",
                        "description": "",
                        "location_str": "",
                        "source": "Eventbrite",
                        "source_url": f"https://www.eventbrite.com/e/{eid}",
                        "category": "events",
                        "price_flag": "$",
                        "kid_friendly": False,
                    })
        print(f"[LOCAL_FEEDS] Eventbrite public: fetched {len(items[:limit])} events")
        return items[:limit]
    except Exception as e:
        print(f"[LOCAL_FEEDS] Eventbrite public error: {e}")
        return []


def fetch_patch_events(user_lat, user_lng, limit=10):
    """
    Fetch local news/events from Patch.com RSS feeds.
    Tries RSS feeds for Bay Area cities near the user's location.
    No API key needed.
    """
    if not requests:
        return []
    try:
        # Bay Area cities mapped to Patch slugs
        bay_area_cities = [
            (37.5485, -121.9886, "fremont"),
            (37.5297, -122.0402, "newark"),
            (37.5934, -122.0439, "union-city"),
            (37.6688, -122.0808, "hayward"),
            (37.6879, -122.0902, "castro-valley"),
            (37.8044, -122.2712, "oakland"),
            (37.8716, -122.2727, "berkeley"),
            (37.5586, -122.2711, "san-mateo"),
            (37.3382, -121.8863, "san-jose"),
            (37.4419, -122.1430, "palo-alto"),
            (37.5022, -122.2594, "redwood-city"),
            (37.4005, -122.1081, "sunnyvale"),
            (37.3688, -122.0363, "cupertino"),
            (37.3861, -122.0839, "mountain-view"),
            (37.7749, -122.4194, "san-francisco"),
        ]
        # Find closest cities
        from math import radians, sin, cos, sqrt, atan2
        city_dists = []
        for clat, clng, slug in bay_area_cities:
            R = 3959
            la1, lo1 = radians(user_lat), radians(user_lng)
            la2, lo2 = radians(clat), radians(clng)
            dlat = la2 - la1
            dlng = lo2 - lo1
            a = sin(dlat / 2) ** 2 + cos(la1) * cos(la2) * sin(dlng / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            city_dists.append((R * c, slug))
        city_dists.sort()
        # Try the 3 closest cities
        items = []
        headers = {"User-Agent": "ActivityPlanner/1.0 (Local Feeds)"}
        for _, slug in city_dists[:3]:
            rss_url = f"https://patch.com/california/{slug}/rss"
            try:
                r = requests.get(rss_url, headers=headers, timeout=4)
                if r.status_code != 200:
                    continue
                parsed = _parse_rss_or_atom(r.content, rss_url, f"Patch ({slug})")
                for item in parsed:
                    # Check if it looks like an event
                    title_lower = (item.get("title", "") or "").lower()
                    desc_lower = (item.get("description", "") or "").lower()
                    is_event = any(kw in title_lower or kw in desc_lower for kw in
                                   ["event", "festival", "fair", "concert", "show", "class",
                                    "workshop", "opening", "celebration", "market", "parade"])
                    item["source"] = f"Patch ({slug})"
                    item["source_url"] = rss_url
                    item["category"] = "events" if is_event else "local_news"
                    item["price_flag"] = "free"
                    item["kid_friendly"] = False
                    items.append(item)
            except Exception as e:
                print(f"[LOCAL_FEEDS] Patch {slug} error: {e}")
                continue
            if len(items) >= limit:
                break
        print(f"[LOCAL_FEEDS] Patch: fetched {len(items[:limit])} items")
        return items[:limit]
    except Exception as e:
        print(f"[LOCAL_FEEDS] Patch error: {e}")
        return []


def fetch_tripadvisor_places(user_lat, user_lng, radius_miles=25, limit=10):
    """
    Fetch places from TripAdvisor Content API.
    Requires TRIPADVISOR_API_KEY env var. Free tier: 5000 calls/month.
    """
    if not TRIPADVISOR_API_KEY or not requests:
        return []
    try:
        url = "https://api.content.tripadvisor.com/api/v1/location/nearby_search"
        params = {
            "latLong": f"{user_lat},{user_lng}",
            "radius": min(int(radius_miles), 50),
            "radiusUnit": "mi",
            "language": "en",
            "key": TRIPADVISOR_API_KEY,
        }
        headers = {
            "Accept": "application/json",
            "Referer": "https://www.tripadvisor.com",
        }
        r = requests.get(url, params=params, headers=headers, timeout=4)
        if r.status_code != 200:
            print(f"[LOCAL_FEEDS] TripAdvisor error: {r.status_code}")
            return []
        data = r.json()
        locations = data.get("data", [])
        items = []
        for loc in locations[:limit]:
            name = loc.get("name", "")
            if not name:
                continue
            addr = loc.get("address_obj", {})
            addr_str = ", ".join(filter(None, [
                addr.get("street1", ""),
                addr.get("city", ""),
                addr.get("state", ""),
            ]))
            distance_str = loc.get("distance", "")
            # Parse distance (e.g., "3.5")
            dist_val = None
            try:
                dist_val = float(distance_str) if distance_str else None
            except (ValueError, TypeError):
                pass
            location_id = loc.get("location_id", "")
            ta_url = f"https://www.tripadvisor.com/Attraction_Review-g{location_id}" if location_id else ""
            items.append({
                "title": name,
                "link": ta_url,
                "description": loc.get("description", "") or f"TripAdvisor listing",
                "location_str": addr_str,
                "source": "TripAdvisor",
                "source_url": ta_url or "https://www.tripadvisor.com",
                "category": "attractions",
                "distance_miles": dist_val,
                "travel_time_min": max(5, int(round((dist_val / 25) * 60))) if dist_val else None,
                "price_flag": "$",
                "kid_friendly": False,
            })
        print(f"[LOCAL_FEEDS] TripAdvisor: fetched {len(items)} places")
        return items
    except Exception as e:
        print(f"[LOCAL_FEEDS] TripAdvisor error: {e}")
        return []


def fetch_alltrails_trails(user_lat, user_lng, radius_miles=25, limit=10):
    """
    Fetch parks and trails from the National Park Service API (free, no key required
    beyond DEMO_KEY) plus SF Fun Cheap events for outdoor/nature activities.
    Replaces AllTrails scraping which returns 403.
    """
    if not requests:
        return []
    items = []

    # Source 1: NPS API — national/state parks in California
    try:
        NPS_KEY = os.environ.get("NPS_API_KEY", "DEMO_KEY")
        r = requests.get(
            "https://developer.nps.gov/api/v1/parks",
            params={"stateCode": "CA", "limit": 50, "api_key": NPS_KEY},
            headers={"User-Agent": "ActivityPlanner/1.0"},
            timeout=4,
        )
        if r.status_code == 200:
            from math import radians, sin, cos, sqrt, atan2
            data = r.json()
            parks = data.get("data", [])
            for park in parks:
                name = park.get("fullName", "")
                if not name:
                    continue
                plat = float(park.get("latitude") or 0)
                plng = float(park.get("longitude") or 0)
                if plat == 0 and plng == 0:
                    continue
                # Calculate distance
                R = 3959
                la1, lo1 = radians(user_lat), radians(user_lng)
                la2, lo2 = radians(plat), radians(plng)
                dlat = la2 - la1
                dlng = lo2 - lo1
                a = sin(dlat / 2) ** 2 + cos(la1) * cos(la2) * sin(dlng / 2) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                dist = R * c
                if dist > radius_miles:
                    continue
                travel_min = max(5, int(round((dist / 25) * 60)))
                addresses = park.get("addresses", [])
                addr = ""
                if addresses:
                    a0 = addresses[0]
                    addr = f"{a0.get('line1', '')}, {a0.get('city', '')}, {a0.get('stateCode', '')}".strip(", ")
                desc = (park.get("description") or "")[:300]
                activities = [a.get("name", "") for a in park.get("activities", [])[:5]]
                if activities:
                    desc += f" Activities: {', '.join(activities)}"
                items.append({
                    "title": name,
                    "link": park.get("url", ""),
                    "description": desc,
                    "location_str": addr or f"{park.get('states', 'CA')}",
                    "source": "National Park Service",
                    "source_url": park.get("url", "https://www.nps.gov"),
                    "category": "nature",
                    "distance_miles": round(dist, 1),
                    "travel_time_min": travel_min,
                    "price_flag": "free" if not park.get("entranceFees") or (park["entranceFees"][0].get("cost", "0") in ("0", "0.00", "0.0000")) else "$",
                    "kid_friendly": True,
                })
            items.sort(key=lambda x: x.get("distance_miles", 999))
            print(f"[LOCAL_FEEDS] NPS: {len(items)} parks within {radius_miles}mi")
        else:
            print(f"[LOCAL_FEEDS] NPS API: {r.status_code}")
    except Exception as e:
        print(f"[LOCAL_FEEDS] NPS error: {e}")

    # Source 2: SF Fun Cheap RSS — free/cheap outdoor events
    try:
        r2 = requests.get(
            "https://sf.funcheap.com/feed/",
            headers={"User-Agent": "ActivityPlanner/1.0"},
            timeout=4,
        )
        if r2.status_code == 200:
            parsed = _parse_rss_or_atom(r2.content, "https://sf.funcheap.com/feed/", "SF Fun Cheap")
            for item in parsed[:15]:
                title = item.get("title", "")
                # Filter for outdoor/nature/park related events
                title_lower = title.lower()
                outdoor_keywords = ["park", "hike", "trail", "garden", "beach", "nature", "walk", "outdoor", "bike", "farm"]
                if any(kw in title_lower for kw in outdoor_keywords):
                    item["category"] = "nature"
                else:
                    item["category"] = "events"
                item["source"] = "SF Fun Cheap"
                item["price_flag"] = "free"
                item["kid_friendly"] = "kid" in title_lower or "family" in title_lower or "free" in title_lower
                items.append(item)
            print(f"[LOCAL_FEEDS] SF Fun Cheap: {len(parsed)} events")
        else:
            print(f"[LOCAL_FEEDS] SF Fun Cheap: {r2.status_code}")
    except Exception as e:
        print(f"[LOCAL_FEEDS] SF Fun Cheap error: {e}")

    print(f"[LOCAL_FEEDS] AllTrails/nature: fetched {len(items[:limit])} total items")
    return items[:limit]


def fetch_parks_rec_events(user_lat, user_lng, radius_miles=25, limit=10):
    """
    Fetch community events from working Bay Area RSS feeds.
    Replaces broken city Parks & Rec feeds (most return 403/404) with
    reliable sources: SF Fun Cheap, SF Parks Alliance, and local library feeds.
    No API key needed.
    """
    if not requests:
        return []
    items = []

    # Working Bay Area community event RSS feeds
    community_feeds = [
        ("SF Fun Cheap", "https://sf.funcheap.com/feed/"),
        ("SF Parks Alliance", "https://www.sfparksalliance.org/feed"),
    ]

    headers = {"User-Agent": "ActivityPlanner/1.0 (Local Feeds)"}

    for source_name, feed_url in community_feeds:
        try:
            r = requests.get(feed_url, headers=headers, timeout=4, allow_redirects=True)
            if r.status_code != 200:
                print(f"[LOCAL_FEEDS] {source_name}: {r.status_code}")
                continue
            parsed = _parse_rss_or_atom(r.content, feed_url, source_name)
            for item in parsed:
                title_lower = (item.get("title") or "").lower()
                item["source"] = source_name
                item["source_url"] = feed_url
                item["category"] = "events"
                item["price_flag"] = "free" if ("free" in title_lower or source_name == "SF Fun Cheap") else "$"
                item["kid_friendly"] = any(kw in title_lower for kw in ["family", "kid", "children", "park"])
                if not item.get("location_str"):
                    item["location_str"] = "San Francisco, CA"
                items.append(item)
            print(f"[LOCAL_FEEDS] {source_name}: {len(parsed)} items")
        except Exception as e:
            print(f"[LOCAL_FEEDS] {source_name} error: {e}")
            continue

    print(f"[LOCAL_FEEDS] Parks & Rec/Community: fetched {len(items[:limit])} events")
    return items[:limit]


def get_local_feed_config():
    """
    Read config from environment.
    LOCAL_FEED_URLS: comma-separated RSS/Atom URLs (e.g. https://api.axios.com/feed/top/)
    LOCAL_FEED_LABELS: optional comma-separated labels (same order as URLs)
    FACEBOOK_ACCESS_TOKEN: optional token for Facebook events
    EVENTBRITE_TOKEN: optional token for Eventbrite
    YELP_API_KEY: optional Yelp Fusion API key
    TICKETMASTER_API_KEY: optional Ticketmaster Discovery API key
    TRIPADVISOR_API_KEY: optional TripAdvisor Content API key
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
        "yelp_api_key": YELP_API_KEY,
        "ticketmaster_api_key": TICKETMASTER_API_KEY,
        "tripadvisor_api_key": TRIPADVISOR_API_KEY,
        "osm_overpass": True,  # Always available (no key needed)
        "eventbrite_public": True,  # Always available (scraping)
        "patch": True,  # Always available (RSS)
        "alltrails": True,  # Always available (scraping)
        "parks_rec": True,  # Always available (RSS)
    }


def get_local_feed_recommendations(profile, user_lat, user_lng, geocode_fn=None, max_items=5,
                                   max_travel_min=None, max_radius_miles=None, week_str=None):
    """
    Fetch from all configured local feeds, normalize to recommendation items,
    rank by relevance, filter by travel/radius, and return top items.
    
    Sources:
    - Luma (lu.ma events)
    - Meetup (local meetups)
    - 510families.com (family events - East Bay)
    - Eventbrite (ticketed events)
    - Facebook events (if token provided)
    - RSS/Atom feeds (if configured)
    """
    from datetime import datetime
    week_str = week_str or f"{datetime.now().year}-{datetime.now().isocalendar()[1]:02d}"
    config = get_local_feed_config()
    raw_items = []
    radius_miles = max_radius_miles or 25
    user_interests = (profile or {}).get("interests", [])

    print(f"[LOCAL_FEEDS] Fetching from all sources for ({user_lat}, {user_lng}), radius={radius_miles}mi (parallel)")

    def _fetch_luma():
        try:
            return fetch_luma_events(user_lat, user_lng, radius_miles=radius_miles, limit=20)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Luma error: {e}")
            return []

    def _fetch_meetup():
        try:
            return fetch_meetup_events(user_lat, user_lng, radius_miles=radius_miles, limit=20)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Meetup error: {e}")
            return []

    def _fetch_510families():
        try:
            return fetch_510families_events(limit=20)
        except Exception as e:
            print(f"[LOCAL_FEEDS] 510families error: {e}")
            return []

    def _fetch_eventbrite():
        if not config.get("eventbrite_token"):
            return []
        try:
            radius_km = radius_miles * 1.609
            return fetch_eventbrite_events(user_lat, user_lng, min(radius_km, 50), config["eventbrite_token"], limit=20)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Eventbrite error: {e}")
            return []

    def _fetch_facebook():
        if not config.get("facebook_token"):
            return []
        try:
            radius_m = radius_miles * 1609
            return fetch_facebook_events_near(user_lat, user_lng, min(int(radius_m), 50000), config["facebook_token"], limit=20)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Facebook error: {e}")
            return []

    def _fetch_rss():
        if not config.get("feed_configs"):
            return []
        try:
            return fetch_all_rss_feeds(config["feed_configs"], timeout=4)
        except Exception as e:
            print(f"[LOCAL_FEEDS] RSS error: {e}")
            return []

    def _fetch_yelp():
        if not YELP_API_KEY:
            return []
        try:
            return fetch_yelp_places(user_lat, user_lng, radius_miles=radius_miles, categories=user_interests, limit=15)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Yelp error: {e}")
            return []

    def _fetch_ticketmaster():
        if not TICKETMASTER_API_KEY:
            return []
        try:
            return fetch_ticketmaster_events(user_lat, user_lng, radius_miles=radius_miles, limit=15)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Ticketmaster error: {e}")
            return []

    def _fetch_osm():
        try:
            return fetch_osm_places(user_lat, user_lng, radius_miles=min(radius_miles, 15), limit=15)
        except Exception as e:
            print(f"[LOCAL_FEEDS] OSM error: {e}")
            return []

    def _fetch_eventbrite_pub():
        if config.get("eventbrite_token"):
            return []  # Skip public scraping when we have the API token
        try:
            return fetch_eventbrite_public(user_lat, user_lng, radius_miles=radius_miles, limit=10)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Eventbrite public error: {e}")
            return []

    def _fetch_patch():
        try:
            return fetch_patch_events(user_lat, user_lng, limit=10)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Patch error: {e}")
            return []

    def _fetch_tripadvisor():
        if not TRIPADVISOR_API_KEY:
            return []
        try:
            return fetch_tripadvisor_places(user_lat, user_lng, radius_miles=radius_miles, limit=10)
        except Exception as e:
            print(f"[LOCAL_FEEDS] TripAdvisor error: {e}")
            return []

    def _fetch_alltrails():
        try:
            return fetch_alltrails_trails(user_lat, user_lng, limit=10)
        except Exception as e:
            print(f"[LOCAL_FEEDS] AllTrails error: {e}")
            return []

    def _fetch_parks_rec():
        try:
            return fetch_parks_rec_events(user_lat, user_lng, limit=10)
        except Exception as e:
            print(f"[LOCAL_FEEDS] Parks & Rec error: {e}")
            return []

    # Fetch all sources in parallel (max wait = slowest source, not sum of all)
    # Removed known-broken sources: _fetch_patch (0 results), _fetch_alltrails (403),
    # _fetch_parks_rec (dead RSS feeds), _fetch_meetup (404 API change),
    # _fetch_eventbrite_pub (JS-rendered, returns page headers not events)
    tasks = [
        _fetch_luma, _fetch_510families, _fetch_eventbrite, _fetch_facebook, _fetch_rss,
        _fetch_yelp, _fetch_ticketmaster, _fetch_osm,
        _fetch_tripadvisor,
    ]
    # Early return: stop waiting after 5s so we return fast with available results.
    FETCH_TIMEOUT = 5
    with ThreadPoolExecutor(max_workers=min(16, len(tasks))) as executor:
        futures = {executor.submit(t): t.__name__ for t in tasks}
        try:
            for future in as_completed(futures, timeout=FETCH_TIMEOUT):
                try:
                    items = future.result()
                    raw_items.extend(items)
                    name = futures.get(future, "unknown")
                    if items:
                        print(f"[LOCAL_FEEDS] {name}: {len(items)} items")
                except Exception as e:
                    print(f"[LOCAL_FEEDS] Parallel fetch error: {e}")
        except TimeoutError:
            print(f"[LOCAL_FEEDS] Fetch timeout ({FETCH_TIMEOUT}s) - returning {len(raw_items)} items from completed sources")

    print(f"[LOCAL_FEEDS] Total raw items from all sources: {len(raw_items)}")

    if not raw_items:
        return []

    # Cap items to normalize to avoid slow geocoding when many sources return data
    MAX_RAW_TO_PROCESS = 60
    if len(raw_items) > MAX_RAW_TO_PROCESS:
        raw_items = raw_items[:MAX_RAW_TO_PROCESS]
        print(f"[LOCAL_FEEDS] Capped to {MAX_RAW_TO_PROCESS} items for faster processing")

    # Extract user's state from their location for geocoding context
    user_state = None
    loc = (profile or {}).get("location", {})
    if isinstance(loc, dict):
        addr = loc.get("formatted_address") or loc.get("input") or ""
        # Try to extract state from address (e.g., "Fremont, CA" or "123 Main St, Fremont, CA 94536")
        import re
        state_match = re.search(r',\s*([A-Z]{2})\s*\d{0,5}', addr.upper())
        if state_match:
            user_state = state_match.group(1)
        elif re.search(r',\s*California', addr, re.IGNORECASE):
            user_state = "CA"
        print(f"[LOCAL_FEEDS] Extracted user state: {user_state} from '{addr}'")

    # Normalize to recommendation shape and filter by distance/travel
    recs = []
    for i, item in enumerate(raw_items):
        rec = normalize_feed_item_to_recommendation(
            item, i, user_lat, user_lng, week_str, geocode_fn=geocode_fn, user_state=user_state
        )
        # Preserve kid_friendly from source if present
        if item.get("kid_friendly"):
            rec["kid_friendly"] = True
        # Filter by travel time/distance (skip items with n/a since we can't verify)
        travel_time = rec.get("travel_time_min")
        distance = rec.get("distance_miles")
        if max_travel_min is not None and travel_time is not None and travel_time > max_travel_min:
            continue
        if max_radius_miles is not None and distance is not None and distance > max_radius_miles:
            continue
        recs.append(rec)
    
    print(f"[LOCAL_FEEDS] After filtering: {len(recs)} items")
    
    # Get group_type from profile for family filtering
    group_type = (profile or {}).get("group_type")
    
    # Rank and deduplicate, ensuring source diversity and family-appropriateness
    ranked_recs = rank_and_dedupe_recommendations(
        recs, 
        user_interests=user_interests, 
        max_items=max_items,
        group_type=group_type
    )
    
    print(f"[LOCAL_FEEDS] Returning top {len(ranked_recs)} ranked recommendations")
    return ranked_recs
