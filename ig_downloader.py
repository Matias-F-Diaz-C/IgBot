import instaloader
import os
import time

PROFILE_NAME = "mysaintclo"
SESSION_FILE = "session-instagram"
DOWNLOAD_DIR = "downloads"

loader = instaloader.Instaloader()

try:
    loader.load_session_from_file(PROFILE_NAME, SESSION_FILE)
except FileNotFoundError:
    pass

try:
    profile = instaloader.Profile.from_username(loader.context, PROFILE_NAME)
except instaloader.exceptions.InstaloaderException as e:
    print(f"Error: {e}")
    exit()

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

for post in profile.get_posts():
    if post.is_video:
        filename = f"{DOWNLOAD_DIR}/{post.shortcode}.mp4"
        if not os.path.exists(filename):
            try:
                loader.download_post(post, target=DOWNLOAD_DIR)
            except Exception as e:
                print(f"Error descargando {post.shortcode}: {e}")
    time.sleep(10)
