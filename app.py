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

@dataclass
class Song:
    title: str
    artist: str
    genre: str
    popularity: float

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Song':
        return cls(
            title=data.get('title', ''),
            artist=data.get('artist', ''),
            genre=data.get('genre', ''),
            popularity=float(data.get('popularity', 0.5))
        )

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

    def generate_playlist(self, preferences: MusicPreferences, popular_pct: int, moderate_pct: int, hidden_pct: int) -> List[Song]:
        age_group = self.get_age_group(preferences.age)
        
        prompt = f"""
        Create a playlist of exactly 25 songs matching these criteria:
        - Age group: {age_group}
        - Mood: {preferences.mood}
        - Favorite genres: {', '.join(preferences.favorite_genres)}

        Return the playlist as a JSON array with the following structure:
        {{"songs": [
            {{"title": "song title", "artist": "artist name", "genre": "genre", "popularity": 0.9}}
        ]}}

        Distribution:
        - {popular_pct}% popular hits (popularity 0.8-1.0)
        - {moderate_pct}% moderate hits (popularity 0.5-0.7)
        - {hidden_pct}% hidden gems (popularity 0.1-0.4)
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a music expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return self._parse_json_response(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return []

    def _parse_json_response(self, response_text: str) -> List[Song]:
        try:
            data = json.loads(response_text)
            songs_data = data.get('songs', [])
            songs = []
            
            for song_data in songs_data:
                if all(k in song_data for k in ['title', 'artist', 'genre', 'popularity']):
                    songs.append(Song.from_json(song_data))
            
            return sorted(songs, key=lambda x: x.popularity, reverse=True)[:25]
        except Exception as e:
            st.error(f"Error parsing response: {str(e)}")
            return []

def main():
    st.set_page_config(page_title="AI Music Playlist Generator", page_icon="🎵")
    st.title("🎵 AI Music Playlist Generator")
    
    agent = MusicAgent()
    
    with st.sidebar:
        st.header("Your Preferences")
        age = st.number_input("Age", min_value=13, max_value=100, value=25)
        mood = st.selectbox("Current Mood", options=agent.mood_options)
        
        age_group = agent.get_age_group(age)
        recommended_genres = agent.genre_by_age[age_group]
        
        st.write("Recommended genres for your age group:")
        st.write(", ".join(recommended_genres))
        
        selected_genres = st.multiselect(
            "Select your favorite genres",
            options=recommended_genres,
            default=recommended_genres[:2]
        )

        st.header("Song Distribution")
        popular_pct = st.slider("Popular Hits", 0, 100, 40, 5)
        moderate_pct = st.slider("Moderate Hits", 0, 100, 30, 5)
        hidden_pct = st.slider("Hidden Gems", 0, 100, 30, 5)

    if not selected_genres:
        st.warning("Please select at least one genre to continue.")
        return

    total_pct = popular_pct + moderate_pct + hidden_pct
    if total_pct != 100:
        st.error("Percentages must sum to 100%")
        return

    preferences = MusicPreferences(age=age, mood=mood, favorite_genres=selected_genres)
    
    if st.button("Generate Playlist"):
        playlist = agent.generate_playlist(preferences, popular_pct, moderate_pct, hidden_pct)
        
        if playlist:
            st.success("Playlist generated successfully!")
            
            cols = st.columns([1, 2, 2, 2, 1])
            cols[0].write("**#**")
            cols[1].write("**Song**")
            cols[2].write("**Artist**")
            cols[3].write("**Genre**")
            cols[4].write("**Rating**")
            
            for i, song in enumerate(playlist, 1):
                cols = st.columns([1, 2, 2, 2, 1])
                cols[0].write(f"{i}.")
                cols[1].write(song.title)
                cols[2].write(song.artist)
                cols[3].write(song.genre)
                cols[4].write(f"{song.popularity:.2f}")

if __name__ == "__main__":
    main() 