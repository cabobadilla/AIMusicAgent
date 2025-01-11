import streamlit as st
import openai
from typing import List, Dict, Any
from dataclasses import dataclass
import json

@dataclass
class MusicPreferences:
    age: int
    mood: str
    favorite_genres: List[str]
    hidden_gems_ratio: int  # Percentage of hidden gems (0-100)

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
            "18-24": ["Pop", "Hip Hop", "R&B", "Alternative", "Electronic"],
            "25-34": ["Pop", "Rock", "Hip Hop", "R&B", "Electronic"],
            "35-44": ["Rock", "Pop", "Alternative", "Country", "Jazz"],
            "45+": ["Classic Rock", "Jazz", "Classical", "Country", "Folk"]
        }

    def get_age_group(self, age: int) -> str:
        if age < 18: return "13-17"
        elif age < 25: return "18-24"
        elif age < 35: return "25-34"
        elif age < 45: return "35-44"
        else: return "45+"

    def generate_playlist(self, preferences: MusicPreferences) -> List[Song]:
        try:
            prompt = f"""Generate a playlist of 25 songs for:
            Age: {preferences.age}, Mood: {preferences.mood}
            Genres: {', '.join(preferences.favorite_genres)}
            
            Distribution: {preferences.hidden_gems_ratio}% hidden gems (popularity 0.1-0.4) 
            and {100 - preferences.hidden_gems_ratio}% popular songs (popularity 0.7-1.0)
            
            Return as JSON array: {{"songs": [
                {{"title": "name", "artist": "artist", "genre": "genre", "popularity": 0.9}}
            ]}}"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            # Parse response
            content = response.choices[0].message.content
            data = json.loads(content)
            songs = []
            
            for song_data in data.get('songs', []):
                songs.append(Song(
                    title=song_data.get('title', ''),
                    artist=song_data.get('artist', ''),
                    genre=song_data.get('genre', ''),
                    popularity=float(song_data.get('popularity', 0.5))
                ))
            
            return sorted(songs, key=lambda x: x.popularity, reverse=True)
        except Exception as e:
            st.error(f"Error generating playlist: {str(e)}")
            return []

def main():
    st.set_page_config(page_title="AI Music Playlist Generator", page_icon="🎵")
    st.title("🎵 AI Music Playlist Generator")
    
    agent = MusicAgent()
    
    # Add distribution explanation
    st.markdown("""
    ### 🎵 Hidden Gems Ratio
    Move the slider to adjust how many lesser-known songs you want in your playlist.
    - 0% = Only popular hits
    - 100% = Only hidden gems
    """)
    
    hidden_gems = st.slider("Percentage of Hidden Gems", 0, 100, 30, 10)
    
    with st.sidebar:
        st.header("Your Preferences")
        age = st.number_input("Age", min_value=13, max_value=100, value=25)
        mood = st.selectbox("Current Mood", options=agent.mood_options)
        
        recommended_genres = agent.genre_by_age[agent.get_age_group(age)]
        selected_genres = st.multiselect(
            "Select your favorite genres",
            options=recommended_genres,
            default=recommended_genres[:2]
        )

    if not selected_genres:
        st.warning("Please select at least one genre to continue.")
        return

    preferences = MusicPreferences(
        age=age,
        mood=mood,
        favorite_genres=selected_genres,
        hidden_gems_ratio=hidden_gems
    )
    
    if st.button("Generate Playlist"):
        with st.spinner("Generating playlist..."):
            playlist = agent.generate_playlist(preferences)
        
        if playlist:
            st.success("Playlist generated!")
            
            for i, song in enumerate(playlist, 1):
                st.write(f"{i}. {song.title} by {song.artist} ({song.genre}) - {song.popularity:.1f}")

if __name__ == "__main__":
    main() 