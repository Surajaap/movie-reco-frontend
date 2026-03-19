import requests
import streamlit as st
 
# ── Config ──
API_BASE = "https://YOUR_RAILWAY_URL.up.railway.app"  # ← Railway URL yahan lagao
 
st.set_page_config(page_title="🎬 Movie Recommender", page_icon="🎬", layout="wide")
 
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; max-width: 1300px; }
.movie-title { font-size: 0.85rem; margin-top: 4px; line-height: 1.2; height: 2.4rem; overflow: hidden; }
.stButton > button { width: 100%; font-size: 0.75rem; padding: 4px; }
</style>
""", unsafe_allow_html=True)
 
# ── Session State ──
if "page" not in st.session_state:
    st.session_state.page = "home"
if "tmdb_id" not in st.session_state:
    st.session_state.tmdb_id = None
 
 
def go_home():
    st.session_state.page = "home"
    st.rerun()
 
 
def go_details(tmdb_id):
    st.session_state.tmdb_id = int(tmdb_id)
    st.session_state.page = "details"
    st.rerun()
 
 
# ── API Helper ──
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None
 
 
# ── Poster Grid ──
def show_grid(movies, cols=5, key_prefix="grid"):
    if not movies:
        st.info("Koi movie nahi mili.")
        return
    rows = (len(movies) + cols - 1) // cols
    idx = 0
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(movies):
                break
            m = movies[idx]
            idx += 1
            with colset[c]:
                poster = m.get("poster_url")
                if poster:
                    st.image(poster, use_column_width=True)
                else:
                    st.write("🖼️")
                tmdb_id = m.get("tmdb_id")
                if tmdb_id and st.button("Open", key=f"{key_prefix}_{r}_{c}_{idx}"):
                    go_details(tmdb_id)
                st.markdown(f"<div class='movie-title'>{m.get('title','')}</div>", unsafe_allow_html=True)
 
 
# ═══════════════════════════
# SIDEBAR
# ═══════════════════════════
with st.sidebar:
    st.title("🎬 Movie Recommender")
    if st.button("🏠 Home"):
        go_home()
    st.markdown("---")
    category = st.selectbox(
        "Home Feed",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"],
    )
    cols = st.slider("Grid Columns", 3, 7, 5)
 
 
# ═══════════════════════════
# PAGE: HOME
# ═══════════════════════════
if st.session_state.page == "home":
    st.title("🎬 Movie Recommender")
 
    # Search bar
    query = st.text_input("🔍 Movie Search karo", placeholder="e.g. Avengers, Batman...")
 
    if query.strip():
        results = api_get("/search", params={"query": query.strip()})
        if results:
            st.markdown("### Search Results")
            options = {f"{m['title']} ({m.get('release_date','')[:4]})": m["tmdb_id"] for m in results if m.get("tmdb_id")}
            selected = st.selectbox("Movie chuno:", ["-- Select --"] + list(options.keys()))
            if selected != "-- Select --":
                go_details(options[selected])
            show_grid(results, cols=cols, key_prefix="search")
        else:
            st.warning("Koi result nahi mila.")
    else:
        # Home feed
        st.markdown(f"### 🏠 {category.replace('_',' ').title()}")
        movies = api_get("/home", params={"category": category, "limit": 20})
        if movies:
            show_grid(movies, cols=cols, key_prefix="home")
        else:
            st.error("Home feed load nahi ho raha. Backend check karo.")
 
 
# ═══════════════════════════
# PAGE: DETAILS
# ═══════════════════════════
elif st.session_state.page == "details":
    tmdb_id = st.session_state.tmdb_id
 
    if st.button("← Back"):
        go_home()
 
    # Movie details
    movie = api_get(f"/movie/{tmdb_id}")
    if not movie:
        st.error("Movie details nahi mila.")
        st.stop()
 
    # Layout
    left, right = st.columns([1, 2.5], gap="large")
 
    with left:
        if movie.get("poster_url"):
            st.image(movie["poster_url"], use_column_width=True)
 
    with right:
        st.markdown(f"## {movie.get('title', '')}")
        genres = ", ".join([g["name"] for g in movie.get("genres", [])]) or "-"
        st.markdown(f"**Release:** {movie.get('release_date', '-')}")
        st.markdown(f"**Genres:** {genres}")
        st.markdown(f"**Rating:** ⭐ {movie.get('vote_average', '-')}")
        st.markdown("---")
        st.markdown("### Overview")
        st.write(movie.get("overview") or "Overview nahi hai.")
 
    if movie.get("backdrop_url"):
        st.image(movie["backdrop_url"], use_column_width=True)
 
    st.divider()
 
    # Recommendations
    st.markdown("### 🎯 Similar Movies (TF-IDF)")
    recs = api_get(f"/recommend/{tmdb_id}", params={"top_n": 10})
    if recs:
        show_grid(recs, cols=cols, key_prefix="recs")
    else:
        st.info("Is movie ke liye recommendations nahi mili.")