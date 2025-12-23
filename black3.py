import streamlit as st
import pandas as pd
import numpy as np
import os

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="Decoding Movie Ratings & Viewer Behaviour",
    layout="wide",
    page_icon="🎬"
)

st.title("🎬 Decoding Movie Ratings & Viewer Behaviour")
st.caption("Dataset-based Movie Rating & User Behaviour Analysis")

# =================================================
# LOAD DATA
# =================================================
FILE_NAME = "asta.csv"

if not os.path.exists(FILE_NAME):
    st.error("❌ asta.csv not found")
    st.stop()

movies = pd.read_csv(FILE_NAME, encoding="latin1")
movies.columns = movies.columns.str.strip()

movies = movies.rename(columns={
    "Unnamed: 0": "MovieID",
    "Name of movie": "MovieName",
    "Movie Rating": "BaseRating"
})

movies = movies[["MovieID", "MovieName", "Genre", "BaseRating"]].dropna()
movies["BaseRating"] = pd.to_numeric(movies["BaseRating"], errors="coerce")
movies = movies.dropna()

# =================================================
# SIDEBAR CONTROL
# =================================================
st.sidebar.header("🎛 Controls")

num_movies = st.sidebar.slider(
    "Movies to analyze",
    100,
    min(500, len(movies)),
    300
)

movies = movies.head(num_movies)

# =================================================
# USER PREFERENCE MODEL (UPDATED)
# =================================================
user_preferences = {
    "U01": ["Drama"],
    "U02": ["Action", "Adventure"],
    "U03": ["Comedy"],
    "U04": ["Crime", "Mystery"],       # Updated: Thriller -> Crime
    "U05": ["Fantasy", "Drama", "Comedy"]  # Updated: Romance -> Fantasy
}

np.random.seed(42)
records = []
dates = pd.date_range("2024-01-01", "2024-06-30")

for user, genres in user_preferences.items():

    # Step 1: Get preferred genre movies
    preferred_movies = movies[
        movies["Genre"].str.contains("|".join(genres), case=False, na=False)
    ]

    # Step 2: If still less, sample with replacement (only similar genres)
    if len(preferred_movies) < 60:
        preferred_movies = preferred_movies.sample(
            n=60, replace=True
        )
    else:
        preferred_movies = preferred_movies.sample(
            n=60, replace=False
        )

    # Step 3: Generate interactions
    for _, row in preferred_movies.iterrows():

        # Preference-based rating
        if any(g.lower() in row["Genre"].lower() for g in genres):
            rating = np.random.randint(4, 6)  # 4–5 for liked genres
        else:
            rating = np.random.randint(2, 4)  # 2–3 otherwise

        records.append([
            user,
            row["MovieID"],
            row["MovieName"],
            row["Genre"],
            rating,                         # ⭐ different ratings
            np.random.randint(60, 180),
            np.random.choice(dates)
        ])

df = pd.DataFrame(records, columns=[
    "UserID", "MovieID", "MovieName",
    "Genre", "UserRating", "WatchTime", "WatchDate"
])

# =================================================
# NORMALIZE GENRES
# =================================================
df["GenreList"] = df["Genre"].str.split(", ")

# =================================================
# USER–MOVIE DATA VIEW
# =================================================
st.subheader("📂 User–Movie Interaction Data")

view_user = st.selectbox(
    "View interactions",
    ["All"] + list(user_preferences.keys())
)

if view_user == "All":
    st.dataframe(df.head(50), use_container_width=True)
else:
    st.dataframe(df[df["UserID"] == view_user], use_container_width=True)

# =================================================
# KPI METRICS
# =================================================
st.subheader("📌 Platform Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Users", df["UserID"].nunique())
c2.metric("Movies Watched", df["MovieName"].nunique())
c3.metric("Avg Rating", round(df["UserRating"].mean(), 2))
c4.metric("Avg Watch Time", int(df["WatchTime"].mean()))

# =================================================
# SIMPLE GENRE POPULARITY (CLEAR OUTPUT)
# =================================================
st.subheader("🎭 Genre Popularity (Simple)")

genre_popularity = (
    df.explode("GenreList")["GenreList"]
      .value_counts()
      .reset_index()
)

genre_popularity.columns = ["Genre", "TotalViews"]

st.dataframe(genre_popularity, use_container_width=True)
st.bar_chart(genre_popularity.set_index("Genre"))

st.caption(
    "Genres are split first. Each watch is counted. Higher bar = more user interest."
)

# =================================================
# USER BEHAVIOUR ANALYSIS (TABLE)
# =================================================
st.subheader("👤 User Behaviour Analysis")

user_behaviour = (
    df.explode("GenreList")
      .groupby("UserID")
      .agg(
          MoviesWatched=("MovieID", "count"),
          AvgRating=("UserRating", "mean"),
          AvgWatchTime=("WatchTime", "mean"),
          FavoriteGenre=("GenreList", lambda x: x.value_counts().idxmax())
      )
      .reset_index()
)

st.dataframe(user_behaviour, use_container_width=True)

# =================================================
# SIMPLE USER BEHAVIOUR CHANGE (VERY EASY)
# =================================================
st.subheader("📊 User Favourite Genre (Behaviour Result)")

user_fav_genre = (
    df.explode("GenreList")
      .groupby(["UserID", "GenreList"])
      .size()
      .reset_index(name="WatchCount")
)

user_fav_genre = user_fav_genre.loc[
    user_fav_genre.groupby("UserID")["WatchCount"].idxmax()
]

st.dataframe(user_fav_genre, use_container_width=True)
st.bar_chart(user_fav_genre.set_index("UserID")[["WatchCount"]])

st.caption(
    "For each user, the most watched genre is selected as final behaviour."
)

# =================================================
# USER-BASED RECOMMENDATION
# =================================================
st.subheader("🎯 User-Based Recommendation")

selected_user = st.selectbox(
    "Select User",
    list(user_preferences.keys())
)

user_df = df[df["UserID"] == selected_user]

fav_genre = (
    user_df.explode("GenreList")["GenreList"]
    .value_counts()
    .idxmax()
)

st.success(f"🎯 Favorite Genre: {fav_genre}")

watched_movies = set(user_df["MovieID"])

user_recommendations = movies[
    movies["Genre"].str.contains(fav_genre, case=False, na=False) &
    (~movies["MovieID"].isin(watched_movies))
].head(7)

st.dataframe(
    user_recommendations[["MovieName", "Genre", "BaseRating"]],
    use_container_width=True
)

# =================================================
# MOVIE-BASED RECOMMENDATION
# =================================================
st.subheader("🔍 Movie-Based Recommendation")

movie_input = st.text_input("Type a movie name you like")

if movie_input:
    match = movies[
        movies["MovieName"].str.contains(movie_input, case=False, na=False)
    ]

    if match.empty:
        st.error("❌ Movie not found")
    else:
        movie = match.iloc[0]

        st.info(f"🎬 Movie: {movie['MovieName']}")
        st.info(f"🎭 Genre: {movie['Genre']}")
        st.info(f"⭐ Rating: {movie['BaseRating']}")

        main_genre = movie["Genre"].split(",")[0]

        similar = movies[
            movies["Genre"].str.contains(main_genre, case=False, na=False) &
            (movies["BaseRating"] >= movie["BaseRating"] - 0.5) &
            (movies["MovieID"] != movie["MovieID"])
        ].sort_values("BaseRating", ascending=False).head(10)

        st.subheader("🎯 Similar Movies")
        st.dataframe(
            similar[["MovieName", "Genre", "BaseRating"]],
            use_container_width=True
        )

# =================================================
# CONCLUSION
# =================================================
