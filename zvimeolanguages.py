import vimeo

# === Config ===
VIMEO_ACCESS_TOKEN = "17067378d4977fa10bb0f58f0dd3382c"
client = vimeo.VimeoClient(token=VIMEO_ACCESS_TOKEN)


def get_supported_languages():
    """
    Fetch all supported languages for Vimeo text tracks (captions/subtitles).
    Returns a list of language objects with code and name.
    """
    try:
        response = client.get(
            '/languages',
            params={
                'fields': 'code,name'  # Fetch only code and name
            }
        )
        if response.status_code != 200:
            print(f"Error fetching languages: Status code {response.status_code}: {response.text}")
            return []

        data = response.json()
        languages = data.get('data', [])

        for lang in languages:
            print(f"Language: {lang['name']} (Code: {lang['code']})")

        return languages

    except Exception as e:
        print(f"Error fetching languages: {str(e)}")
        return []


def main():
    print("Fetching supported languages for Vimeo text tracks...")
    languages = get_supported_languages()

    if languages:
        print(f"\nTotal languages found: {len(languages)}")
        with open('vimeo_languages.txt', 'w', encoding='utf-8') as f:
            for lang in languages:
                f.write(f"{lang['name']}: {lang['code']}\n")
        print("Languages saved to 'vimeo_languages.txt'")
    else:
        print("No languages found or error occurred. Check your access token and scopes.")


if __name__ == "__main__":
    main()
