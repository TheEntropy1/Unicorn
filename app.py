from flask import Flask, render_template, request, redirect, url_for, Response
import requests
import difflib
import re

app = Flask(__name__)
TMDB_API_KEY = "483a8d6b53d5bb68c110d2c17aa6d725"

# --- TMDB API Helper Functions ---

def search_tmdb(query):
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(url)
    return response.json().get('results', [])

def get_movie_details(tmdb_id, media_type='movie'):
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    return response.json()

def get_trending_movies():
    url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    return response.json().get('results', [])

def get_trending_series():
    url = f"https://api.themoviedb.org/3/trending/tv/week?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    return response.json().get('results', [])

def get_trending_anime():
    url = f"https://api.themoviedb.org/3/discover/tv?api_key={TMDB_API_KEY}&with_genres=16"
    response = requests.get(url)
    return response.json().get('results', [])

# --- Device Detection Helper ---
def is_mobile():
    ua = request.user_agent.string.lower()
    return any(device in ua for device in ['iphone', 'android', 'mobile', 'ipad'])

# --- Routes ---

@app.route('/')
def home():
    trending_movies = get_trending_movies()[:6]
    trending_series = get_trending_series()[:6]
    trending_anime = get_trending_anime()[:6]
    template = 'home_mobile.html' if is_mobile() else 'home_desktop.html'
    return render_template(template, movies=trending_movies, series=trending_series, anime=trending_anime)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    results = search_tmdb(query)
    if not results:
        all_titles = [r['title'] for r in search_tmdb(' ')]
        corrected = difflib.get_close_matches(query, all_titles, n=1, cutoff=0.6)
        if corrected:
            results = search_tmdb(corrected[0])
    template = 'search_mobile.html' if is_mobile() else 'search_desktop.html'
    return render_template(template, results=results)

@app.route('/watch/<media_type>/<int:tmdb_id>')
def watch(media_type, tmdb_id):
    details = get_movie_details(tmdb_id, media_type)
    template = 'watch_mobile.html' if is_mobile() else 'watch_desktop.html'
    return render_template(template, details=details, media_type=media_type, tmdb_id=tmdb_id)

# --- Proxy Route with Ad Removal ---
@app.route('/proxy/embed/<media_type>/<int:tmdb_id>/<int:ep>')
def proxy_embed(media_type, tmdb_id, ep):
    url = f"https://vidsrc.to/embed/{media_type}/{tmdb_id}?episode={ep}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://vidsrc.to/"
    }
    upstream = requests.get(url, headers=headers)
    content = upstream.text

    # --- Ad Removal Filters ---
    ad_filtered = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)
    ad_filtered = re.sub(r'<!--.*?-->', '', ad_filtered, flags=re.DOTALL)
    ad_filtered = re.sub(r'<iframe.*?ads.*?>.*?</iframe>', '', ad_filtered, flags=re.DOTALL)

    return Response(ad_filtered, content_type='text/html')

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)
