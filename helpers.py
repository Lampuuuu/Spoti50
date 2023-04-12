import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from time import sleep
from flask import redirect, render_template, request, session

"""
neat helper functions for the main app
"""

# create authentified spotify object to search db
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

# function that gets recommendations from the db
def get_recommendations(artists, genre, tracks, limit):

    # list for artist IDs
    artist_IDs = []

    # if artists were input
    if artists:
        
        # loop through each
        for artist in artists:
            if artist:
                # get the first result from search, indentify its ID and append it
                artistsearch = sp.search(artist, 1, 0, "artist")
                if artistsearch["artists"]["items"]:
                    ID = artistsearch["artists"]["items"][0]["id"]
                    artist_IDs.append(ID)

    # list for track IDs 
    track_IDs = []

    # get IDs for tracks, methodology see artists
    if tracks: 
        for track in tracks:
            if track:
                tracksearch = sp.search(track, 1, 0, "track")
                if tracksearch["tracks"]["items"]:
                    ID = tracksearch["tracks"]["items"][0]["id"]
                    track_IDs.append(ID)

    recommendations = []
    
    # get the recommendations from spotify's recommendations function
    if track_IDs or artist_IDs:
        rec = sp.recommendations(artist_IDs, genre, track_IDs, limit)

        # store resulting tracks neatly in a list

        for track in rec["tracks"]:
            recommendations.append(track)

    #return list
    return recommendations



def apology(message, code=400):
    """render message as an apology"""
    def escape(s):
        """
        Escape special characters. More information:
        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    
    return render_template("apology.html", top=code, bottom = escape(message)), code
    