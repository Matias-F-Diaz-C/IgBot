import os
import time
import datetime
import instaloader
import shutil
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http

# Parámetros globales
WATERMARK_IMAGE = "watermark.png"
UPLOAD_DESCRIPTION = "Video subido automáticamente"
ACCOUNTS = ["mysaintclo"]  # Lista de cuentas de Instagram
USERNAME = ""
PASSWORD = ""
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = 'token.json'


def authenticate_youtube():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    credentials = None
    
    if os.path.exists(TOKEN_FILE):
        credentials = google_auth_oauthlib.flow.Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not credentials:
        client_secrets_file = "W:/Programacion/igbot_repensado/client.json"
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
        credentials = flow.run_local_server()
        with open(TOKEN_FILE, "w") as token:
            token.write(credentials.to_json())
    
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)


def download_recent_instagram_videos(accounts, since_time):
    L = instaloader.Instaloader()
    
    try:
        L.load_session_from_file(USERNAME)
    except:
        L.login(USERNAME, PASSWORD)
    
    downloaded_videos = []
    
    for account in accounts:
        for _ in range(3):  # Intentar hasta 3 veces en caso de error
            try:
                profile = instaloader.Profile.from_username(L.context, account)
                break
            except instaloader.exceptions.ConnectionException:
                print("Error de conexión. Reintentando en 30 segundos...")
                time.sleep(30)
        
        for post in profile.get_posts():
            if post.is_video and post.date_utc > since_time:
                print(f"Descargando video {post.shortcode} de {account}")
                target_dir = account
                os.makedirs(target_dir, exist_ok=True)
                L.download_post(post, target=target_dir)
                video_path = os.path.join(target_dir, f"{post.shortcode}.mp4")
                if os.path.exists(video_path):
                    downloaded_videos.append({
                        'file_path': video_path,
                        'caption': post.caption or "",
                        'account': account
                    })
    
    return downloaded_videos


def upload_video_to_youtube(youtube, video_path, title, description):
    request_body = {
        "snippet": {
            "categoryId": "22",
            "title": title,
            "description": description,
            "tags": ["test", "python", "api"]
        },
        "status": {"privacyStatus": "private"}
    }
    
    media_file = googleapiclient.http.MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media_file)
    
    for _ in range(3):  # Intentar 3 veces en caso de fallo
        try:
            status, response = request.next_chunk()
            if status:
                print(f"Subida {int(status.progress() * 100)}% completada")
            if response:
                print(f"Video subido con ID: {response['id']}")
                return
        except googleapiclient.errors.HttpError as e:
            print(f"Error subiendo video: {e}. Reintentando en 10 segundos...")
            time.sleep(10)
    

def clean_up_files(file_list):
    for file in file_list:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Archivo eliminado: {file}")
        except Exception as e:
            print(f"Error al eliminar {file}: {e}")


def main():
    youtube = authenticate_youtube()
    since_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    
    downloaded_videos = download_recent_instagram_videos(ACCOUNTS, since_time)
    
    for video_info in downloaded_videos:
        video_path = video_info['file_path']
        caption = video_info['caption']
        account = video_info['account']
        title = caption if caption else f"Video de @{account}"
        description = f"{UPLOAD_DESCRIPTION}\n- Créditos: @{account}"
        upload_video_to_youtube(youtube, video_path, title, description)
    
    clean_up_files([info['file_path'] for info in downloaded_videos])
    
    for account in ACCOUNTS:
        if os.path.exists(account):
            shutil.rmtree(account)


if __name__ == "__main__":
    main()
