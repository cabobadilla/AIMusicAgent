import streamlit as st
import openai
from typing import List
from dataclasses import dataclass

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

    def generate_playlist(self, preferences: MusicPreferences) -> List[Song]:
        age_group = self.get_age_group(preferences.age)
        
        prompt = f"""
        Create a playlist of exactly 25 songs matching these criteria:
        - Age group: {age_group}
        - Mood: {preferences.mood}
        - Favorite genres: {', '.join(preferences.favorite_genres)}

        Format each song EXACTLY as follows (including the dashes and labels):
        - Title: [song title]
        - Artist: [artist name]
        - Genre: [genre]

        Include both popular hits and lesser-known gems.
        Ensure songs flow well together and match the mood.
        IMPORTANT: Use EXACTLY this format for EACH song, with each field on a new line.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a music expert creating playlists. Always format songs exactly as specified."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            playlist = self._parse_playlist_response(response.choices[0].message.content)
            
            if not playlist:
                st.error("Failed to generate playlist. Please try again.")
                return []
            
            return playlist
        except Exception as e:
            st.error(f"Error generating playlist: {str(e)}")
            return []

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
                    if all(k in current_song for k in ['title', 'artist', 'genre']):
                        songs.append(Song(**current_song))
                        current_song = {}
        
        return songs[:25]

def main():
    st.set_page_config(page_title="AI Music Playlist Generator", page_icon="🎵")
    
    st.title("🎵 AI Music Playlist Generator")
    st.write("Generate personalized playlists based on your age, mood, and music preferences!")
    
    agent = MusicAgent()
    
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

    preferences = MusicPreferences(
        age=age,
        mood=mood,
        favorite_genres=selected_genres
    )
    
    if st.button("Generate Playlist"):
        with st.spinner("Generating your personalized playlist..."):
            playlist = agent.generate_playlist(preferences)
        
        st.success("Playlist generated successfully!")
        
        st.header("Your Personalized Playlist")
        
        cols = st.columns([1, 2, 2, 2, 1])
        cols[0].write("**#**")
        cols[1].write("**Song**")
        cols[2].write("**Artist**")
        cols[3].write("**Genre**")
        cols[4].write("**Popularity**")
        
        for i, song in enumerate(playlist, 1):
            cols = st.columns([1, 2, 2, 2, 1])
            cols[0].write(f"{i}.")
            cols[1].write(song.title)
            cols[2].write(song.artist)
            cols[3].write(song.genre)
            cols[4].write(f"{song.popularity:.2f}")
        
        playlist_text = "\n".join([
            f"{i}. {song.title} by {song.artist} ({song.genre}) - Popularity: {song.popularity:.2f}" 
            for i, song in enumerate(playlist, 1)
        ])
        st.download_button(
            label="Download Playlist",
            data=playlist_text,
            file_name="my_playlist.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main() 