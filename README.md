# Movie Explorer Dashboard

## Introduction

This repository is dedicated to a dashboarding project on movie data. The end result can be seen [here](https://share.streamlit.io/philipdekoning/movie-explorer-dashboard/movie_explorer_dashboard_streamlit.py) on Streamlit, a dashboarding framework for python. 

## About the dashboard

With the plethora of streaming services and movie information sources available these days, you can find yourself scattered using multiple sources in your search for a new movie. A typical back and forth can be to start with the streaming service you subscribe to and browse for titles there and then, when you have found a candidate, jumping to IMDB or Rotten tomatoes, to get their ratings, or vice versa. This dashboard integrates sources with review information and streaming availability to ease the process of navigation. Additionally, the dashboard allows you to browse movies in ways that other sources do not offer. To begin with, you can specify criteria such as rating, genre, and year, and get an overview of movies which meet your selection criteria. Additionally, you can browse movies by the people that were involved in it, such as your favorite director or actors/actresses. For any of the movies in your selection you can get more information directly in the dashboard or through direct links from the dashboard. Happy movie browsing!

## Data

IMDB provides the main data source for this project. In the data/prep IMDB data.ipynb jupyter notebook, four zipped files are downloaded and stored as pickle files. These four files are untracked files which do not need to be in the repository (see .gitignore) and serve as inputs when creating three relevant tables on which the app runs, namely the 'movies', 'people', and 'genres' tables to be found under the data folder. As Streamlit constructs an app of the basis of a public repository, the resulting three tables have to be included in the repository. 

Additional data sources are OMDB and JustWatch, from which information is retrieved through their respective APIs. The main script for the Streamlit app, 'movie_explorer_dashboard_streamlit.py', includes the API calls. The OMDB API requires an API KEY (one can apply for it [here](https://www.omdbapi.com/apikey.aspx), which is non-public, and therefore it's kept a secret under the untracked secrets folder locally, and in the deployed Streamlit app it is stored under settings > secrets. 





