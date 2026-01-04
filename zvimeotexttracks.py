import vimeo

# Set your Vimeo access token here
VIMEO_ACCESS_TOKEN = "17067378d4977fa10bb0f58f0dd3382c"
client = vimeo.VimeoClient(token=VIMEO_ACCESS_TOKEN)


def get_text_tracks(video_id):
    """
    Fetches and returns all text tracks for a given Vimeo video ID.

    :param video_id: str or int – Vimeo video ID
    :return: list of dicts – text track data
    """
    uri = f"/videos/{video_id}/texttracks"
    response = client.get(uri)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch text tracks: {response.status_code} - {response.text}")

    return response.json().get("data", [])


def print_text_tracks(video_id):
    """
    Prints all text track details for a given Vimeo video ID.

    :param video_id: str or int – Vimeo video ID
    """
    tracks = get_text_tracks(video_id)

    if not tracks:
        print("❌ No text tracks found for this video.")
        return

    print(f"🎬 Text Tracks for Video ID {video_id}:")
    for i, track in enumerate(tracks, start=1):
        print(f"\n--- Track {i} ---")
        print(f"ID         : {track['uri'].split('/')[-1]}")
        print(f"Language   : {track['language']}")
        print(f"Type       : {track['type']}")
        print(f"Name       : {track.get('name', 'N/A')}")
        print(f"Active     : {track.get('active', False)}")
        print(f"Link       : {track['link']}")
        print(f"URI        : {track['uri']}")




video_id = "503662069"
print_text_tracks(video_id)
