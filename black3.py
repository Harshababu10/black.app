import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

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
# SIDEBAR CONTROL (USE ALL 500 MOVIES)
# =================================================
st.sidebar.header("🎛 Controls")

num_movies = st.sidebar.slider(
    "Movies to analyze",
    100,
    len(movies),
    500
)

movies = movies.sample(num_movies, random_state=42)

# =================================================
# USER PREFERENCE MODEL
# =================================================
user_preferences = {
    "U01": ["Drama"],
    "U02": ["Action", "Adventure"],
    "U03": ["Comedy"],
    "U04": ["Thriller", "Mystery"],
    "U05": ["Romance"]
}

# =================================================
# SYNTHETIC USER INTERACTION DATA
# =================================================
np.random.seed(42)
records = []
dates = pd.date_range("2024-01-01", "2024-06-30")

for user, genres in user_preferences.items():
    preferred_movies = movies[
        movies["Genre"].str.contains("|".join(genres), case=False, na=False)
    ].sample(60, random_state=42)

    for _, row in preferred_movies.iterrows():
        rating = np.clip(
            round(row["BaseRating"] + np.random.normal(0, 0.4), 1),
            1,
            5
        )

        records.append([
            user,
            row["MovieID"],
            row["MovieName"],
            row["Genre"],
            rating,
            np.random.randint(60, 180),
            np.random.choice(dates)
        ])

df = pd.DataFrame(records, columns=[
    "UserID", "MovieID", "MovieName",
    "Genre", "UserRating", "WatchTime", "WatchDate"
])

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
# USER WATCH TIME GRAPH (REQUESTED)
# =================================================
st.subheader("⏱ User Watch Time Analysis")

watch_time_user = df.groupby("UserID")["WatchTime"].mean().reset_index()

st.plotly_chart(
    px.bar(
        watch_time_user,
        x="UserID",
        y="WatchTime",
        title="Average Watch Time per User (minutes)"
    ),
    use_container_width=True
)

# =================================================
# USER RATING DISTRIBUTION
# =================================================
st.subheader("⭐ User Rating Distribution")

st.plotly_chart(
    px.histogram(
        df,
        x="UserRating",
        nbins=10,
        title="Distribution of User Ratings"
    ),
    use_container_width=True
)

# =================================================
# GENRE POPULARITY
# =================================================
st.subheader("🎭 Genre Popularity")

genre_counts = (
    df["Genre"]
    .str.split(", ")
    .explode()
    .value_counts()
    .reset_index()
)
genre_counts.columns = ["Genre", "Count"]

st.plotly_chart(
    px.bar(
        genre_counts.sort_values("Count", ascending=False),
        x="Genre",
        y="Count",
        title="Most Watched Genres"
    ),
    use_container_width=True
)

# =================================================
# USER BEHAVIOUR TABLE
# =================================================
st.subheader("👤 User Behaviour Summary")

user_behaviour = df.groupby("UserID").agg(
    MoviesWatched=("MovieName", "count"),
    AvgRating=("UserRating", "mean"),
    AvgWatchTime=("WatchTime", "mean"),
    FavoriteGenre=("Genre", lambda x:
        x.str.split(", ").explode().value_counts().idxmax()
    )
)

st.dataframe(user_behaviour, use_container_width=True)

# =================================================
# AVERAGE RATING PER USER GRAPH
# =================================================
st.subheader("📊 Average Rating per User")

avg_rating_user = df.groupby("UserID")["UserRating"].mean().reset_index()

st.plotly_chart(
    px.bar(
        avg_rating_user,
        x="UserID",
        y="UserRating",
        title="Average Rating Given by Each User"
    ),
    use_container_width=True
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
    user_df["Genre"]
    .str.split(", ")
    .explode()
    .value_counts()
    .idxmax()
)

st.success(f"🎯 Favorite Genre: {fav_genre}")

watched_movies = set(user_df["MovieID"])

user_recommendations = movies[
    movies["Genre"].str.contains(fav_genre, case=False) &
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

        similar = movies[
            (movies["Genre"].str.contains(movie["Genre"].split(",")[0], case=False)) &
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
st.markdown("""
## ✅ Project Summary
✔ Uses all 500 movies  
✔ Visible watch-time & rating analysis  
✔ Realistic user behavior modeling  
✔ User-based & movie-based recommendations  
✔ Suitable for **lab exam, viva & GitHub**
""")
