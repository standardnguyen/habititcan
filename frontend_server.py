#!/usr/bin/env python3
import http.server
import socketserver
import os

# Configuration
PORT = 3000
DIRECTORY = "."  # Current directory

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        # If requesting root, serve frontend.html
        if self.path == '/':
            self.path = '/frontend.html'
        return super().do_GET()

if __name__ == "__main__":
    # Check if frontend.html exists
    if not os.path.exists('frontend.html'):
        print("Error: frontend.html not found in current directory")
        exit(1)
    
    print(f"Starting server at http://localhost:{PORT}")
    print(f"Serving files from: {os.path.abspath(DIRECTORY)}")
    print(f"Your HTML file will be available at:")
    print(f"  - http://localhost:{PORT}/")
    print(f"  - http://localhost:{PORT}/frontend.html")
    print("\nPress Ctrl+C to stop the server")
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")