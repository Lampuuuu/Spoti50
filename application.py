import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask_session import Session
from flask import Flask, redirect, render_template, request
from tempfile import mkdtemp
from helpers import *

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# create authentified spotify object to conduct searches in the API
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

if not sp:
    apology("we have an internal server problem", 501)


# index route: renders index.html
@app.route("/")
def index():
    return render_template("index.html")

#recommendations route: renders the form "recommendations.html" and converts it to results on post 
@app.route("/recommendations", methods=["GET", "POST"])
def recommendations():

    # POST-method: Form was filled and is interpreted here
    if request.method == "POST":

        # get the form inputs and evaluate if they exist
        artists_requested = request.form.get("artists").split(", ")
        if not artists_requested[0]:
            artists_requested = []
        genre = [request.form.get("genre")]
        if not genre[0]:
            genre = []
        tracks_requested = request.form.get("tracks").split(", ")
        if not tracks_requested[0]:
            tracks_requested = []
        limit = request.form.get("limit")
        if not limit:
            limit = 20
        else:
            limit = int(limit)

        # option: no inputs
        if not artists_requested and not tracks_requested and not genre:
            return apology("no inputs", 400)

        # option too many inputs (with genre)
        elif len(artists_requested) + len(tracks_requested) > 4 and genre:
            return apology("too many inputs", 400)

        # option too many inputs (without genre)
        elif len(artists_requested) + len(tracks_requested) > 5 and not genre:
            return apology("too many inputs", 400)


        # inputs were valid -> get recommendations
        # more info see helpers.py
        recommendations = get_recommendations(artists_requested, genre, tracks_requested, limit)

        if not recommendations:
            return apology("no results found", 400)

        # initiate list, that later is passed to the html-file
        recs = []
        print(recommendations)

        # loop through all results of recommendations
        for track in recommendations:

            # get the important information from recommendations and save it in variables
            title = track["name"]
            artists = []
            artists[:] = [artist["name"] for artist in track["artists"]]
            link = track["external_urls"]["spotify"]
            img_url = track["album"]["images"][1]["url"]

            # combine them to a dict
            trackdict = {"title": title, "artists": artists, "link": link, "img": img_url}

            # append dict to the list introduced earlier
            recs.append(trackdict)
        
        # change up the user inputs so they can be represented in the output
        if artists_requested:
            artists_toresults = ", ".join(artists_requested)
        else:
            artists_toresults = []

        if tracks_requested:
            tracks_toresults = ", ".join(tracks_requested)
        else:
            tracks_toresults = []

        # render results template with all the important information
        return render_template("results.html",
                                recommendations=recs,
                                limit=limit,
                                artists=artists_toresults,
                                genre="".join(genre),
                                tracks=tracks_toresults)


    # GET-method
    else:
        
        # get available genres from Databas
        genres = sp.recommendation_genre_seeds()["genres"]

        # render recommendations.html with provided genres
        return render_template("recommendations.html", genres=genres)



# search route: renders search.html and converts it to results
@app.route("/search", methods=["GET", "POST"])
def search():

    # POST-method: evaluates form from get-route
    if request.method == "POST":

        # get user inputs from form and store them
        the_type = request.form.get("type")
        the_query = request.form.get("query")
        limit = request.form.get("limit")
        limit = request.form.get("limit")
        if not limit:
            limit = 5
        else:
            limit = int(limit)

        # render spotify search query with user inputs
        results = sp.search(the_query, limit, 0, the_type)
        
        """Depending on input-types "results" is different"""

        # artists were searched
        if the_type == "artist":

            # initiate output list
            artists = []

            # loop through results
            for artist in results["artists"]["items"]:

                # get important information
                name = artist["name"]
                link = artist["external_urls"]["spotify"]
                if artist["images"]:
                    img_url = artist["images"][0]["url"]

                # store information in dict
                artistdict = {"name": name, "link": link, "img": img_url}
                
                # append dict to output list
                artists.append(artistdict)

            # check if there were results
            if not artists:
                return apology("no results", 404)

            # render "searchresults.html" with important information
            return render_template("searchresults.html",
                                    limit=limit,
                                    type=the_type,
                                    query=the_query,
                                    withartists=False,
                                    searchresults=artists)

        # tracks were searched
        # methodology see artists
        elif the_type == "track":

            tracks = []

            for track in results["tracks"]["items"]:
                title = track["name"]
                link = track["external_urls"]["spotify"]
                img_url = track["album"]["images"][0]["url"]
                artists = []
                artists[:] = [artist["name"] for artist in track["artists"]]

                trackdict = {"name": title, "link": link, "img": img_url, "artists": artists}
                tracks.append(trackdict)

            if not tracks:
                return apology("no results", 404)

            return render_template("searchresults.html",
                                     limit=limit,
                                     type=the_type,
                                     query=the_query,
                                     withartists=True,
                                     searchresults=tracks)

        # albums were searched
        # methodology see artists
        elif the_type == "album":
            albums = []
            for album in results["albums"]["items"]:
                title =  album["name"]
                link = album["external_urls"]["spotify"]
                img_url = album["images"][0]["url"]


                artists = []
                artists[:] = [artist["name"] for artist in album["artists"]]
                
                albumdict = {"name": title, "link": link, "img": img_url, "artists": artists}
                albums.append(albumdict)
            
            if not albums:
                return apology("no results", 404)
                

            return render_template("searchresults.html",
                                    limit=limit,
                                    type=the_type,
                                    query=the_query,
                                    withartists=True,
                                    searchresults=albums)

        # in case something went wrong(which it shouldn't)
        else:
            return apology("something went wrong", 501)

    # GET-method: render template
    else:
        return render_template("search.html")

 
if __name__ == "__main__":
    app.run(debug=True)

