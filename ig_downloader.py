import instaloader
import time

loader = instaloader.Instaloader()

# Load profile posts
profile_name = "mysaintclo"
profile = instaloader.Profile.from_username(loader.context, profile_name)

for post in profile.get_posts():
    if post.is_video:
        loader.download_post(post, target=profile_name)
    time.sleep(20)
