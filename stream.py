#!/usr/bin/env python3

import os
import sys
import re
import json
import subprocess
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

class LobsterApp:
    def __init__(self):
        self.base_url = "https://flixhq.to"
        self.api_url = "https://dec.eatmynerds.live"
        self.provider = "Vidcloud"
        self.subs_language = "english"
        self.quality = "720"
        self.player = "mpv"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def notify(self, message, title=""):
        """Send notification to user"""
        if title:
            print(f"\n[{title}] {message}")
        else:
            print(f"\n{message}")
    
    def search(self, query):
        """Search for movies/TV shows"""
        self.notify(f"Searching for: {query}")
        search_query = query.replace(' ', '-')
        url = f"{self.base_url}/search/{search_query}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            items = soup.find_all('div', class_='flw-item')
            
            for item in items:
                try:
                    img = item.find('img')
                    link = item.find('a', href=True)
                    title_elem = link.get('title') if link else None
                    
                    if not link or not title_elem:
                        continue
                    
                    href = link['href']
                    media_type = 'tv' if '/tv/' in href else 'movie'
                    media_id = re.search(r'-(\d+)$', href)
                    media_id = media_id.group(1) if media_id else None
                    
                    year_elem = item.find('span', class_='fdi-item')
                    year = year_elem.text if year_elem else 'N/A'
                    
                    if media_id:
                        results.append({
                            'title': title_elem,
                            'id': media_id,
                            'type': media_type,
                            'year': year,
                            'image': img.get('data-src', '') if img else ''
                        })
                except Exception as e:
                    continue
            
            return results
        except Exception as e:
            self.notify(f"Search error: {e}", "Error")
            return []
    
    def select_from_list(self, items, prompt="Select"):
        """Simple CLI selection menu"""
        if not items:
            return None
        
        print(f"\n{prompt}:")
        for idx, item in enumerate(items, 1):
            if isinstance(item, dict):
                display = f"{item.get('title', item)} ({item.get('type', '')}) [{item.get('year', '')}]"
            else:
                display = str(item)
            print(f"  {idx}. {display}")
        
        while True:
            try:
                choice = input("\nEnter number ('b' to back or 'q' to quit): ").strip()
                if choice.lower() == 'q':
                    return None
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    return items[idx]
                print("Invalid selection. Try again.")
            except (ValueError, KeyboardInterrupt):
                return None
    
    def get_seasons(self, media_id):
        """Get available seasons for a TV show"""
        url = f"{self.base_url}/ajax/v2/tv/seasons/{media_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            seasons = []
            for link in soup.find_all('a', href=True):
                season_id = re.search(r'-(\d+)$', link['href'])
                if season_id:
                    seasons.append({
                        'title': link.text.strip(),
                        'id': season_id.group(1)
                    })
            return seasons
        except Exception as e:
            self.notify(f"Error getting seasons: {e}", "Error")
            return []
    
    def get_episodes(self, season_id):
        """Get episodes for a season"""
        url = f"{self.base_url}/ajax/v2/season/episodes/{season_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            episodes = []
            for item in soup.find_all(class_='nav-item'):
                data_id = item.get('data-id')
                title = item.get('title', '').strip()
                if data_id:
                    episodes.append({
                        'title': title,
                        'data_id': data_id
                    })
            return episodes
        except Exception as e:
            self.notify(f"Error getting episodes: {e}", "Error")
            return []
    
    def get_episode_id(self, data_id):
        """Get the episode streaming ID"""
        url = f"{self.base_url}/ajax/v2/episode/servers/{data_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for item in soup.find_all(class_='nav-item'):
                title = item.get('title', '')
                if self.provider in title:
                    return item.get('data-id')
            
            # Fallback to first available
            first_item = soup.find(class_='nav-item')
            return first_item.get('data-id') if first_item else None
        except Exception as e:
            self.notify(f"Error getting episode ID: {e}", "Error")
            return None
    
    def get_movie_episode_id(self, media_id):
        """Get episode ID for a movie"""
        url = f"{self.base_url}/ajax/movie/episodes/{media_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            link = soup.find('a', href=True, title=re.compile(self.provider))
            if link:
                href = link['href']
                match = re.search(r'\.(\d+)$', href)
                return match.group(1) if match else None
            return None
        except Exception as e:
            self.notify(f"Error getting movie ID: {e}", "Error")
            return None
    
    def get_video_link(self, episode_id):
        """Get the actual video streaming link"""
        # Get embed link
        url = f"{self.base_url}/ajax/episode/sources/{episode_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            embed_link = data.get('link', '')
            
            if not embed_link:
                self.notify("Could not get embed link", "Error")
                return None, None
            
            # Decrypt and get video link
            api_url = f"{self.api_url}/?url={embed_link}"
            response = self.session.get(api_url, timeout=15)
            response.raise_for_status()
            video_data = response.json()
            
            # Extract video link
            sources = video_data.get('sources', [])
            video_link = None
            for source in sources:
                file_url = source.get('file', '')
                if '.m3u8' in file_url:
                    video_link = file_url
                    break
            
            if not video_link:
                self.notify("Could not extract video link", "Error")
                return None, None
            
            # Apply quality settings
            if self.quality:
                video_link = re.sub(r'/playlist\.m3u8', f'/{self.quality}/index.m3u8', video_link)
            
            # Extract subtitle links
            subtitles = []
            tracks = video_data.get('tracks', [])
            for track in tracks:
                if track.get('kind') == 'captions':
                    label = track.get('label', '').lower()
                    if self.subs_language.lower() in label:
                        subtitles.append(track.get('file'))
            
            return video_link, subtitles
            
        except Exception as e:
            self.notify(f"Error getting video link: {e}", "Error")
            return None, None
    
    def play_video(self, video_url, subtitle_urls, title):
        """Play video using media player"""
        self.notify(f"Now playing: {title}")
        
        if not video_url:
            self.notify("No video URL provided", "Error")
            return
        
        # Build mpv command - use = for options with values
        cmd = [self.player, video_url]
        cmd.append(f'--force-media-title={title}')
        
        if subtitle_urls:
            for sub_url in subtitle_urls:
                cmd.append(f'--sub-file={sub_url}')
        
        try:
            subprocess.run(cmd, check=False)
        except FileNotFoundError:
            self.notify(f"Player '{self.player}' not found. Please install it.", "Error")
        except Exception as e:
            self.notify(f"Error playing video: {e}", "Error")
    
    def handle_movie(self, media):
        """Handle movie playback"""
        episode_id = self.get_movie_episode_id(media['id'])
        if not episode_id:
            self.notify("Could not get movie data", "Error")
            return
        
        video_url, subtitles = self.get_video_link(episode_id)
        if video_url:
            self.play_video(video_url, subtitles, media['title'])
    
    def handle_tv_show(self, media):
        """Handle TV show playback"""
        # Get seasons
        seasons = self.get_seasons(media['id'])
        if not seasons:
            self.notify("No seasons found", "Error")
            return
        
        season = self.select_from_list(seasons, "Select Season")
        if not season:
            return
        
        # Get episodes
        episodes = self.get_episodes(season['id'])
        if not episodes:
            self.notify("No episodes found", "Error")
            return
        
        while True:
            episode = self.select_from_list(episodes, "Select Episode")
            if not episode:
                return
            
            # Get episode ID
            episode_id = self.get_episode_id(episode['data_id'])
            if not episode_id:
                self.notify("Could not get episode data", "Error")
                continue
            
            video_url, subtitles = self.get_video_link(episode_id)
            if video_url:
                title = f"{media['title']} - {season['title']} - {episode['title']}"
                self.play_video(video_url, subtitles, title)
                
                # Ask to continue
                choice = input("\nPlay next episode? (y/n): ").strip().lower()
                if choice != 'y':
                    return
    
    def run(self):
        """Main application loop"""
        print("=" * 60)
        print("🦞 Lobster - Movie/TV Show Streaming")
        print("=" * 60)
        
        while True:
            query = input("\nSearch for movie/TV show (or 'q' to quit): ").strip()
            
            if query.lower() == 'q':
                print("Goodbye!")
                break
            
            if not query:
                continue
            
            # Search
            results = self.search(query)
            
            if not results:
                self.notify("No results found", "Info")
                continue
            
            # Select media
            media = self.select_from_list(results, "Select Media")
            if not media:
                continue
            
            # Handle based on type
            if media['type'] == 'movie':
                self.handle_movie(media)
            elif media['type'] == 'tv':
                self.handle_tv_show(media)


def main():
    """Entry point"""
    try:
        app = LobsterApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
