import sqlite3


def delete_all_saved_videos():
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()

    # Count entries before deleting
    cursor.execute("SELECT COUNT(*) FROM saved_videos")
    count = cursor.fetchone()[0]

    if count == 0:
        print("✅ No saved videos to delete.")
    else:
        cursor.execute("DELETE FROM saved_videos")
        print(f"🗑️ Deleted {count} saved videos from the database.")

    conn.commit()
    conn.close()


def delete_all_failed_videos():
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()

    # Count entries before deleting
    cursor.execute("SELECT * FROM failedVideos")
    count = cursor.fetchall()

    if count == 0:
        print("✅ No saved videos to delete.")
    else:
        cursor.execute("DELETE FROM failedVideos")
        print(f"🗑️ Deleted {count} failed videos from the database.")

    conn.commit()
    conn.close()


def print_and_clear_failed_videos():
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()

    cursor.execute("SELECT video_id, video_name, language, timestamp FROM failedVideos")
    failed = cursor.fetchall()

    failedList = []

    if not failed:
        print("✅ No failed videos in the database.")
    else:
        print("❌ Failed Videos:")
        for video_id, video_name, language, timestamp in failed:
            failedList.append(int(video_id))
            #print(f"- {video_name} | ID: {video_id} | Language: {language} | Time: {timestamp}")

        # Delete all failed records
        print(failedList)

    conn.commit()
    conn.close()



def print_and_clear_saved_videos():
    conn = sqlite3.connect("saved_videos.db")
    cursor = conn.cursor()

    cursor.execute("SELECT video_id, video_name FROM saved_videos")
    failed = cursor.fetchall()

    savedList = []

    if not failed:
        print("✅ No saved videos in the database.")
    else:
        print("❌ Saved Videos:")
        for video_id, video_name in failed:
            savedList.append(int(video_id))
            #print(f"- {video_name} | ID: {video_id} | Language: {language} | Time: {timestamp}")

        # Delete all failed records
        print(savedList)

    conn.commit()
    conn.close()



# print_and_clear_failed_videos()
# print_and_clear_saved_videos()
# delete_all_saved_videos()
# delete_all_failed_videos()
