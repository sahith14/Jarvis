import urllib.request
import urllib.parse
import re

def get_youtube_video_id_fast(query):
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    html = urllib.request.urlopen(req, timeout=3).read().decode('utf-8')
    match = re.search(r'"videoRenderer":\{"videoId":"([a-zA-Z0-9_-]{11})"', html)
    if match:
        return match.group(1)
    
    # Fallback to the generic one
    match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
    if match:
        return match.group(1)
    
    return None

print("Result:", get_youtube_video_id_fast("rick roll"))
