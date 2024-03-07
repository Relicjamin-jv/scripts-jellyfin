from jellyfin_apiclient_python import JellyfinClient
import re
import requests
from tqdm import tqdm
import jellyfish
import os

current_working_directory = os.getcwd()

# Create the client
client = JellyfinClient()
client.config.app("download_your_movies", "0.0.1", "THE_Machine", "512")
client.config.data["auth.ssl"] = True

server_url = ""
client.auth.connect_to_address(server_url)
client.auth.login(server_url, "username", "password")

items = client.jellyfin.search_media_items(media="Movie", limit=None)


def check_for_similar_file(filename):
    filenames = os.listdir(current_working_directory)

    for file in filenames:
        s = jellyfish.jaro_similarity(filename, file)

        if s > 0.95:
            return True

    return False


for item in items["Items"]:
    id = item["Id"]
    metadata = client.jellyfin.get_item(id)

    try:
        if metadata["IsHD"]:
            download_url = client.jellyfin.download_url(id)
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get("content-length", 0))
            content_disposition = response.headers.get(
                "content-disposition", "filename=missing_title.mp4"
            )
            filename = re.findall('filename="(.+)"', content_disposition)[0]

            if check_for_similar_file(filename):
                print(f"Skipping {filename}, similar file found")
                continue

            print(f"Downloading {filename}")
            with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
                with open(f"{filename}", mode="wb") as file:
                    for chunk in response.iter_content(chunk_size=10 * 1024):
                        progress_bar.update(len(chunk))
                        file.write(chunk)
                print(f"COMPLETED {filename}")
    except Exception:
        pass
