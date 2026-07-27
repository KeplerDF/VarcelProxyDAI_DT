from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse video_id from URL query params (e.g. /?video_id=pb9VfCG7_XU)
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
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)

            # Try English first, otherwise translate available track to English
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US'])
            except NoTranscriptFound:
                first_available = next(iter(transcript_list))
                transcript = first_available.translate('en')

            entries = transcript.fetch()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "entries": entries}).encode())

        except (TranscriptsDisabled, NoTranscriptFound):
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "No transcripts found for this video"}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())