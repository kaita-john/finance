import asyncio
import os
import sqlite3
import time
import vimeo
from typing import List

import httpx
import requests

# === VTTxAITranslator ===

xai_key = ""
base_url = "https://api.x.ai/v1"


class VTTxAITranslator:
    def __init__(self, model="grok-3", batch_size=50, language='fr', max_retries=3):
        self.model = model
        self.batch_size = batch_size  # Kept for compatibility, though not used for translation
        self.language = language
        self.max_retries = max_retries
        print(
            f"📋 Initializing VTTxAITranslator: model={model}, batch_size={batch_size}, language={language}, max_retries={max_retries}")

    async def translate_batch(self, lines: List[str]) -> List[str]:
        print(f"🌐 Starting translation for {len(lines)} lines to {self.language}")
        numbered_lines = [f"{i + 1}. {line}" for i, line in enumerate(lines)]
        prompt = (
                f"Translate the following English text to {self.language}, using standard musical terminology used by violinists. "
                f"Return exactly {len(lines)} lines, one translation per line, maintaining the same order and number of lines as the input. "
                f"Do not combine lines or add extra text. Each line should correspond to the numbered input line:\n"
                + "\n".join(numbered_lines)
        )
        for attempt in range(self.max_retries):
            print(f"🔄 Attempt {attempt + 1}/{self.max_retries} for translation")
            async with httpx.AsyncClient(headers={"Authorization": f"Bearer {xai_key}"}) as client:
                try:
                    print(f"📤 Sending translation request to API")
                    response = await client.post(
                        f"{base_url}/chat/completions",
                        json={
                            "model": self.model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        f"Translate the provided English text to {self.language}, using standard musical terminology used by violinists. "
                                        f"Return exactly one translation per input line, maintaining the same number of lines and order. "
                                        f"Do not combine lines or add extra text."
                                    )
                                },
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.2,
                        },
                        timeout=1060.0
                    )
                    response.raise_for_status()
                    output = response.json()["choices"][0]["message"]["content"].strip()
                    print(f"📥 Raw API response (first 100 chars): {output[:100]}...")

                    translated_lines = output.split('\n')
                    cleaned_lines = []
                    for line in translated_lines:
                        cleaned_line = line.strip()
                        if cleaned_line and cleaned_line[0].isdigit() and '.' in cleaned_line[:3]:
                            cleaned_line = cleaned_line[cleaned_line.index('.') + 1:].strip()
                        cleaned_lines.append(cleaned_line)
                    print(f"📥 Received {len(cleaned_lines)} translated lines")
                    if  (len(lines) - len(cleaned_lines)) <= 1:
                        print(f"✅ Translation successful")
                        return cleaned_lines
                    print(f"❌ Line count mismatch: expected {len(lines)}, got {len(cleaned_lines)}")
                    with open(f"failed_translation_{self.language}_{time.time()}.txt", "w", encoding="utf-8") as f:
                        f.write(
                            f"Input lines ({len(lines)}):\n{chr(10).join(lines)}\n\nOutput lines ({len(cleaned_lines)}):\n{output}")
                    if attempt < self.max_retries - 1:
                        print(f"🔄 Retrying due to line count mismatch")
                        await asyncio.sleep(3)
                        continue
                    print(f"🔄 Retrying failed translation line by line")
                    translated_lines = []
                    for i, line in enumerate(lines):
                        print(f"📦 Translating line {i + 1}/{len(lines)} individually")
                        sub_translated = await self.translate_batch([line])
                        if len(sub_translated) != 1:
                            raise ValueError(
                                f"Line {i + 1} translation failed: expected 1 line, got {len(sub_translated)}")
                        translated_lines.append(sub_translated[0])
                    print(f"✅ Line-by-line translation successful")
                    return translated_lines
                except Exception as e:
                    print(f"❌ Error during translation attempt {attempt + 1}: {e}")
                    if attempt < self.max_retries - 1:
                        print(f"⏳ Waiting 3 seconds before retry")
                        await asyncio.sleep(3)
                    else:
                        print(f"🔄 Max retries reached, retrying line by line")
                        translated_lines = []
                        for i, line in enumerate(lines):
                            print(f"📦 Translating line {i + 1}/{len(lines)} individually")
                            sub_translated = await self.translate_batch([line])
                            if len(sub_translated) != 1:
                                raise ValueError(
                                    f"Line {i + 1} translation failed: expected 1 line, got {len(sub_translated)}")
                            translated_lines.append(sub_translated[0])
                        print(f"✅ Line-by-line translation successful")
                        return translated_lines
        raise ValueError(f"Translation failed for {len(lines)} lines after retries and line-by-line attempts")

    def process_vtt_lines(self, content: str):
        lines = content.splitlines()
        empty_lines = []
        position_numbers = []
        timestamp_lines = []
        content_lines = []
        content_indices = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                empty_lines.append(i)
            elif '-->' in stripped:
                timestamp_lines.append((i, stripped))
            elif stripped.isdigit():
                position_numbers.append((i, stripped))
            elif stripped != 'WEBVTT':
                content_lines.append(stripped)
                content_indices.append(i)

        return empty_lines, position_numbers, timestamp_lines, content_lines, content_indices

    async def translate_file(self, input_file, output_file):
        print(f"📄 Starting translation of file: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"📖 Read {len(content.splitlines())} lines from input file")

        empty_lines, position_numbers, timestamp_lines, content_lines, content_indices = self.process_vtt_lines(content)
        print(f"📏 Empty lines: {empty_lines}")
        print(f"🔢 Position numbers: {position_numbers}")
        print(f"⏰ Timestamp lines: {timestamp_lines}")
        print(f"🗣️ Content lines: {len(content_lines)} at positions: {content_indices}")

        # Send the entire content_lines list to the API
        print(f"📦 Sending all {len(content_lines)} content lines for translation")
        try:
            translated_lines = await self.translate_batch(content_lines)
            print(f"✅ Received {len(translated_lines)} translated lines")
        except ValueError as e:
            print(f"❌ Translation failed: {e}")
            return None  # Return None to indicate failure and move to next video

        if len(translated_lines) != len(content_lines):
            print(
                f"❌ Error: Translated line count ({len(translated_lines)}) does not match input ({len(content_lines)})")
            return None  # Return None to indicate failure and move to next video

        # Reconstruct the file
        output_lines = [''] * len(content.splitlines())
        output_lines[0] = 'WEBVTT'  # Ensure WEBVTT is first
        for idx in empty_lines:
            output_lines[idx] = ''  # Preserve empty lines
        for idx, num in position_numbers:
            output_lines[idx] = num  # Preserve position numbers
        for idx, timestamp in timestamp_lines:
            output_lines[idx] = timestamp  # Preserve timestamps
        for idx, translated_text in zip(content_indices, translated_lines):
            output_lines[idx] = translated_text  # Insert translated content

        print(f"📝 Writing translated lines to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines) + '\n')
        print(f"✅ File translation completed: {output_file}")

        return output_lines  # Return the content for inspection


# === Helper Functions ===

VIMEO_ACCESS_TOKEN = "17067378d4977fa10bb0f58f0dd3382c"
client = vimeo.VimeoClient(token=VIMEO_ACCESS_TOKEN)


def init_db():
    print("💾 Initializing database")
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT UNIQUE,
            video_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS failedVideos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            video_name TEXT,
            language TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized with saved_videos and failedVideos tables")


def count_vtt_lines(file_path=None, content=None):
    print(f"🔢 Counting lines in VTT file: {file_path if file_path else 'content'}")
    try:
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        if content:
            lines = content.splitlines()
            text_lines = 0
            for line in lines:
                line = line.strip()
                if not line or line.isdigit() or "-->" in line or line == "WEBVTT":
                    continue
                text_lines += 1
            print(f"✅ Found {text_lines} text lines in VTT file")
            return text_lines
        else:
            raise ValueError("No content provided to count lines")
    except Exception as e:
        print(f"❌ Failed to count lines: {e}")
        return -1


def save_failed_video(video_id, video_name, language):
    print(f"💾 Saving failed video: ID={video_id}, Name={video_name}, Language={language}")
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO failedVideos (video_id, video_name, language)
        VALUES (?, ?, ?)
    """, (video_id, video_name, language))
    conn.commit()
    conn.close()
    print(f"✅ Failed video saved to database")


def handle_new_file(filepath, file_id, language_name, short_form):
    print(f"📤 Uploading new subtitle file: {filepath} for video {file_id}")
    video_uri = f"/videos/{file_id}"
    text_tracks_uri = f"{video_uri}/texttracks"
    print(f"🔍 Checking existing text tracks for video {file_id}")
    existing_tracks = client.get(text_tracks_uri).json().get("data", [])
    time.sleep(3)  # Small pause for safety
    for track in existing_tracks:
        if track["language"] == short_form and track["type"] == "subtitles":
            print(f"ℹ️ Subtitles for {language_name} ({short_form}) already exist, skipping upload")
            return
    caption_payload = {
        "type": "subtitles",
        "language": short_form,
        "name": f"{language_name} Captions"
    }
    print(f"📤 Creating new text track for {language_name}")
    time.sleep(3)  # Small pause for safety
    caption_data = client.post(text_tracks_uri, data=caption_payload).json()
    upload_link = caption_data['link']
    text_track_uri = caption_data['uri']
    print(f"📤 Uploading VTT content to Vimeo")
    with open(filepath, 'rb') as f:
        vtt_content = f.read()
    requests.put(upload_link, headers={"Accept": "application/vnd.vimeo.*+json;version=3.4"}, data=vtt_content)
    print(f"✅ VTT content uploaded successfully")
    client.patch(text_track_uri, data={"active": True})
    print(f"✅ Text track activated for {language_name}")


def save_video_name_to_db(video_id, video_name):
    print(f"💾 Saving video to database: ID={video_id}, Name={video_name}")
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO saved_videos (video_id, video_name)
        VALUES (?, ?)
    """, (video_id, video_name))
    conn.commit()
    conn.close()
    print(f"✅ Video saved to database")


def get_video_data(video_id):
    print(f"📡 Fetching video data for ID: {video_id}")
    time.sleep(2)
    response = client.get(f'/videos/{video_id}')
    print(f"✅ Video data retrieved successfully")
    return response.json()


def get_text_tracks(video_id):
    time.sleep(1)
    print(f"📡 Fetching text tracks for video ID: {video_id}")
    response = client.get(f'/videos/{video_id}/texttracks')
    print(f"✅ Text tracks retrieved successfully")
    return response.json().get("data", [])


def download_caption_file(download_link, file_path):
    print(f"⬇️ Downloading captions: {file_path}")
    full_file_path = os.path.join("violinlab_files", file_path)
    os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
    response = requests.get(download_link, timeout=60)
    with open(full_file_path, "wb") as f:
        f.write(response.content)
    print(f"✅ Captions downloaded to: {full_file_path}")
    return full_file_path


def is_video_saved(video_id, video_name):
    print(f"🔍 Checking if video is saved: ID={video_id}, Name={video_name}")
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM saved_videos WHERE video_id = ? AND video_name = ?", (video_id, video_name))
    result = cursor.fetchone()
    conn.close()
    if result:
        print(f"ℹ️ Video already processed and saved")
    else:
        print(f"ℹ️ Video not found in database, proceeding with processing")
    return result is not None


# === Main Async Flow ===

async def translate_vtt_with_xai(input_file, source_language_name, source_short_form, target_language_name,
                                 target_short_form, video_id):
    print(
        f"\n---------------------------- TRANSLATING SUBTITLES TO {target_language_name.upper()} FOR VIDEO ID: {video_id} ----------------------------")
    input_path = os.path.join("violinlab_files", input_file)
    output_file = input_file.replace(f"_{source_short_form}.vtt", f"_{target_short_form}.vtt")
    output_path = os.path.join("violinlab_files", output_file)
    print(f"📄 Input file: {input_path}")
    print(f"📄 Output file: {output_path}")
    translator = VTTxAITranslator(language=target_short_form, max_retries=3)
    output_lines = await translator.translate_file(input_path, output_path)
    if output_lines is None:
        print(f"❌ Translation failed for video {video_id}, moving to next video")
        return None, 0, 0
    print(f"🔢 Counting lines for validation")
    orig_lines = count_vtt_lines(file_path=input_path)
    trans_lines = count_vtt_lines(file_path=output_path)
    if (orig_lines - trans_lines) >= 2:
        print(f"❌ Validation failed: Original lines ({orig_lines}) != Translated lines ({trans_lines})")
        return None, orig_lines, trans_lines
    print(f"✅ Validation passed: Original lines ({orig_lines}) = Translated lines ({trans_lines})")
    return output_path, orig_lines, trans_lines


async def mainFlow_async(VIDEO_ID):
    print(f"\n---------------------------- PROCESSING VIDEO {VIDEO_ID} ----------------------------")
    print(f"📡 Fetching video data")
    video_data = get_video_data(VIDEO_ID)
    video_name = video_data["name"]
    print(f"ℹ️ Video name: {video_name}")
    print(f"📡 Checking for English captions")
    text_tracks = get_text_tracks(VIDEO_ID)
    en_caption = next((track for track in text_tracks if track["language"] in ["en", "en-x-autogen"]), None)
    if not en_caption:
        print(f"❌ No English captions found for video {VIDEO_ID}")
        return False
    source_language_name = "English"
    source_short_form = "en"
    source_file_name = f"{VIDEO_ID}_{video_name}_{source_short_form}.vtt"
    print(f"⬇️ Downloading English captions")
    download_caption_file(en_caption["link"], source_file_name)
    source_lines = count_vtt_lines(file_path=os.path.join("violinlab_files", source_file_name))
    print(f"ℹ️ English caption lines: {source_lines}")
    languages = [
        ('French', 'fr'),
        ('Portuguese', 'pt'),
        ('Chinese', 'zh')
    ]
    results = []
    for lang_name, lang_code in languages:
        print(f"\n---------------------------- TRANSLATING TO {lang_name.upper()} ----------------------------")
        try:
            translated_path, orig, trans = await translate_vtt_with_xai(source_file_name, source_language_name,
                                                                        source_short_form, lang_name, lang_code,
                                                                        VIDEO_ID)
            # if not translated_path or orig != trans:
            if not translated_path:
                print(f"❌ Translation to {lang_name} failed")
                save_failed_video(VIDEO_ID, video_name, lang_name)
                return False
            print(f"✅ Translation to {lang_name} successful")
            results.append((translated_path, lang_name, lang_code))
        except Exception as e:
            print(f"❌ Error during {lang_name} translation: {e}")
            save_failed_video(VIDEO_ID, video_name, lang_name)
            return False
    for translated_path, lang_name, lang_code in results:
        print(f"\n---------------------------- UPLOADING {lang_name.upper()} SUBTITLES ----------------------------")
        try:
            handle_new_file(translated_path, VIDEO_ID, lang_name, lang_code)
            print(f"✅ Successfully uploaded {lang_name} subtitles")
        except Exception as e:
            print(f"❌ Error uploading {lang_name} subtitles: {e}")
            save_failed_video(VIDEO_ID, video_name, lang_name)
            return False
    print(f"💾 Saving video metadata to database")
    save_video_name_to_db(VIDEO_ID, video_name)
    print(f"✅ Video {VIDEO_ID} processing completed successfully")
    return True


async def get_all_video_names_async():
    videoList = [1023990820, 242120638, 1013867720, 1032028999,]
    print(f"\n---------------------------- STARTING VIDEO PROCESSING ----------------------------")
    print(f"ℹ️ Total videos to process: {len(videoList)}")
    init_db()
    success_count = 0
    fail_count = 0
    for i, videoId in enumerate(videoList, 1):
        print(
            f"\n---------------------------- PROCESSING VIDEO {i}/{len(videoList)} (ID: {videoId}) ----------------------------")
        try:
            video_data = get_video_data(videoId)
            video_name = video_data["name"]
            print(f"ℹ️ Video name: {video_name}")
            if is_video_saved(videoId, video_name):
                print(f"⏭️ Skipping video {videoId} as it's already processed")
                success_count += 1
                continue
            success = await mainFlow_async(videoId)
            if success:
                success_count += 1
                print(f"✅ Completed processing video {videoId}")
            else:
                fail_count += 1
                print(f"❌ Failed processing video {videoId}, moving to next video")
        except Exception as e:
            print(f"❌ Error processing video {videoId}: {e}")
            fail_count += 1
            print(f"❌ Failed processing video {videoId}, moving to next video")
    print(f"\n---------------------------- FINISHED PROCESSING ALL VIDEOS ----------------------------")
    print(f"✅ Total videos processed successfully: {success_count}")
    print(f"❌ Total videos failed: {fail_count}")


# === Run ===

if __name__ == "__main__":
    print("🚀 Starting subtitle translation pipeline")
    asyncio.run(get_all_video_names_async())
    print("🏁 Pipeline completed")
