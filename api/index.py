from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        video_id = query_params.get('video_id', [None])[0]

        if not video_id:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing video_id parameter"}).encode())
            return

        try:
            # Initialize API instance for modern youtube-transcript-api versions
            ytt = YouTubeTranscriptApi()

            # Fetch transcript using instance method with language preferences
            transcript_data = ytt.fetch(video_id, languages=['en', 'en-US', 'en-GB', 'en-orig'])

            # Convert Transcript objects to plain dictionaries
            entries = []
            for item in transcript_data:
                entries.append({
                    "start": item['start'] if isinstance(item, dict) else item.start,
                    "duration": item.get('duration', 0.0) if isinstance(item, dict) else getattr(item, 'duration', 0.0),
                    "text": item['text'] if isinstance(item, dict) else item.text
                })

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "entries": entries}).encode())

        except Exception as e:
            # Send explicit error message so Render receives exact failure cause
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e),
                "entries": []
            }).encode())