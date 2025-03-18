import os
import datetime
import instaloader
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip
import subprocess
import shutil

import google_auth_httplib2
import google_auth_oauthlib
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http

# Parámetros globales
WATERMARK_IMAGE = "watermark.png"  # Ruta a tu imagen de marca de agua
upload_description = "Video subido automáticamente"
ACCOUNTS = ["mysaintclo"]    # Lista de nombres de usuario de Instagram    tiktokgirls10001
USERNAME = ""
PASSWORD = "" 

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = 'token.json'



def authenticate_youtube():
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

	if os.path.exists(TOKEN_FILE):
		os.remove(TOKEN_FILE)

	# Load client secrets file, put the path of your file
	client_secrets_file = "W:/Programacion/igbot_repensado/client.json"

	
	flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
		client_secrets_file, SCOPES)
	credentials = flow.run_local_server()

	youtube = googleapiclient.discovery.build(
		"youtube", "v3", credentials=credentials)

	return youtube

def download_recent_instagram_videos(accounts, since_time):
	"""
	Descarga los videos de Instagram publicados desde 'since_time' para cada cuenta.
	Retorna una lista de diccionarios con la información: ruta del video, caption y cuenta.
	"""
	L = instaloader.Instaloader(download_video_thumbnails=False,
								save_metadata=False,
								download_comments=False)
	# Forzar un User-Agent móvil
	
	try:
		L.load_session_from_file(USERNAME)
		print("Logged in with file")
	except:
		L.login(USERNAME, PASSWORD)  
		print("Logged in with password")


	downloaded_videos = []  # Lista de diccionarios: {'file_path': ..., 'caption': ..., 'account': ...}

	for account in accounts:
		#try:
			print("INtentando procesar")
			profile = instaloader.Profile.from_username(L.context, account)
			print(f"Procesando cuenta: {account}")
			all_posts = profile.get_posts()
			for post in all_posts:
				# Verificar que sea video y que se haya publicado en la última hora
				print (post.title, ":",  post.date_utc, ":::::", since_time)
				if post.is_video:
					print(f"Descargando video {post.shortcode} publicado el {post.date_utc}")
					target_dir = account
					if not os.path.exists(target_dir):
						os.makedirs(target_dir)
					# Descarga el post en el directorio de la cuenta
					L.download_post(post, target=target_dir)
					# Los archivos descargados suelen llamarse "{shortcode}.mp4" o "{shortcode}_0.mp4"
					posibles = [os.path.join(target_dir, f"{post.shortcode}.mp4"),
								os.path.join(target_dir, f"{post.shortcode}_0.mp4")]
					for file_path in posibles:
						if os.path.exists(file_path):
							downloaded_videos.append({
								'file_path': file_path,
								'caption': post.caption if post.caption else "",
								'account': account
							})
							break
		#except Exception as e:
		#	print(f"Error al procesar la cuenta {account}: {e}")
	return downloaded_videos

def add_watermark_to_video(video_path, watermark_path):
	"""
	Agrega la marca de agua al video indicado y genera un nuevo archivo.
	Retorna la ruta del video con marca de agua.
	"""
	try:
		video = VideoFileClip(video_path)
		watermark = ImageClip(watermark_path)

		# Ajusta el tamaño de la marca de agua (modifica según convenga)
		watermark = watermark.resize(height=50)
		video_w, video_h = video.size
		wm_w, wm_h = watermark.size

		# Posición: esquina inferior derecha con un margen de 10px
		watermark = watermark.set_position((video_w - wm_w - 10, video_h - wm_h - 10))
		watermark = watermark.set_duration(video.duration)

		final_clip = CompositeVideoClip([video, watermark])
		output_path = f"watermarked_{os.path.basename(video_path)}"
		final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

		video.close()
		watermark.close()
		final_clip.close()

		return output_path
	except Exception as e:
		print(f"Error al agregar la marca de agua a {video_path}: {e}")
		return None

def upload_video_to_youtube(youtube,video_path, title, description):
	"""
	Sube el video a YouTube usando la api oficial
	"""
	try:
		request_body = {
			"snippet": {
				"categoryId": "22",
				"title": title,
				"description": description,
				"tags": ["test","python", "api" ]
			},
			"status":{
				"privacyStatus": "private"
			}
		}

		# put the path of the video that you want to upload
		media_file = video_path

		request = youtube.videos().insert(
			part="snippet,status",
			body=request_body,
			media_body=googleapiclient.http.MediaFileUpload(media_file, chunksize=-1, resumable=True)
		)

		response = None 

		while response is None:
			status, response = request.next_chunk()
			if status:
				print(f"Upload {int(status.progress()*100)}%")

			print(f"Video uploaded with ID: {response['id']}")
	except Exception as e:
		print(f"Error al subir el video {video_path}: {e}")

def clean_up_files(file_list):
	"""Elimina de disco los archivos indicados."""
	for file in file_list:
		try:
			if os.path.exists(file):
				os.remove(file)
				print(f"Archivo eliminado: {file}")
		except Exception as e:
			print(f"Error al eliminar el archivo {file}: {e}")

def clean_up_directories(directories):
	"""Elimina de disco los directorios indicados."""
	for directory in directories:
		try:
			if os.path.exists(directory):
				shutil.rmtree(directory)
				print(f"Directorio eliminado: {directory}")
		except Exception as e:
			print(f"Error al eliminar el directorio {directory}: {e}")

def main():

	youtube_key = authenticate_youtube()

	# Calcula la hora desde la que se consideran nuevos (última hora en UTC usando objetos timezone-aware)
	one_hour_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)

	# Descarga los videos recientes de todas las cuentas
	downloaded_videos_info = download_recent_instagram_videos(ACCOUNTS, one_hour_ago.replace(tzinfo=None))
	watermarked_files = []

	for video_info in downloaded_videos_info:
		video_path = video_info['file_path']
		caption = video_info['caption']
		account = video_info['account']

		# Construir título para YouTube:
		youtube_title = caption if caption else f"Video de @{account}"
		upload_description = f"{UPLOAD_DESCRIPTION}\n- Créditos: @{account}"


		# Agrega la marca de agua
		#wm_video = add_watermark_to_video(video_path, WATERMARK_IMAGE)
		#if wm_video:
			#watermarked_files.append(wm_video)
			# Sube el video procesado a YouTube con el título generado
			#upload_video_to_youtube(youtube_key, wm_video, youtube_title, upload_description)
		
		# Sube el video
		if video_path:
			watermarked_files.append(video_path)
			upload_video_to_youtube(youtube_key, video_path, youtube_title, upload_description)
	# Limpieza: elimina videos descargados y procesados
	downloaded_file_paths = [info['file_path'] for info in downloaded_videos_info]
	clean_up_files(downloaded_file_paths + watermarked_files)

	# Opcional: elimina los directorios creados para cada cuenta
	for account in ACCOUNTS:
		if os.path.exists(account):
			clean_up_directories([account])

if __name__ == "__main__":
	main()