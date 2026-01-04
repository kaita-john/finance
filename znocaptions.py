import sqlite3
import webbrowser


def delete_all_nocaptions_videos():
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()

    # Count entries before deleting
    cursor.execute("SELECT COUNT(*) FROM no_captions")
    count = cursor.fetchone()[0]

    if count == 0:
        print("✅ No saved videos to delete.")
    else:
        cursor.execute("DELETE FROM no_captions")
        print(f"🗑️ Deleted {count} no caption videos from the database.")

    conn.commit()
    conn.close()

def print_and_clear_nocaption_videos():
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()

    cursor.execute("SELECT video_id, video_name FROM no_captions")
    failed = cursor.fetchall()

    failedList = []

    if not failed:
        print("✅ No No caption videos in the database.")
    else:
        print("❌ No caption Videos:")
        for video_id, video_name in failed:
            failedList.append(int(video_id))
            #print(f"- {video_name} | ID: {video_id} | Language: {language} | Time: {timestamp}")

        # Print all no caption records
        print(failedList)

    conn.commit()
    conn.close()


def print_named_nocaption_videos():
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()

    cursor.execute("SELECT video_id, video_name FROM no_captions")
    videos = cursor.fetchall()

    if not videos:
        print("✅ No No caption videos in the database.")
    else:
        print("📋 No Caption Videos (Named List):")
        for idx, (video_id, video_name) in enumerate(videos, start=1):
            print(f"{idx}. {video_name} - ({video_id})")

    conn.close()


def get_nocaption_video_urls():
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()

    cursor.execute("SELECT video_id FROM no_captions")
    video_ids = cursor.fetchall()

    urls = [f"https://vimeo.com/{video_id[0]}" for video_id in video_ids]

    if not urls:
        print("✅ No No caption videos in the database.")
    else:
        print("🌐 Video URLs:")
        for index, url in enumerate(urls):
            print(url)

        urls_to_open = urls[31:40]
        if not urls_to_open:
            print("No URLs found in the specified range (1-10).")
        else:
            for index, url in enumerate(urls_to_open):
                webbrowser.open_new_tab(url)
                # Adjust printed index to reflect original list index + 1 (since we started from index 1 of the slice)
                print(f"Opening URL at original index {index + 1}: {url}")

    conn.close()
    return urls


# get_nocaption_video_urls()
# print_and_clear_nocaption_videos()
# print_named_nocaption_videos()
# delete_all_nocaptions_videos()



