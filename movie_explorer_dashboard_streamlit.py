import pandas as pd
import numpy as np
import re
from justwatch import JustWatch
import streamlit as st
import plotly.graph_objects as go
from plotly import tools
import plotly.offline as py
import plotly.express as px
import requests
import pickle
from sklearn.preprocessing import LabelEncoder

# define functions
def get_OMDB(movieID, API_KEY):
    OMDB_info      = requests.get('http://www.omdbapi.com/?i='+ movieID + '&apikey=' + API_KEY).json()
    withoutRatings = pd.json_normalize(data = OMDB_info).set_index('imdbID')#.columns#, record_path='Ratings')
    withoutRatings = withoutRatings.loc[:,withoutRatings.columns!='Ratings']
    Ratings        = pd.json_normalize(data=OMDB_info, record_path='Ratings').set_index('Source').T
    Ratings.index  = withoutRatings.index
    movie_complete = Ratings.merge(withoutRatings, right_index = True, left_index = True)
    return movie_complete

def obtain_offers_via_JustWatch(country_query = 'US', movieTitle = 'Licence to Kill'):

    relevant_columns = ['provider_id','monetization_type','presentation_type(s)','urls.edited_web','provider_name','country']
    # first search by IMDB title
    just_watch          = JustWatch(country=country_query)
    JWquery_title       = just_watch.search_title_id(query=movieTitle)

    # first title returned is most relevant usually
    most_relevent_title =  list(JWquery_title.items())[0][0]
    most_relevent_id    =  list(JWquery_title.items())[0][1]

    just_watch          = JustWatch(country=country_query)
    JWquery             = just_watch.get_title(title_id=most_relevent_id)

    if 'offers' in list(JWquery.keys()):
        offers                         = pd.json_normalize(data = JWquery, record_path = 'offers')
        offers['urls.edited_web']      = offers['urls.standard_web'].str.extract(r'(.+\.com|.+\.net|.+\.tv)')
        offers['provider_name']        = offers['urls.edited_web'].str.replace('https://|http://|www.|.com|.net|.tv','')
        offers['presentation_type(s)'] = offers.groupby(['provider_id','monetization_type'])['presentation_type'].transform(lambda x: '/'.join(x))
        offers                         = offers[relevant_columns].drop_duplicates()
        offers['Title']                = movieTitle
    else:
        offers = 'none'
    return offers

def robust_query_item(omdb_query_item):
    
    relevant_cols = ['Internet Movie Database','Rotten Tomatoes','Metacritic','BoxOffice','Plot','Actors','Awards','Writer','Poster']
    for relevant_col in relevant_cols:
        try:
            omdb_query_item[relevant_col] = omdb_query_item[relevant_col]
        except:
            omdb_query_item[relevant_col] = 'N/A'

    return omdb_query_item 

######### Initialize App #####################################################
st.set_page_config(layout="wide", page_icon="📽", page_title="movie dashboard")

# app requires valid API_KEY for OMDB api: https://www.omdbapi.com/
try: # for local running
    API_KEY = open('secrets/OMDb_API.txt', 'r').read()
except: # for app deployed to Streamlit
    API_KEY = st.secrets['API_KEY']

countries_justwatch = sorted(['US','UK','AU','CA','DE','SE','ES','NL','RU','CH','SK','RO','PT','PL','IT','GR','HK'])
person_types        = ['director', 'actor','actress', 'producer','writer', 'self', 'editor','cinematographer' , 'composer', 'production_designer', 'archive_footage','archive_sound']
default_director    = ['Christopher Nolan']
default_actor       = ['Tom Hanks']
default_actress     = ['Meryl Streep']
show_columns_movie_page = ['Title','Rating','Votes','Genres', 'Year','Runtime']

movies         = pickle.load(open("data/movies.pkl","rb"))
people         = pickle.load(open("data/people.pkl","rb"))
le_tconst      = pickle.load(open('data/label_encoder_tconst.pkl', 'rb')) 
Genres         = pickle.load(open("data/genres.pkl","rb"))
genres_options = np.sort(list(set(Genres.columns) - set(['genres_label','Genres'])))

st.sidebar.title("Explore Movies Dashboard 📽")
st.sidebar.subheader(f"data updated on: {open('data/date_update.txt', 'r').read()}")
st.sidebar.write("This dashboard allows the user to browse movie data on the basis of movie characteristics and by people. Besides IMDB ratings, ratings from Rotten Tomatoes and MetaCritic can be retrieved. Additionally, the app allows to check out the viewing options for any selected film using the JustWatch API.")

page = st.sidebar.radio('Browse:', ['Movies','Movie People'])
if page == 'Movie People':
    person_types_select      = st.multiselect('Select the type of profession to browse by', person_types, ['director'])
    people_selected_category = people[people.Category.isin(person_types_select)]

    if len(person_types_select) > 1:
        name_col = 'name with or without Category'
        nr_categories_per_name = people_selected_category.groupby('Name')['Category'].transform('count')
        people_selected_category['name with or without Category'] = people_selected_category.Name
        people_selected_category.loc[nr_categories_per_name > 1,'name with or without Category'] = \
        people_selected_category.loc[nr_categories_per_name > 1,'Name'] + ' - ' \
            + people_selected_category.loc[nr_categories_per_name > 1,'Category']  

    else:
        name_col = 'Name'

    # create list of options (choices) and subset: selected, which are fed as inputs to multiselect
    choices  = list(people_selected_category[name_col])    
    if set(person_types_select)   == set(['director']):
        selected = default_director 
    elif set(person_types_select) == set(['actor']):
        selected = default_actor
    elif set(person_types_select) == set(['actress']):
        selected = default_actress 
    else:
        selected = choices[1:3]

    people_selection = st.multiselect('Select people', choices, selected)

    movies_by_personCategory_stacked = \
    people_selected_category[people_selected_category[name_col].isin(people_selection)]\
        .explode('tconst')

    movies_persons = movies_by_personCategory_stacked.merge(movies, on = 'tconst', how = 'left').sort_values(by = 'Year')# movies[(movies.Name.isin(people_selection))].sort_values(by = 'Year')

    year_selection =  st.slider('Select range of years', 1899, 2021, (2000, 2021))

    movies_subset = movies_persons[(movies_persons.Year>=year_selection[0]) & \
                                   (movies_persons.Year<=year_selection[1])]
    movies_subset = movies_subset.sort_values(by = ['Rating','Title'], ascending = False).reset_index()


    fig = px.line(movies_subset.sort_values(by = ['Year', name_col]), x="Year", y="Rating", markers = True, \
                  title='Movie Scores over Time for Each Person Selected', \
                    color = name_col, hover_name = 'Title')# fig.show()

    st.plotly_chart(fig, use_container_width=True) # set size better

    show_columns_persons_page = ['Title','Rating','Votes','Genres', name_col, 'Year','Runtime']
    fig3d = px.scatter_3d(movies_subset, y='Runtime', z='Rating', x='Votes', color=name_col, hover_name = 'Title')
    fig3d.update_layout(
    title={
        'text': "rating, runtime, and the number of votes per movie (hover and drag!)",
        'y':0.9,
        'x':0.45,
        'xanchor': 'center',
        'yanchor': 'top'})
    st.plotly_chart(fig3d, use_container_width=True) # set size better

    st.subheader(f'Table selected movies ({movies_subset.shape[0]})')
    see_selected_movies = st.expander('👉 Click here to see movies for selected people')
    with see_selected_movies:
        st.dataframe(movies_subset[show_columns_persons_page]\
                .style.format({'Year': '{:.0f}', 'Rating': '{:.1f}',\
                'Runtime': '{:.0f}','Votes': '{:.0f}'}),height=500, width = 5500)

elif page == 'Movies':
    year_selection_movies     = st.slider('Select range of years', 1899, 2021, (2000, 2021))
    rating_selection_movies   = st.slider('Select range of IMDB ratings', 1,10,       (7,    10))
    Votes_selection_movies    = st.slider('Select range of number of votes on IMDB', 20,2500000, (100000,    1000000))
    runtime_selection_movies  = st.slider('Select range of runtime in minutes', 2,1500,  (90,    160))

    movies_subset = movies[(movies.Year        >= year_selection_movies[0])    & \
                           (movies.Year        <= year_selection_movies[1])    & \
                           (movies.Rating      >= rating_selection_movies[0])  & \
                           (movies.Rating      <= rating_selection_movies[1])  & \
                           (movies.Votes       >= Votes_selection_movies[0])   &\
                           (movies.Votes       <= Votes_selection_movies[1])   &\
                           (movies.Runtime     >= runtime_selection_movies[0]) &\
                           (movies.Runtime     <= runtime_selection_movies[1])]

    genres_selection= st.multiselect('Select genre(s)', genres_options, ['crime','drama'])
    labels_genres_selection = Genres.loc[\
                Genres[genres_selection].sum(axis = 1) == len(genres_selection),'genres_label']

    movies_subset = movies_subset[movies_subset.genres_label.isin(labels_genres_selection)]
    movies_subset = movies_subset.sort_values(by = ['Rating','Title'], ascending = False).reset_index()
    # movies_subset = movies_subset.sort_values(by = ['Year','Title']).reset_index()

    st.markdown("""---""")
    st.subheader(f'{movies_subset.shape[0]} movies meet the specified criteria')

    # 3D interactive visualization
    fig3d = px.scatter_3d(movies_subset, y='Runtime', z='Rating', x='Votes', color='Genres', hover_name = 'Title')
    fig3d.update_layout(
    title={
        'text': "rating, runtime, and the number of votes per movie (hover and drag!)",
        'y':0.9,
        'x':0.45,
        'xanchor': 'center',
        'yanchor': 'top'})
    
    st.plotly_chart(fig3d, use_container_width=True) # set size better

    st.subheader(f'Table selected movies ({movies_subset.shape[0]})')
    see_selected_movies = st.expander('👉 Click here to see movies that match the selection criteria')
    with see_selected_movies:
        st.dataframe(movies_subset[show_columns_movie_page].style.format({'Year': '{:.0f}', 'Rating': '{:.1f}',\
                'Runtime': '{:.0f}','Votes': '{:.0f}'}),height=500, width = 5500)

#################################################################################################################################################
#################################################################################################################################################
#################################################################################################################################################
######################### MOVIE DETAILS (applicable to both pages) ##############################################################################
st.markdown("""---""")
st.subheader("Movie details")

movie_select    = st.selectbox(f'Select any of the {movies_subset.shape[0]} movies from the selected subset for further details', movies_subset.Title)
movie_select_id = movies_subset.loc[movies_subset.Title==str(movie_select),'tconst'].item()
movie_imdb_id   = le_tconst.inverse_transform([movie_select_id]).item() # transform integer label back to original IMDB ID

movie_name_formatted = re.sub('[^0-9a-zA-Z]+', ' ',str(movie_select)).replace(" ", "_").lower()
if movie_name_formatted[len(movie_name_formatted )-1] == "_":
    movie_name_formatted = movie_name_formatted[:-1]
url_imdb = "https://www.imdb.com/title/"         + str(movie_imdb_id) + '/'
url_rt   = "https://www.rottentomatoes.com/m/"   + movie_name_formatted
url_yt   = "https://www.youtube.com/results?search_query="   + movie_name_formatted.replace("_", "-") + '+trailer'
url_letterboxd  = "https://letterboxd.com/film/" + movie_name_formatted.replace("_", "-")

if requests.get(url_rt).status_code != 200: # page doesn't exists >> go to search results instead for title
    url_rt = 'https://www.rottentomatoes.com/search?search=' + movie_name_formatted.replace("_", "%20")
if requests.get(url_letterboxd).status_code != 200: # page doesn't exists >> go to search results instead for title
    url_letterboxd = 'https://letterboxd.com/search/' + movie_name_formatted.replace("_", "")


st.write("Check out " + str(movie_select) + " at [IMDB](%s)" % url_imdb + ", at [Rotten Tomatoes](%s)" % url_rt + ", or at [Letterboxd](%s)" % url_letterboxd +' directly or checkout the trailer on [YouTube](%s)' % url_yt + ' here.')


OMDB_query = robust_query_item(get_OMDB(movie_imdb_id, API_KEY))
col1, col2, col3, col4 = st.columns(4)
col1.metric("IMDB",            OMDB_query['Internet Movie Database'].item())
col2.metric("Rotten Tomatoes", OMDB_query['Rotten Tomatoes'].item())
col3.metric("Metacritic",      OMDB_query['Metacritic'].item())
col4.metric("Box Office",      OMDB_query['BoxOffice'].item())
# col3.metric("Awards", OMDB_query['Awards'].item())

scol1, scol2 = st.columns((1, 4))   
# plot
scol2.subheader("Plot")
scol2.write(OMDB_query['Plot'].item())

# main actors
scol2.subheader('Main Actors')
scol2.write(OMDB_query['Actors'].item())

# awards
scol2.subheader('Awards')
scol2.write(OMDB_query['Awards'].item())

# director(s)
scol2.subheader('Director(s)')
scol2.write(OMDB_query['Director'].item())

# writer(s)
scol2.subheader('Writer(s)')
scol2.write(OMDB_query['Writer'].item())
scol1.image(OMDB_query['Poster'].item())

OMDB_query_secondary = OMDB_query.copy()

#### similar movies #################################################
st.markdown("""---""")
st.subheader('Movies similar to ' + str(movie_select))
similar_tconsts_to_selected = movies[movies.tconst == movie_select_id]\
    .similar_tconsts.item()
if ~np.isnan(similar_tconsts_to_selected).any():
    df_similar = movies[movies.tconst.isin(similar_tconsts_to_selected)]\
    .sort_values(by = ['Rating','Title'], ascending = False).reset_index()
    see_similar_movies = st.expander('👉 Click here to see movies similar to ' + str(movie_select))
    with see_similar_movies:
        st.dataframe(df_similar[show_columns_movie_page]\
        .style.format({'Year': '{:.0f}', 'Rating': '{:.1f}',\
            'Runtime': '{:.0f}','Votes': '{:.0f}'}),height=500, width = 5500)
else:
    st.write('No movies similar to ' + str(movie_select) + ' could be found')   
########################################################################

#### Streaming Availability ###########################################
st.markdown("""---""")
st.subheader('Streaming availability for ' + str(movie_select))
country_select = st.selectbox('Select for which country you would like to see offerings', countries_justwatch)

url_justwatch  = "https://www.justwatch.com/" + str(country_select).lower() + '/movie/' + movie_name_formatted.replace("_", "-")
if requests.get(url_justwatch).status_code != 200: # page doesn't exist
    url_justwatch  = "https://www.justwatch.com/" + str(country_select).lower() + '/search?q=' + movie_name_formatted.replace("_", "-")

st.write("You can also check out streaming availibility for " + str(movie_select) + " in " + str(country_select) + " directly at [JustWatch](%s)" % url_justwatch +' or retrieve offerings below:')

if st.button('Obtain offerings in ' + str(country_select) + ' through the JustWatch API for ' + str(movie_select)):
    try:
        offerings = obtain_offers_via_JustWatch(country_query = str(country_select), movieTitle = str(movie_select))
        offerings.drop(['provider_id','urls.edited_web','country','Title'], axis = 1, inplace = True)
        offerings = offerings.sort_values(by = ['monetization_type','provider_name'], ascending = False).reset_index(drop=True)
        offerings = offerings.rename(columns = {'monetization_type' : 'monetization type', 'presentation_type(s)': 'quality options','provider_name':'provider'})
        offerings = offerings[['provider', 'monetization type','quality options']]
        st.dataframe(offerings.T)
    except:
        st.write('No data could be obtained through the JustWatch API for ' + str(movie_select) + ' in ' + str(country_select))
########################################################################
