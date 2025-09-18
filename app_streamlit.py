import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Function to load data (can modify to read from Google Sheet CSV export link)
@st.cache_data
def load_data(csv_url):
    """Loads data from a CSV URL."""
    df = pd.read_csv(csv_url)
    # Ensure 'published_parsed' is datetime
    df['published_parsed'] = pd.to_datetime(df['published'], errors='coerce')
    return df

# Function to calculate tonality percentages
def get_tonality_percentages(df):
    """Calculates and returns tonality percentages."""
    tonality_counts = df['tonality'].value_counts()
    tonality_percentages = (tonality_counts / len(df)) * 100
    return tonality_percentages

# Function to get top sources
def get_top_sources(df, n=5):
    """Identifies and returns top sources by article count and percentage."""
    source_counts = df['source'].value_counts()
    top_sources = source_counts.head(n)
    total_articles = len(df)
    top_percentages = (top_sources / total_articles) * 100
    return top_sources, top_percentages

# Function to get recent mentions by tonality
def get_recent_mentions(df, tonality_type, n=5):
    """Filters for recent mentions of a specific tonality."""
    df_sorted = df.sort_values(by='published_parsed', ascending=False)
    recent_articles = df_sorted[df_sorted['tonality'] == tonality_type].head(n)
    return recent_articles[['published', 'title', 'source']]

# --- Streamlit App ---
st.title("HELB Kenya News Sentiment Monitor")

# You can replace this with the CSV export link from your Google Sheet
# Make sure the Google Sheet is shared publicly or with appropriate permissions for Streamlit to access it.
CSV_URL = "https://docs.google.com/spreadsheets/d/10LcDId4y2vz5mk7BReXL303-OBa2QxsN3drUcefpdSQ/export?format=csv" # Replace with your actual CSV export link

try:
    df = load_data(CSV_URL)

    st.sidebar.header("Filter by Date Range")

    # Get min and max dates from the data
    min_date = df['published_parsed'].min().date() if not df['published_parsed'].min() is pd.NaT else pd.to_datetime('2023-01-01').date() # Provide a default if NaT
    max_date = df['published_parsed'].max().date() if not df['published_parsed'].max() is pd.NaT else pd.to_datetime('today').date() # Provide a default if NaT

    if min_date > max_date: # Handle cases where min date is after max date due to data issues
         min_date = max_date

    start_date = st.sidebar.date_input("Start date", min_date)
    end_date = st.sidebar.date_input("End date", max_date)

    # Convert date_input to datetime objects for filtering
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date)

    # Filter DataFrame by date range
    filtered_df = df[(df['published_parsed'] >= start_datetime) & (df['published_parsed'] <= end_datetime)].copy() # Use .copy() to avoid SettingWithCopyWarning

    st.subheader("Analysis within Selected Date Range")

    if not filtered_df.empty:
        # --- Tonality Analysis ---
        st.subheader("Article Tonality Distribution")
        tonality_percentages = get_tonality_percentages(filtered_df)
        st.write("Percentage of articles by tonality:")
        st.write(tonality_percentages)

        # Plotting Tonality
        fig_tonality = px.pie(tonality_percentages, values=tonality_percentages.values, names=tonality_percentages.index, title='Distribution of Article Tonality')
        st.plotly_chart(fig_tonality)


        # --- Top Sources Analysis ---
        st.subheader("Top 5 News Sources")
        top_sources, top_percentages = get_top_sources(filtered_df)
        st.write("Top 5 Sources by Article Count and Percentage:")
        st.write(top_percentages)

        # Plotting Top Sources
        fig_sources = px.bar(top_sources, x=top_sources.index, y=top_sources.values, labels={'x':'Source', 'y':'Article Count'}, title='Top 5 Sources by Article Count')
        st.plotly_chart(fig_sources)


        # --- Recent Mentions ---
        st.subheader("Most Recent Mentions")

        st.write("Top 5 Most Recent Negative Articles:")
        negative_mentions = get_recent_mentions(filtered_df, 'Negative')
        if not negative_mentions.empty:
            st.dataframe(negative_mentions)
        else:
            st.info("No recent negative articles found in this date range.")


        st.write("Top 5 Most Recent Positive Articles:")
        positive_mentions = get_recent_mentions(filtered_df, 'Positive')
        if not positive_mentions.empty:
            st.dataframe(positive_mentions)
        else:
             st.info("No recent positive articles found in this date range.")


        # --- Optional: Time Series Plot of Article Counts ---
        st.subheader("Daily Article Count (Time Series)")
        timeseries = filtered_df.groupby(filtered_df['published_parsed'].dt.date).size().reset_index(name='count')
        timeseries['published_parsed'] = pd.to_datetime(timeseries['published_parsed']) # Convert date back to datetime for plotting

        fig_timeseries = px.line(timeseries, x='published_parsed', y='count', title='Daily Article Count')
        st.plotly_chart(fig_timeseries)


    else:
        st.warning("No articles found within the selected date range.")

except Exception as e:
    st.error(f"An error occurred: {e}")
    st.write("Please ensure the CSV URL is correct and accessible.")
