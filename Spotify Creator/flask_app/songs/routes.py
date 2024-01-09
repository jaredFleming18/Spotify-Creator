import base64,io
from io import BytesIO
from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import current_user

from .. import movie_client
from ..forms import PlaylistForm, SearchForm
from ..models import User, Playlist
from ..utils import current_time

from dotenv import load_dotenv
import os
import base64
import json
from requests import post, get

songs = Blueprint("songs", __name__)
""" ************ Helper for pictures uses username to get their profile picture************ """
def get_b64_img(username):
    user = User.objects(username=username).first()
    bytes_im = io.BytesIO(user.profile_pic.read())
    image = base64.b64encode(bytes_im.getvalue()).decode()
    return image

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"

    headers = {
        "Authorization" : "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers = headers, data = data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_for_song(token, song):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={song}&type=track&limit=10"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)

    results = []
    for elem in json_result['tracks']['items']:
        song_name = elem['name']
        artist_name = elem['artists'][0]['name']
        album_name = elem['album']['name']
        temp_dict = {"song" : song_name, "artist": artist_name, "album": album_name}
        results.append(temp_dict)
    return results

def top_songs(token, artist):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist}&type=artist&limit=1"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    artist_id = json_result[0]["id"]

    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result
""" ************ View functions ************ """


@songs.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()

    if form.validate_on_submit():
        return redirect(url_for("songs.query_results", query=form.search_query.data))

    return render_template("index.html", form=form)


@songs.route("/search-results/<query>", methods=["GET", "POST"])
def query_results(query):
    try:
        token = get_token()
        results = search_for_song(token, query)
    except ValueError as e:
        return render_template("query.html", error_msg=str(e))
    
    form = PlaylistForm()
    if form.validate_on_submit():
        playlist = Playlist(
            user=current_user._get_current_object(),
            song=form.song.data,
            artist = form.artist.data
        )

        playlist.save()

        return redirect(request.path)

    return render_template("query.html", results=results, form=form)


@songs.route("/songs/<artist>", methods=["GET", "POST"])
def artist_details(artist):
    global result
    result = []
    try:
        songs = top_songs(get_token(), artist)
        for index, elem in enumerate(songs):
            obj = {"number" : index + 1, "name" : elem["name"]}
            result.append(obj)
    except ValueError as e:
        return render_template("artist_detail.html", error_msg=str(e))

    return render_template("artist_detail.html", artist=result)


@songs.route("/user/<username>")
def user_detail(username):
    #uncomment to get review image
    #user = find first match in db
    user = User.objects(username=username).first()
    img = get_b64_img(user.username)
    playlist = Playlist.objects(user=user)
    return render_template("user_detail.html", image = img, playlist = playlist)
    