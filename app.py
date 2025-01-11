import streamlit as st
import openai
from typing import List
from dataclasses import dataclass

# Data Classes
@dataclass
class MusicPreferences:
    age: int
    mood: str
    favorite_genres: List[str]

@dataclass
class Song:
    title: str
    artist: str
    genre: str
    popularity: float

class MusicAgent:
    def __init__(self):
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        
        self.mood_options = [
            "Happy", "Energetic", "Relaxed", "Melancholic",
            "Focused", "Romantic", "Party", "Chill"
        ]
        
        self.genre_by_age = {
            "13-17": ["Pop", "Hip Hop", "K-pop", "Alternative", "Indie"],
            "18-24": ["Pop", "Hip Hop", "R&B", "Alternative", "Electronic", "Indie"],
            "25-34": ["Pop", "Rock", "Hip Hop", "R&B", "Alternative", "Electronic"],
            "35-44": ["Rock", "Pop", "Alternative", "Country", "R&B", "Jazz"],
            "45+": ["Classic Rock", "Jazz", "Classical", "Country", "Folk"]
        }

    def get_age_group(self, age: int) -> str:
        if age < 18:
            return "13-17"
        elif age < 25:
            return "18-24"
        elif age < 35:
            return "25-34"
        elif age < 45:
            return "35-44"
        else:
            return "45+"

    def generate_initial_playlist(self, preferences: MusicPreferences) -> List[Song]:
        age_group = self.get_age_group(preferences.age)
        
        prompt = f"""
        Generate a playlist of 50 songs based on the following criteria:
        - Age group: {age_group}
        - Mood: {preferences.mood}
        - Favorite genres: {', '.join(preferences.favorite_genres)}
        
        For each song, provide:
        - Song title
        - Artist name
        - Genre
        - Popularity score (0-1)
        
        Include a mix of popular and lesser-known songs.
        Format each song as:
        - Title: [song title]
        - Artist: [artist name]
        - Genre: [genre]
        - Popularity: [score]
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        songs = self._parse_playlist_response(response.choices[0].message.content)
        return songs

    def refine_playlist(self, initial_playlist: List[Song]) -> List[Song]:
        songs_str = "\n".join([f"{s.title} by {s.artist} ({s.genre})" for s in initial_playlist])
        
        prompt = f"""
        From the following 50 songs, select the best 25 songs that provide:
        - A balanced mix of popular hits and hidden gems
        - Good flow between songs
        - Variety in genres while maintaining cohesion
        - Emotional range appropriate for the mood
        
        Format each selected song as:
        - Title: [song title]
        - Artist: [artist name]
        - Genre: [genre]
        - Popularity: [score]
        
        Current playlist:
        {songs_str}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        
        refined_songs = self._parse_playlist_response(response.choices[0].message.content)
        return refined_songs[:25]

    def _parse_playlist_response(self, response_text: str) -> List[Song]:
        songs = []
        lines = response_text.strip().split('\n')
        current_song = {}
        
        for line in lines:
            if line.startswith('- '):
                line = line[2:]
                if 'Title:' in line:
                    current_song['title'] = line.split('Title:')[1].strip()
                elif 'Artist:' in line:
                    current_song['artist'] = line.split('Artist:')[1].strip()
                elif 'Genre:' in line:
                    current_song['genre'] = line.split('Genre:')[1].strip()
                elif 'Popularity:' in line:
                    try:
                        current_song['popularity'] = float(line.split('Popularity:')[1].strip())
                        songs.append(Song(**current_song))
                        current_song = {}
                    except:
                        current_song['popularity'] = 0.5
        
        return songs

# Streamlit UI
def main():
    st.set_page_config(page_title="AI Music Playlist Generator", page_icon="🎵")
    
    st.title("🎵 AI Music Playlist Generator")
    st.write("Generate personalized playlists based on your age, mood, and music preferences!")
    
    # Initialize the agent
    agent = MusicAgent()
    
    # Create sidebar for inputs
    with st.sidebar:
        st.header("Your Preferences")
        age = st.number_input("Age", min_value=13, max_value=100, value=25)
        
        mood = st.selectbox(
            "Current Mood",
            options=agent.mood_options
        )
        
        age_group = agent.get_age_group(age)
        recommended_genres = agent.genre_by_age[age_group]
        
        st.write("Recommended genres for your age group:")
        st.write(", ".join(recommended_genres))
        
        selected_genres = st.multiselect(
            "Select your favorite genres",
            options=recommended_genres,
            default=recommended_genres[:2]
        )

    if not selected_genres:
        st.warning("Please select at least one genre to continue.")
        return

    # Create preferences object
    preferences = MusicPreferences(
        age=age,
        mood=mood,
        favorite_genres=selected_genres
    )
    
    if st.button("Generate Playlist"):
        with st.spinner("Generating initial playlist..."):
            initial_playlist = agent.generate_initial_playlist(preferences)
        
        with st.spinner("Refining playlist..."):
            final_playlist = agent.refine_playlist(initial_playlist)
        
        st.success("Playlist generated successfully!")
        
        # Display the playlist
        st.header("Your Personalized Playlist")
        
        # Create three columns for better visualization
        cols = st.columns([1, 2, 2, 2])
        cols[0].write("**#**")
        cols[1].write("**Song**")
        cols[2].write("**Artist**")
        cols[3].write("**Genre**")
        
        for i, song in enumerate(final_playlist, 1):
            cols = st.columns([1, 2, 2, 2])
            cols[0].write(f"{i}.")
            cols[1].write(song.title)
            cols[2].write(song.artist)
            cols[3].write(song.genre)
        
        # Add export option
        playlist_text = "\n".join([f"{i}. {song.title} by {song.artist} ({song.genre})" 
                                 for i, song in enumerate(final_playlist, 1)])
        st.download_button(
            label="Download Playlist",
            data=playlist_text,
            file_name="my_playlist.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main() 