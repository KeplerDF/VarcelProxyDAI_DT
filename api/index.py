from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        video_id = query_params.get('video_id', [None])[0]

        self.send_response(200 if video_id else 400)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        if not video_id:
            self.wfile.write(json.dumps({"error": "Missing video_id parameter"}).encode())
            return

        try:
            ytt_api = YouTubeTranscriptApi()

            # Fetch all available transcript tracks for the video
            transcript_list = ytt_api.list(video_id)

            # 1. Try manual English tracks first, then auto-generated English
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB', 'en-orig'])
            except NoTranscriptFound:
                # 2. Try any generated track, or translate the first available track to English
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except NoTranscriptFound:
                    first_available = next(iter(transcript_list))
                    transcript = first_available.translate('en')

            entries = transcript.fetch()

            formatted_entries = []
            for item in entries:
                formatted_entries.append({
                    "start": item['start'] if isinstance(item, dict) else item.start,
                    "duration": item.get('duration', 0.0) if isinstance(item, dict) else getattr(item, 'duration', 0.0),
                    "text": item['text'] if isinstance(item, dict) else item.text
                })

            self.wfile.write(json.dumps({"success": True, "entries": formatted_entries}).encode())

        except (TranscriptsDisabled, NoTranscriptFound) as e:
            self.wfile.write(json.dumps({"error": str(e), "entries": []}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e), "entries": []}).encode())