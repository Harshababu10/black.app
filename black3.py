import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Movie Rating & Behavior Analysis", layout="wide")

st.title("🎬 Movie Rating & Viewer Behavior Analysis")

# -------------------------------
# LOAD MOVIE DATA
# -------------------------------
movies = pd.read_csv("movies.csv")   # must contain: MovieID, Title, Genre, BaseRating

st.sidebar.header("🎯 User Preferences")

# -------------------------------
# USER INPUTS
# -------------------------------
users = ["U01", "U02", "U03", "U04", "U05"]
selected_user = st.sidebar.selectbox("Select User", users)

genres = st.sidebar.multiselect(
    "Preferred Genres",
    sorted(set(",".join(movies["Genre"]).split(", "))),
    default=["Drama", "Action"]
)

# -------------------------------
# USER WATCH TIME BIAS
# -------------------------------
user_watch_bias = {
    "U01": (90, 160),
    "U02": (70, 140),
    "U03": (60, 120),
    "U04": (80, 150),
    "U05": (100, 180)
}

# -------------------------------
# FILTER MOVIES BY GENRE
# -------------------------------
preferred_movies = movies[
    movies["Genre"].str.contains("|".join(genres), case=False, na=False)
]

# SAFE SAMPLING FIX (ERROR FIX)
if len(preferred_movies) < 60:
    preferred_movies = preferred_movies.sample(60, replace=True, random_state=42)
else:
    preferred_movies = preferred_movies.sample(60, random_state=42)

# -------------------------------
# GENERATE USER INTERACTION DATA
# -------------------------------
records = []

for _, row in preferred_movies.iterrows():
    wt_min, wt_max = user_watch_bias[selected_user]
    watch_time = np.random.randint(wt_min, wt_max)

    liked = any(g.lower() in row["Genre"].lower() for g in genres)

    rating = row["BaseRating"]

    if liked:
        rating += np.random.uniform(0.3, 0.8)
    else:
        rating -= np.random.uniform(0.2, 0.6)

    rating += (watch_time - 60) / 300
    rating = round(np.clip(rating, 1, 5), 1)

    records.append({
        "UserID": selected_user,
        "Movie": row["Title"],
        "Genre": row["Genre"],
        "WatchTime": watch_time,
        "UserRating": rating,
        "Liked": liked
    })

df = pd.DataFrame(records)

# -------------------------------
# METRICS
# -------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("🎥 Movies Watched", len(df))
col2.metric("⭐ Avg Rating", round(df["UserRating"].mean(), 2))
col3.metric("⏱ Avg Watch Time", f"{int(df['WatchTime'].mean())} mins")

# -------------------------------
# GRAPH 1: RATING VARIATION
# -------------------------------
st.subheader("⭐ Rating Variation by User")

st.plotly_chart(
    px.box(
        df,
        x="UserID",
        y="UserRating",
        title="User Rating Distribution"
    ),
    use_container_width=True
)

# -------------------------------
# GRAPH 2: WATCH TIME VS RATING
# -------------------------------
st.subheader("⏱ Watch Time vs Rating")

st.plotly_chart(
    px.scatter(
        df,
        x="WatchTime",
        y="UserRating",
        color="Liked",
        trendline="ols",
        title="Relationship Between Watch Time and Rating"
    ),
    use_container_width=True
)

# -------------------------------
# GRAPH 3: TOP GENRES
# -------------------------------
st.subheader("🎭 Top Genres Watched")

top_genres = (
    df.assign(Genre=df["Genre"].str.split(", "))
      .explode("Genre")
      .groupby("Genre")
      .size()
      .reset_index(name="Count")
      .sort_values("Count", ascending=False)
)

st.plotly_chart(
    px.bar(
        top_genres.head(5),
        x="Genre",
        y="Count",
        title="Top 5 Genres Watched"
    ),
    use_container_width=True
)

# -------------------------------
# GRAPH 4: WATCH TIME BY LIKED STATUS
# -------------------------------
st.subheader("❤️ Liked vs Not Liked Watch Time")

st.plotly_chart(
    px.bar(
        df.groupby("Liked")["WatchTime"].mean().reset_index(),
        x="Liked",
        y="WatchTime",
        title="Average Watch Time (Liked vs Not Liked)"
    ),
    use_container_width=True
)

# -------------------------------
# MOVIE RECOMMENDATIONS
# -------------------------------
st.subheader("🎯 Recommended Movies")

recommended = df[df["Liked"] == True].sort_values(
    ["UserRating", "WatchTime"],
    ascending=False
).head(5)

st.dataframe(recommended[["Movie", "Genre", "UserRating", "WatchTime"]])

# -------------------------------
# DEBUG INFO (OPTIONAL)
# -------------------------------
st.sidebar.info(f"Total movies loaded: {len(movies)}")
