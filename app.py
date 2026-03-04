import requests
import streamlit as st

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-rec-466x.onrender.com" or "http://127.0.0.1:8000"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", page_icon="🍿", layout="wide")

# =============================
# STYLES (minimal modern)
# =============================
st.markdown(
    """
<style>
/* Import Premium Web Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global Styles & Typography */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Base App Background (Subtle Gradient Light Mode) */
.stApp {
    background: linear-gradient(135deg, #f3f4f6 0%, #ffffff 100%);
    color: #111827;
}

/* Refined Block Container */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* Hide Default Streamlit Elements to make it feel like a real web app */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Custom Scrollbar for a polished feel */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background-color: #94a3b8;
}

/* Typography Helpers */
.small-muted {
    color: #64748b;
    font-size: 0.95rem;
    font-weight: 400;
    line-height: 1.5;
}

.movie-title {
    font-size: 0.95rem;
    font-weight: 600;
    line-height: 1.3;
    height: 2.6rem; /* Allow exactly two lines */
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    margin-top: 0.5rem;
    color: #0f172a;
}

/* Premium Card (Glassmorphism + Smooth Hover) */
.card {
    border: 1px solid rgba(255, 255, 255, 0.4);
    border-radius: 20px;
    padding: 24px;
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 4px 24px -4px rgba(0, 0, 0, 0.04);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.1);
}

/* Interactive Elements (Buttons & Posters) Transitions */
.stButton>button {
    border-radius: 12px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    background-color: #f1f5f9 !important; /* Lighter button background for contrast */
    color: #1e293b !important;
    border: 1px solid #cbd5e1 !important;
}

.stButton>button:hover {
    background-color: #e2e8f0 !important;
    border-color: #94a3b8 !important;
    color: #0f172a !important;
}

/* Target images inside columns for hover effect */
div[data-testid="stImage"] img {
    border-radius: 12px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

div[data-testid="stImage"] img:hover {
    transform: scale(1.03);
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

/* Clean up select boxes and inputs */
/* Target the actual input fields and select box backgrounds */
div[data-baseweb="select"] > div, 
input[class^="st-"] {
    border-radius: 8px !important;
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #cbd5e1 !important;
}

/* Ensure text inside dropdowns is dark */
div[data-baseweb="popover"] {
    background-color: #ffffff !important;
    color: #0f172a !important;
}
li[role="option"] {
    color: #0f172a !important;
}

/* Divider Styling */
hr {
    border-top: 1px solid rgba(0,0,0,0.06);
    margin-top: 2rem;
    margin-bottom: 2rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# STATE + ROUTING (single-file pages)
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"  # home | details
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

qp_view = st.query_params.get("view")
qp_id = st.query_params.get("id")
if qp_view in ("home", "details"):
    st.session_state.view = qp_view
if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except:
        pass


def goto_home():
    st.session_state.view = "home"
    st.query_params["view"] = "home"
    if "id" in st.query_params:
        del st.query_params["id"]
    st.rerun()


def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.query_params["view"] = "details"
    st.query_params["id"] = str(int(tmdb_id))
    st.rerun()


# =============================
# API HELPERS
# =============================
@st.cache_data(ttl=30)  # short cache for autocomplete
def api_get_json(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"


def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies to show.")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break
            m = cards[idx]
            idx += 1

            tmdb_id = m.get("tmdb_id")
            title = m.get("title", "Untitled")
            poster = m.get("poster_url")

            with colset[c]:
                if poster:
                    st.image(poster, use_container_width=True)
                else:
                    st.write("🖼️ No poster")

                if st.button("Open", key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}"):
                    if tmdb_id:
                        goto_details(tmdb_id)

                st.markdown(
                    f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True
                )


def to_cards_from_tfidf_items(tfidf_items):
    cards = []
    for x in tfidf_items or []:
        tmdb = x.get("tmdb") or {}
        if tmdb.get("tmdb_id"):
            cards.append(
                {
                    "tmdb_id": tmdb["tmdb_id"],
                    "title": tmdb.get("title") or x.get("title") or "Untitled",
                    "poster_url": tmdb.get("poster_url"),
                }
            )
    return cards


# =============================
# IMPORTANT: Robust TMDB search parsing
# Supports BOTH API shapes:
# 1) raw TMDB: {"results":[{id,title,poster_path,...}]}
# 2) list cards: [{tmdb_id,title,poster_url,...}]
# =============================
def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    """
    Returns:
      suggestions: list[(label, tmdb_id)]
      cards: list[{tmdb_id,title,poster_url}]
    """
    keyword_l = keyword.strip().lower()

    # A) If API returns dict with 'results'
    if isinstance(data, dict) and "results" in data:
        raw = data.get("results") or []
        raw_items = []
        for m in raw:
            title = (m.get("title") or "").strip()
            tmdb_id = m.get("id")
            poster_path = m.get("poster_path")
            if not title or not tmdb_id:
                continue
            raw_items.append(
                {
                    "tmdb_id": int(tmdb_id),
                    "title": title,
                    "poster_url": f"{TMDB_IMG}{poster_path}" if poster_path else None,
                    "release_date": m.get("release_date", ""),
                }
            )

    # B) If API returns already as list
    elif isinstance(data, list):
        raw_items = []
        for m in data:
            # might be {tmdb_id,title,poster_url}
            tmdb_id = m.get("tmdb_id") or m.get("id")
            title = (m.get("title") or "").strip()
            poster_url = m.get("poster_url")
            if not title or not tmdb_id:
                continue
            raw_items.append(
                {
                    "tmdb_id": int(tmdb_id),
                    "title": title,
                    "poster_url": poster_url,
                    "release_date": m.get("release_date", ""),
                }
            )
    else:
        return [], []

    # Word-match filtering (contains)
    matched = [x for x in raw_items if keyword_l in x["title"].lower()]

    # If nothing matched, fallback to raw list (so never blank)
    final_list = matched if matched else raw_items

    # Suggestions = top 10 labels
    suggestions = []
    for x in final_list[:10]:
        year = (x.get("release_date") or "")[:4]
        label = f"{x['title']} ({year})" if year else x["title"]
        suggestions.append((label, x["tmdb_id"]))

    # Cards = top N
    cards = [
        {"tmdb_id": x["tmdb_id"], "title": x["title"], "poster_url": x["poster_url"]}
        for x in final_list[:limit]
    ]
    return suggestions, cards


# =============================
# =============================
# HEADER & HERO SECTION
# =============================
st.markdown(
    """
    <div style='text-align: center; padding: 2rem 0 3rem 0;'>
        <h1 style='font-weight: 700; font-size: 3rem; letter-spacing: -1px; margin-bottom: 0.5rem; background: -webkit-linear-gradient(45deg, #FF6B6B, #556270); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            Movie Recommender
        </h1>
        <p style='color: #64748b; font-size: 1.1rem; max-width: 600px; margin: 0 auto; line-height: 1.6;'>
            Discover your next favorite film. Type a keyword, explore suggestions, and unlock personalized recommendations.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# VIEW: HOME
# ==========================================================

# Initialize defaults if sidebar is gone
if "home_category" not in st.session_state:
    st.session_state.home_category = "trending"
if "grid_cols" not in st.session_state:
    st.session_state.grid_cols = 6

if st.session_state.view == "home":
    
    # Top controls for view configuration
    a, b = st.columns([1, 1])
    with a:
        st.session_state.home_category = st.selectbox(
            "Home Feed Category",
            ["trending", "popular", "top_rated", "now_playing", "upcoming"],
            index=["trending", "popular", "top_rated", "now_playing", "upcoming"].index(st.session_state.home_category)
        )
    with b:
        st.session_state.grid_cols = st.slider("Grid Columns", 4, 8, st.session_state.grid_cols)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Wrap search in a container for better spacing
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        typed = st.text_input(
            "🔎 Search Movies", 
            placeholder="e.g. Inception, Batman, Interstellar...", 
            label_visibility="collapsed"
        )
    
    st.markdown("<br><br>", unsafe_allow_html=True)

    # SEARCH MODE (Autocomplete + word-match results)
    if typed.strip():
        if len(typed.strip()) < 2:
            st.caption("Type at least 2 characters for suggestions.")
        else:
            data, err = api_get_json("/tmdb/search", params={"query": typed.strip()})

            if err or data is None:
                st.error(f"Search failed: {err}")
            else:
                suggestions, cards = parse_tmdb_search_to_cards(
                    data, typed.strip(), limit=24
                )

                # Dropdown
                if suggestions:
                    labels = ["-- Select a movie --"] + [s[0] for s in suggestions]
                    selected = st.selectbox("Suggestions", labels, index=0)

                    if selected != "-- Select a movie --":
                        # map label -> id
                        label_to_id = {s[0]: s[1] for s in suggestions}
                        goto_details(label_to_id[selected])
                else:
                    st.info("No suggestions found. Try another keyword.")

                st.markdown("### Results")
                poster_grid(cards, cols=st.session_state.grid_cols, key_prefix="search_results")

        st.stop()

    # HOME FEED MODE
    st.markdown(f"### 🏠 Home — {st.session_state.home_category.replace('_',' ').title()}")

    home_cards, err = api_get_json(
        "/home", params={"category": st.session_state.home_category, "limit": 24}
    )
    if err or not home_cards:
        st.error(f"Home feed failed: {err or 'Unknown error'}")
        st.stop()

    poster_grid(home_cards, cols=st.session_state.grid_cols, key_prefix="home_feed")

# ==========================================================
# VIEW: DETAILS
# ==========================================================
elif st.session_state.view == "details":
    tmdb_id = st.session_state.selected_tmdb_id
    if not tmdb_id:
        st.warning("No movie selected.")
        if st.button("← Back to Home"):
            goto_home()
        st.stop()

    # Top bar
    st.markdown("<br>", unsafe_allow_html=True)
    a, b = st.columns([10, 1])
    with b:
        if st.button("← Back", use_container_width=True):
            goto_home()

    # Details (your FastAPI safe route)
    data, err = api_get_json(f"/movie/id/{tmdb_id}")
    if err or not data:
        st.error(f"Could not load details: {err or 'Unknown error'}")
        st.stop()

    # Layout: Poster LEFT, Details RIGHT
    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1, 2.4], gap="large")

    with left:
        st.markdown("<div class='card' style='padding: 1rem;'>", unsafe_allow_html=True)
        if data.get("poster_url"):
            st.image(data["poster_url"], use_container_width=True)
        else:
            st.write("🖼️ No poster")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='margin-top: 0; padding-top: 0;'>{data.get('title','')}</h2>", unsafe_allow_html=True)
        release = data.get("release_date") or "-"
        genres = ", ".join([g["name"] for g in data.get("genres", [])]) or "-"
        st.markdown(
            f"<div class='small-muted' style='margin-bottom: 0.5rem;'>📅 Release: {release}</div>", unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='small-muted' style='margin-bottom: 1.5rem;'>🎭 Genres: {genres}</div>", unsafe_allow_html=True
        )
        st.markdown("#### Overview")
        st.markdown(f"<div style='line-height: 1.6; color: #334155;'>{data.get('overview') or 'No overview available.'}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if data.get("backdrop_url"):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🖼️ Backdrop")
        st.image(data["backdrop_url"], use_container_width=True)

    st.markdown("<hr style='margin: 4rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom: 2rem;'>✨ Recommended For You</h3>", unsafe_allow_html=True)

    # Recommendations (TF-IDF + Genre) via your bundle endpoint
    title = (data.get("title") or "").strip()
    if title:
        bundle, err2 = api_get_json(
            "/movie/search",
            params={"query": title, "tfidf_top_n": 12, "genre_limit": 12},
        )

        if not err2 and bundle:
            print("DEBUG BUNDLE KEYS:", bundle.keys())
            print("DEBUG TFIDF LEN:", len(bundle.get("tfidf_recommendations", [])))
            print("DEBUG GENRE LEN:", len(bundle.get("genre_recommendations", [])))
            st.markdown("#### 🔎 Similar Movies (TF-IDF)")
            poster_grid(
                to_cards_from_tfidf_items(bundle.get("tfidf_recommendations")),
                cols=st.session_state.grid_cols,
                key_prefix="details_tfidf",
            )

            st.markdown("#### 🎭 More Like This (Genre)")
            poster_grid(
                bundle.get("genre_recommendations", []),
                cols=st.session_state.grid_cols,
                key_prefix="details_genre",
            )
        else:
            st.info("Showing Genre recommendations (fallback).")
            genre_only, err3 = api_get_json(
                "/recommend/genre", params={"tmdb_id": tmdb_id, "limit": 18}
            )
            if not err3 and genre_only:
                poster_grid(
                    genre_only, cols=st.session_state.grid_cols, key_prefix="details_genre_fallback"
                )
            else:
                st.warning("No recommendations available right now.")
    else:
        st.warning("No title available to compute recommendations.")
