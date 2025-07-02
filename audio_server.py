from flask import Flask, jsonify, send_file
from flask_cors import CORS
import os
import glob
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Hardcoded relative path to audio files
AUDIO_BASE_PATH = "../habitican_hosting/habitican/sfx/"

# Valid difficulty directories
DIFFICULTY_LEVELS = ['easy', 'medium', 'hard', 'trivial']

def get_audio_files(directory_path):
    """Get all .ogg files in a directory"""
    if not os.path.exists(directory_path):
        return []
    
    ogg_files = glob.glob(os.path.join(directory_path, "*.ogg"))
    # Return just the filenames, not full paths
    return [os.path.basename(f) for f in ogg_files]

@app.route('/audio/list', methods=['GET'])
def list_all_audio():
    """Return a list of all available audio files organized by difficulty"""
    audio_files = {}
    
    for level in DIFFICULTY_LEVELS:
        level_path = os.path.join(AUDIO_BASE_PATH, level)
        audio_files[level] = get_audio_files(level_path)
    
    return jsonify({
        'audio_files': audio_files,
        'base_path': AUDIO_BASE_PATH
    })

@app.route('/audio/<level>', methods=['GET'])
def list_audio_by_level(level):
    """Return audio files for a specific difficulty level"""
    if level not in DIFFICULTY_LEVELS:
        return jsonify({
            'error': f'Invalid level. Must be one of: {DIFFICULTY_LEVELS}',
            'received': level
        }), 400
    
    level_path = os.path.join(AUDIO_BASE_PATH, level)
    files = get_audio_files(level_path)
    
    return jsonify({
        'level': level,
        'files': files,
        'count': len(files)
    })

@app.route('/audio/<level>/<filename>', methods=['GET'])
def serve_audio_file(level, filename):
    """Serve a specific audio file"""
    if level not in DIFFICULTY_LEVELS:
        return jsonify({'error': 'Invalid difficulty level'}), 400
    
    if not filename.endswith('.ogg'):
        return jsonify({'error': 'Only .ogg files are supported'}), 400
    
    file_path = os.path.join(AUDIO_BASE_PATH, level, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, mimetype='audio/ogg')

@app.route('/audio/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Check if base audio directory exists
    exists = os.path.exists(AUDIO_BASE_PATH)
    
    # Count total files
    total_files = 0
    for level in DIFFICULTY_LEVELS:
        level_path = os.path.join(AUDIO_BASE_PATH, level)
        total_files += len(get_audio_files(level_path))
    
    return jsonify({
        'status': 'healthy' if exists else 'audio_directory_missing',
        'audio_path_exists': exists,
        'total_audio_files': total_files,
        'levels_checked': DIFFICULTY_LEVELS
    })

if __name__ == '__main__':
    print("Starting Audio Server...")
    print(f"Looking for audio files in: {os.path.abspath(AUDIO_BASE_PATH)}")
    print("Expected directory structure:")
    for level in DIFFICULTY_LEVELS:
        level_path = os.path.join(AUDIO_BASE_PATH, level)
        print(f"  {level_path}/")
        if os.path.exists(level_path):
            files = get_audio_files(level_path)
            if files:
                for file in files:
                    print(f"    ✅ {file}")
            else:
                print(f"    📁 (empty)")
        else:
            print(f"    ❌ (missing)")
    
    print("\nAvailable endpoints:")
    print("  GET /audio/list - List all audio files by difficulty")
    print("  GET /audio/<level> - List files for specific difficulty")
    print("  GET /audio/<level>/<filename> - Serve specific audio file")
    print("  GET /audio/health - Health check")
    print("\nAudio Server running on http://localhost:5001")
    
    app.run(debug=True, host='localhost', port=5001)