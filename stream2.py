#!/usr/bin/env python3
"""
Lobster - Movie/TV Show Streaming Application (Python Version)
An improved Python implementation with robust error handling and interactive features
Version: 2.0
"""

import os
import sys
import re
import json
import subprocess
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from urllib.parse import quote

try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"Error: Missing required package - {e}")
    print("\nPlease install required packages:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.lobster.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ConfigManager:
    """Manage application configuration"""
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'lobster2'
        self.config_file = self.config_dir / 'config.json'
        self.history_file = self.config_dir / 'history.json'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """Load configuration from file"""
        default_config = {
            'base_url': 'https://flixhq.to',
            'api_url': 'https://dec.eatmynerds.live',
            'provider': 'Vidcloud',
            'subs_language': 'english',
            'quality': '1080',
            'player': 'mpv',
            'auto_next': False,
            'download_dir': str(Path.home() / 'Downloads'),
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load config: {e}. Using defaults.")
        
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()


class LobsterApp:
    """Main application class"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.session = self._create_session()
        self.current_media = None
        self.current_season = None
        self.current_episode = None
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
    def notify(self, message: str, level: str = "INFO", title: str = ""):
        """Send notification to user with color coding"""
        color_map = {
            "INFO": Colors.OKBLUE,
            "SUCCESS": Colors.OKGREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL
        }
        
        color = color_map.get(level, Colors.ENDC)
        prefix = f"[{title}] " if title else ""
        print(f"\n{color}{Colors.BOLD}{prefix}{message}{Colors.ENDC}")
        
        # Log to file
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"{prefix}{message}")
    
    def check_player(self) -> bool:
        """Check if the media player is available"""
        player = self.config.get('player')
        try:
            result = subprocess.run(
                [player, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def search(self, query: str) -> List[Dict]:
        """Search for movies/TV shows"""
        self.notify(f"Searching for: {query}", "INFO")
        search_query = query.replace(' ', '-')
        url = f"{self.config.get('base_url')}/search/{search_query}"
        
        try:
            response = self.session.get(url, timeout=(5, 10))
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            items = soup.find_all('div', class_='flw-item')
            
            if not items:
                self.notify("No results found", "WARNING")
                return []
            
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
                    year = year_elem.text.strip() if year_elem else 'N/A'
                    
                    if media_id:
                        results.append({
                            'title': title_elem,
                            'id': media_id,
                            'type': media_type,
                            'year': year,
                            'image': img.get('data-src', '') if img else ''
                        })
                except Exception as e:
                    logger.debug(f"Error parsing item: {e}")
                    continue
            
            self.notify(f"Found {len(results)} results", "SUCCESS")
            return results
            
        except requests.Timeout:
            self.notify("Search timed out. Please check your connection.", "ERROR")
            return []
        except requests.RequestException as e:
            self.notify(f"Search error: {e}", "ERROR")
            return []
    
    def select_from_list(self, items: List, prompt: str = "Select", 
                        display_key: str = None) -> Optional:
        """Interactive selection menu with improved UX"""
        if not items:
            return None
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{prompt}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
        
        for idx, item in enumerate(items, 1):
            if isinstance(item, dict):
                if display_key:
                    display = item.get(display_key, str(item))
                else:
                    display = f"{item.get('title', item)} ({item.get('type', '')}) [{item.get('year', '')}]"
            else:
                display = str(item)
            
            print(f"{Colors.OKCYAN}  {idx:2d}.{Colors.ENDC} {display}")
        
        print(f"\n{Colors.WARNING}Enter number, 'b' to go back, or 'q' to quit{Colors.ENDC}")
        
        while True:
            try:
                choice = input(f"\n{Colors.BOLD}Your choice: {Colors.ENDC}").strip().lower()
                
                if choice == 'q':
                    self.notify("Goodbye!", "INFO")
                    sys.exit(0)
                elif choice == 'b':
                    return None
                
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    return items[idx]
                
                self.notify("Invalid selection. Try again.", "WARNING")
                
            except ValueError:
                self.notify("Please enter a valid number.", "WARNING")
            except KeyboardInterrupt:
                print()
                return None
    
    def get_seasons(self, media_id: str) -> List[Dict]:
        """Get available seasons for a TV show"""
        url = f"{self.config.get('base_url')}/ajax/v2/tv/seasons/{media_id}"
        
        try:
            response = self.session.get(url, timeout=(3, 10))
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
            
            if seasons:
                self.notify(f"Found {len(seasons)} season(s)", "SUCCESS")
            return seasons
            
        except requests.Timeout:
            self.notify("Request timed out while fetching seasons", "ERROR")
            return []
        except requests.RequestException as e:
            self.notify(f"Error getting seasons: {e}", "ERROR")
            return []
    
    def get_episodes(self, season_id: str) -> List[Dict]:
        """Get episodes for a season"""
        url = f"{self.config.get('base_url')}/ajax/v2/season/episodes/{season_id}"
        
        try:
            response = self.session.get(url, timeout=(3, 10))
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
            
            if episodes:
                self.notify(f"Found {len(episodes)} episode(s)", "SUCCESS")
            return episodes
            
        except requests.Timeout:
            self.notify("Request timed out while fetching episodes", "ERROR")
            return []
        except requests.RequestException as e:
            self.notify(f"Error getting episodes: {e}", "ERROR")
            return []
    
    def get_episode_id(self, data_id: str) -> Optional[str]:
        """Get the episode streaming ID"""
        url = f"{self.config.get('base_url')}/ajax/v2/episode/servers/{data_id}"
        provider = self.config.get('provider')
        
        try:
            response = self.session.get(url, timeout=(3, 10))
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find preferred provider
            for item in soup.find_all(class_='nav-item'):
                title = item.get('title', '')
                if provider in title:
                    return item.get('data-id')
            
            # Fallback to first available
            first_item = soup.find(class_='nav-item')
            if first_item:
                self.notify(f"Using fallback provider", "WARNING")
                return first_item.get('data-id')
            
            return None
            
        except requests.Timeout:
            self.notify("Request timed out while fetching episode ID", "ERROR")
            return None
        except requests.RequestException as e:
            self.notify(f"Error getting episode ID: {e}", "ERROR")
            return None
    
    def get_movie_episode_id(self, media_id: str) -> Optional[str]:
        """Get episode ID for a movie"""
        url = f"{self.config.get('base_url')}/ajax/movie/episodes/{media_id}"
        provider = self.config.get('provider')
        
        try:
            response = self.session.get(url, timeout=(3, 10))
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            link = soup.find('a', href=True, title=re.compile(provider, re.IGNORECASE))
            if link:
                href = link['href']
                match = re.search(r'\.(\d+)$', href)
                return match.group(1) if match else None
            
            # Try any available link
            link = soup.find('a', href=True)
            if link:
                href = link['href']
                match = re.search(r'\.(\d+)$', href)
                if match:
                    self.notify("Using fallback provider", "WARNING")
                    return match.group(1)
            
            return None
            
        except requests.Timeout:
            self.notify("Request timed out while fetching movie ID", "ERROR")
            return None
        except requests.RequestException as e:
            self.notify(f"Error getting movie ID: {e}", "ERROR")
            return None
    
    def get_video_link(self, episode_id: str) -> Tuple[Optional[str], List[str]]:
        """Get the actual video streaming link"""
        # Get embed link
        url = f"{self.config.get('base_url')}/ajax/episode/sources/{episode_id}"
        
        try:
            # Get embed link with timeout
            response = self.session.get(url, timeout=(5, 10))
            response.raise_for_status()
            data = response.json()
            embed_link = data.get('link', '')
            
            if not embed_link:
                self.notify("Could not get embed link", "ERROR")
                return None, []
            
            self.notify("Extracting video link...", "INFO")
            
            # Decrypt and get video link with longer timeout for API
            api_url = f"{self.config.get('api_url')}/?url={embed_link}"
            response = self.session.get(api_url, timeout=(10, 20))
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
                self.notify("Could not extract video link", "ERROR")
                return None, []
            
            # Apply quality settings
            quality = self.config.get('quality')
            if quality:
                video_link = re.sub(r'/playlist\.m3u8', f'/{quality}/index.m3u8', video_link)
            
            # Extract subtitle links
            subtitles = []
            subs_language = self.config.get('subs_language')
            tracks = video_data.get('tracks', [])
            
            for track in tracks:
                if track.get('kind') == 'captions':
                    label = track.get('label', '').lower()
                    if subs_language.lower() in label:
                        sub_url = track.get('file')
                        if sub_url:
                            subtitles.append(sub_url)
            
            if subtitles:
                self.notify(f"Found {len(subtitles)} subtitle(s)", "SUCCESS")
            else:
                self.notify("No subtitles found for selected language", "WARNING")
            
            return video_link, subtitles
            
        except requests.Timeout:
            self.notify("Request timed out while getting video link", "ERROR")
            return None, []
        except requests.RequestException as e:
            self.notify(f"Error getting video link: {e}", "ERROR")
            return None, []
        except json.JSONDecodeError:
            self.notify("Invalid response from server", "ERROR")
            return None, []
    
    def play_video(self, video_url: str, subtitle_urls: List[str], title: str):
        """Play video using media player"""
        if not video_url:
            self.notify("No video URL provided", "ERROR")
            return
        
        player = self.config.get('player')
        
        # Check if player exists
        if not self.check_player():
            self.notify(f"Player '{player}' not found. Please install it.", "ERROR")
            self.notify("Install mpv: https://mpv.io/installation/", "INFO")
            return
        
        self.notify(f"Now playing: {title}", "SUCCESS", "Media Player")
        
        # Build mpv command
        cmd = [player, video_url]
        cmd.append(f'--force-media-title={title}')
        cmd.append('--save-position-on-quit')
        cmd.append('--quiet')
        
        # Add subtitles
        if subtitle_urls:
            for sub_url in subtitle_urls:
                cmd.append(f'--sub-file={sub_url}')
        
        try:
            # Run player
            process = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            if process.returncode != 0 and process.returncode != 4:  # 4 is normal mpv quit
                self.notify("Player exited with an error", "WARNING")
                
        except FileNotFoundError:
            self.notify(f"Player '{player}' not found. Please install it.", "ERROR")
        except KeyboardInterrupt:
            self.notify("Playback interrupted", "WARNING")
        except Exception as e:
            self.notify(f"Error playing video: {e}", "ERROR")
    
    def handle_movie(self, media: Dict):
        """Handle movie playback"""
        self.current_media = media
        
        episode_id = self.get_movie_episode_id(media['id'])
        if not episode_id:
            self.notify("Could not get movie data", "ERROR")
            return
        
        video_url, subtitles = self.get_video_link(episode_id)
        if video_url:
            self.play_video(video_url, subtitles, media['title'])
        else:
            self.notify("Failed to get video link", "ERROR")
    
    def handle_tv_show(self, media: Dict):
        """Handle TV show playback"""
        self.current_media = media
        
        # Get seasons
        seasons = self.get_seasons(media['id'])
        if not seasons:
            self.notify("No seasons found", "ERROR")
            return
        
        while True:
            season = self.select_from_list(
                seasons, 
                f"Select Season for '{media['title']}'",
                'title'
            )
            if not season:
                return
            
            self.current_season = season
            
            # Get episodes
            episodes = self.get_episodes(season['id'])
            if not episodes:
                self.notify("No episodes found", "ERROR")
                continue
            
            # Episode playback loop
            current_episode_idx = 0
            while current_episode_idx < len(episodes):
                episode = episodes[current_episode_idx]
                
                # Show episode selection if not auto-continuing
                if current_episode_idx == 0 or not self.config.get('auto_next'):
                    selected = self.select_from_list(
                        episodes[current_episode_idx:], 
                        f"Select Episode - {season['title']}",
                        'title'
                    )
                    if not selected:
                        break
                    episode = selected
                    current_episode_idx = episodes.index(episode)
                
                self.current_episode = episode
                
                # Get episode ID
                episode_id = self.get_episode_id(episode['data_id'])
                if not episode_id:
                    self.notify("Could not get episode data", "ERROR")
                    current_episode_idx += 1
                    continue
                
                # Get and play video
                video_url, subtitles = self.get_video_link(episode_id)
                if video_url:
                    title = f"{media['title']} - {season['title']} - {episode['title']}"
                    self.play_video(video_url, subtitles, title)
                else:
                    self.notify("Failed to get video link", "ERROR")
                
                # Ask what to do next
                if current_episode_idx < len(episodes) - 1:
                    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
                    print(f"{Colors.OKCYAN}1.{Colors.ENDC} Play next episode")
                    print(f"{Colors.OKCYAN}2.{Colors.ENDC} Replay current episode")
                    print(f"{Colors.OKCYAN}3.{Colors.ENDC} Choose another episode")
                    print(f"{Colors.OKCYAN}4.{Colors.ENDC} Back to season selection")
                    print(f"{Colors.OKCYAN}5.{Colors.ENDC} New search")
                    print(f"{Colors.OKCYAN}q.{Colors.ENDC} Quit")
                    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
                    
                    choice = input(f"\n{Colors.BOLD}Your choice: {Colors.ENDC}").strip().lower()
                    
                    if choice == '1':
                        current_episode_idx += 1
                    elif choice == '2':
                        continue  # Replay current
                    elif choice == '3':
                        current_episode_idx = 0  # Reset to episode selection
                    elif choice == '4':
                        break  # Go back to season selection
                    elif choice == '5':
                        return  # Exit to main loop for new search
                    elif choice == 'q':
                        sys.exit(0)
                    else:
                        current_episode_idx += 1  # Default: next episode
                else:
                    self.notify("Finished last episode of the season", "INFO")
                    break
    
    def show_settings(self):
        """Display and modify settings"""
        while True:
            print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
            print(f"{Colors.HEADER}{Colors.BOLD}Settings{Colors.ENDC}")
            print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
            
            settings = [
                ('provider', 'Video Provider'),
                ('quality', 'Video Quality'),
                ('subs_language', 'Subtitle Language'),
                ('player', 'Media Player'),
                ('auto_next', 'Auto Play Next Episode'),
            ]
            
            for idx, (key, label) in enumerate(settings, 1):
                value = self.config.get(key)
                print(f"{Colors.OKCYAN}{idx}.{Colors.ENDC} {label}: {Colors.BOLD}{value}{Colors.ENDC}")
            
            print(f"{Colors.OKCYAN}b.{Colors.ENDC} Back to main menu")
            
            choice = input(f"\n{Colors.BOLD}Select setting to change: {Colors.ENDC}").strip().lower()
            
            if choice == 'b':
                return
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(settings):
                    key, label = settings[idx]
                    current_value = self.config.get(key)
                    
                    if isinstance(current_value, bool):
                        new_value = not current_value
                        self.config.set(key, new_value)
                        self.notify(f"{label} set to: {new_value}", "SUCCESS")
                    else:
                        new_value = input(f"\nEnter new value for {label} (current: {current_value}): ").strip()
                        if new_value:
                            self.config.set(key, new_value)
                            self.notify(f"{label} updated to: {new_value}", "SUCCESS")
            except (ValueError, IndexError):
                self.notify("Invalid selection", "WARNING")
    
    def show_main_menu(self):
        """Display main menu"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}🦞 Lobster - Movie & TV Show Streaming{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}1.{Colors.ENDC} Search for Movie/TV Show")
        print(f"{Colors.OKCYAN}2.{Colors.ENDC} Settings")
        print(f"{Colors.OKCYAN}3.{Colors.ENDC} About")
        print(f"{Colors.OKCYAN}q.{Colors.ENDC} Quit")
        print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    
    def show_about(self):
        """Display about information"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}About Lobster{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
        print(f"\n{Colors.OKGREEN}Version:{Colors.ENDC} 2.0")
        print(f"{Colors.OKGREEN}Description:{Colors.ENDC} A Python-based movie and TV show streaming application")
        print(f"{Colors.OKGREEN}Original:{Colors.ENDC} Based on lobster shell script by justchokingaround")
        print(f"{Colors.OKGREEN}Requirements:{Colors.ENDC} mpv (media player), requests, beautifulsoup4")
        print(f"\n{Colors.WARNING}Note:{Colors.ENDC} Use responsibly and according to your local laws.")
        input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
    
    def run(self):
        """Main application loop"""
        # Check player on startup
        if not self.check_player():
            self.notify(f"Warning: Media player '{self.config.get('player')}' not found!", "WARNING")
            self.notify("Please install mpv: https://mpv.io/installation/", "INFO")
            choice = input("\nContinue anyway? (y/n): ").strip().lower()
            if choice != 'y':
                sys.exit(1)
        
        while True:
            self.show_main_menu()
            choice = input(f"\n{Colors.BOLD}Your choice: {Colors.ENDC}").strip().lower()
            
            if choice == '1':
                # Search
                query = input(f"\n{Colors.BOLD}Search Movie/TV Show: {Colors.ENDC}").strip()
                
                if not query:
                    self.notify("No query provided", "WARNING")
                    continue
                
                # Search
                results = self.search(query)
                
                if not results:
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
                    
            elif choice == '2':
                self.show_settings()
                
            elif choice == '3':
                self.show_about()
                
            elif choice == 'q':
                self.notify("Thanks for using Lobster! Goodbye! 🦞", "SUCCESS")
                break
            else:
                self.notify("Invalid choice", "WARNING")


def main():
    """Entry point"""
    try:
        app = LobsterApp()
        app.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Interrupted by user. Goodbye!{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
        logger.exception("Unexpected error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
