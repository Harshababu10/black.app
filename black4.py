

# streamlit is a Python framework used to build interactive web
# applications directly from Python scripts
# "as st" gives streamlit a short alias name so we can write st.xxx
# instead of streamlit.xxx every time
import streamlit as st

# pandas is used for data manipulation and analysis
# It provides DataFrame (table-like structure)
import pandas as pd

# numpy is used for numerical operations
# Here it is mainly used for random number generation
import numpy as np

# os module is used to interact with the operating system
# Here we use it to check if the CSV file exists or not
import os


# ===============================================================
# PAGE CONFIGURATION (WEB PAGE SETTINGS)
# ===============================================================

# This function controls how the Streamlit web page looks
# It must be called before any other Streamlit UI commands
st.set_page_config(
    page_title="Decoding Movie Ratings & Viewer Behaviour",  
    # page_title → text shown on the browser tab

    layout="wide",  
    # layout="wide" → uses full width of the browser screen

    page_icon="🎬"  
    # page_icon → emoji or icon shown in browser tab
)

# Displays a large heading (H1 style) at the top of the page
st.title("🎬 Decoding Movie Ratings & Viewer Behaviour")

# Displays a small descriptive text just below the title
st.caption("Dataset-based Movie Rating & User Behaviour Analysis")


# ===============================================================
# LOADING MOVIE DATA FROM CSV FILE
# ===============================================================

# Name of the CSV file that contains movie details
FILE_NAME = "asta.csv"

# os.path.exists() checks whether the file is present in the folder
if not os.path.exists(FILE_NAME):
    # If file is not found, show a red error message on the webpage
    st.error("❌ asta.csv not found")

    # Stop the program execution immediately
    # This avoids further errors in the app
    st.stop()

# Read the CSV file into a pandas DataFrame
# encoding="latin1" helps read special characters correctly
movies = pd.read_csv(FILE_NAME, encoding="latin1")

# Remove extra spaces from column names (cleaning step)
movies.columns = movies.columns.str.strip()

# Rename columns to simpler and consistent names
movies = movies.rename(columns={
    "Unnamed: 0": "MovieID",      # Unique ID for each movie
    "Name of movie": "MovieName", # Movie title
    "Movie Rating": "BaseRating"  # IMDb / base rating
})

# Select only the required columns and remove rows with missing values
movies = movies[["MovieID", "MovieName", "Genre", "BaseRating"]].dropna()

# Convert BaseRating column to numeric type
# errors="coerce" converts invalid values to NaN
movies["BaseRating"] = pd.to_numeric(movies["BaseRating"], errors="coerce")

# Remove rows where BaseRating could not be converted
movies = movies.dropna()


# ===============================================================
# SIDEBAR CONTROLS (USER INPUT)
# ===============================================================

# Create a heading inside the sidebar area
st.sidebar.header("🎛 Controls")

# Slider allows the user to choose how many movies to analyze
num_movies = st.sidebar.slider(
    "Movies to analyze",     # Text shown next to slider
    100,                     # Minimum movies
    min(500, len(movies)),   # Maximum movies allowed
    500                      # Default selected value
)

# Limit the dataset to only the selected number of movies
movies = movies.head(num_movies)


# ===============================================================
# USER PREFERENCE MODEL (SIMULATED USERS)
# ===============================================================

# Dictionary that maps each user to their preferred genre
# This simulates different user interests
user_preferences = {
    "U01": ["Drama"],
    "U02": ["Action"],
    "U03": ["Comedy"],
    "U04": ["Thriller"],
    "U05": ["Romance"]
}

# Setting random seed ensures same random output every time
# Useful for reproducibility
np.random.seed(42)

# Empty list to store user-movie interaction records
records = []

# Create a list of random dates for watch history
dates = pd.date_range("2024-01-01", "2024-06-30")

# Divide movies equally among users
movies_per_user = num_movies // len(user_preferences)

# Loop through each user and their genre preference
for user, genres in user_preferences.items():

    # Filter movies that match the user's preferred genre
    preferred_movies = movies[
        movies["Genre"].str.contains("|".join(genres), case=False, na=False)
    ].head(movies_per_user)

    # For each selected movie, create an interaction record
    for _, row in preferred_movies.iterrows():
        records.append([
            user,                         # User ID
            row["MovieID"],              # Movie ID
            row["MovieName"],            # Movie name
            row["Genre"],                # Movie genre
            np.random.randint(4, 6),     # Random user rating (4 or 5)
            np.random.randint(60, 180),  # Watch time in minutes
            np.random.choice(dates)      # Random watch date
        ])

# Convert interaction records list into a DataFrame
df = pd.DataFrame(records, columns=[
    "UserID", "MovieID", "MovieName",
    "Genre", "UserRating", "WatchTime", "WatchDate"
])


# ===============================================================
# GENRE NORMALIZATION
# ===============================================================

# Some movies have multiple genres separated by commas
# This splits them into a list and cleans formatting
df["GenreList"] = (
    df["Genre"]
    .str.split(",")                          # Split genres
    .apply(lambda x: [g.strip().title() for g in x])  
    # Remove spaces and capitalize
)


# ===============================================================
# DISPLAY USER–MOVIE INTERACTION DATA
# ===============================================================

# Section heading
st.subheader("📂 User–Movie Interaction Data")

# Display the DataFrame as an interactive table
st.dataframe(df, use_container_width=True)


# ===============================================================
# KPI DASHBOARD METRICS
# ===============================================================

st.subheader("📌 Platform Overview")

# Create 4 columns to display metrics side by side
c1, c2, c3, c4 = st.columns(4)

# Number of unique users on the platform
c1.metric("Users", df["UserID"].nunique())

# Number of unique movies watched
c2.metric("Movies Watched", df["MovieID"].nunique())

# Average rating given by users
c3.metric("Avg Rating", round(df["UserRating"].mean(), 2))

# Average watch time across all users
c4.metric("Avg Watch Time", int(df["WatchTime"].mean()))


# ===============================================================
# GENRE POPULARITY ANALYSIS
# ===============================================================

st.subheader("🎭 Genre Popularity")

# Explode GenreList so each genre is counted separately
genre_popularity = (
    df.explode("GenreList")["GenreList"]
    .value_counts()        # Count views per genre
    .reset_index()
)

# Rename columns for clarity
genre_popularity.columns = ["Genre", "TotalViews"]

# Display genre popularity table
st.dataframe(genre_popularity, use_container_width=True)

# Display bar chart showing genre popularity
st.bar_chart(genre_popularity.set_index("Genre"))


# ===============================================================
# USER BEHAVIOUR ANALYSIS
# ===============================================================

st.subheader("👤 User Behaviour Analysis")

# Group data by user and calculate behaviour statistics
user_behaviour = (
    df.explode("GenreList")
    .groupby("UserID")
    .agg(
        MoviesWatched=("MovieID", "nunique"),   # Unique movies watched
        AvgRating=("UserRating", "mean"),       # Average rating
        AvgWatchTime=("WatchTime", "mean"),     # Average watch time
        FavoriteGenre=("GenreList", lambda x: x.value_counts().idxmax())
        # Most watched genre
    )
    .reset_index()
)

# Display user behaviour table
st.dataframe(user_behaviour, use_container_width=True)


# ===============================================================
# USER ACTIVITY VISUALIZATION
# ===============================================================

st.subheader("📊 User Activity Overview")

# Count total movies watched by each user
user_activity = (
    df.groupby("UserID")["MovieID"]
    .count()
    .reset_index(name="MoviesWatched")
)

# Display bar chart for user activity
st.bar_chart(user_activity.set_index("UserID"))


# ===============================================================
# USER-BASED RECOMMENDATION SYSTEM
# ===============================================================

st.subheader("🎯 User-Based Recommendation")

# Dropdown menu to select a user
selected_user = st.selectbox(
    "Select User",
    df["UserID"].unique()
)

# Find the most frequently watched genre for the selected user
user_fav_genre = (
    df[df["UserID"] == selected_user]
    .explode("GenreList")["GenreList"]
    .value_counts()
    .idxmax()
)

# Display the user's favorite genre
st.success(f"💖 Favorite Genre: {user_fav_genre}")

# Recommend top-rated movies from that genre
personalized_recommendations = (
    movies[
        movies["Genre"].str.contains(user_fav_genre, case=False, na=False)
    ]
    .sort_values("BaseRating", ascending=False)
    .head(7)
)

# Display recommended movies
st.dataframe(
    personalized_recommendations[["MovieName", "Genre", "BaseRating"]],
    use_container_width=True
)


# ===============================================================
# MOVIE-BASED RECOMMENDATION SYSTEM
# ===============================================================

st.subheader("🔍 Movie-Based Recommendation")

# Text box for user to type a movie name
movie_input = st.text_input("Type a movie name you like")

if movie_input:
    # Search for movies matching input text
    match = movies[
        movies["MovieName"].str.contains(movie_input, case=False, na=False)
    ]

    if match.empty:
        # If no movie found, show error message
        st.error("❌ Movie not found")
    else:
        # Take the first matching movie
        movie = match.iloc[0]

        # Display selected movie details
        st.info(f"🎬 Movie: {movie['MovieName']}")
        st.info(f"🎭 Genre: {movie['Genre']}")
        st.info(f"⭐ Rating: {movie['BaseRating']}")

        # Extract the primary genre for similarity
        main_genre = movie["Genre"].split(",")[0].strip()

        # Find movies with similar genre and rating
        similar = movies[
            movies["Genre"].str.contains(main_genre, case=False, na=False) &
            (movies["BaseRating"] >= movie["BaseRating"] - 0.5) &
            (movies["MovieID"] != movie["MovieID"])
        ].sort_values("BaseRating", ascending=False).head(10)

        # Display similar movie recommendations
        st.subheader("🎯 Similar Movies")
        st.dataframe(
            similar[["MovieName", "Genre", "BaseRating"]],
            use_container_width=True
        )
