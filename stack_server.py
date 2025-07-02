from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# In-memory stack storage
stack = []

# Valid difficulty levels
VALID_LEVELS = ['trivial', 'hard', 'easy', 'medium']

@app.route('/stack', methods=['POST'])
def add_to_stack():
    """Add an item to the stack via POST request"""
    # Try to get the level from JSON data first, then from URL parameters
    data = request.get_json()
    if data and 'level' in data:
        level = data['level']
    else:
        level = request.args.get('level')
    
    # Validate the level
    if level not in VALID_LEVELS:
        return jsonify({
            'error': f'Invalid level. Must be one of: {VALID_LEVELS}',
            'received': level
        }), 400
    
    # Add to stack
    stack.append(level)
    
    return jsonify({
        'message': f'Added "{level}" to stack',
        'stack_size': len(stack),
        'current_stack': stack.copy()
    }), 201

@app.route('/stack', methods=['GET'])
def get_and_clear_stack():
    """Return the stack in order received and clear it"""
    # Get the level parameter (though the behavior is the same regardless)
    level = request.args.get('level')
    
    # Validate the level if provided
    if level and level not in VALID_LEVELS:
        return jsonify({
            'error': f'Invalid level. Must be one of: {VALID_LEVELS}',
            'received': level
        }), 400
    
    # Get current stack and clear it
    current_stack = stack.copy()
    stack.clear()
    
    return jsonify({
        'message': 'Stack retrieved and cleared',
        'stack': current_stack,
        'stack_size': len(current_stack)
    }), 200

@app.route('/stack/status', methods=['GET'])
def get_stack_status():
    """Get current stack status without clearing it"""
    return jsonify({
        'current_stack': stack.copy(),
        'stack_size': len(stack)
    }), 200

if __name__ == '__main__':
    print("Starting Stack Server...")
    print("Available endpoints:")
    print("  POST /stack?level=<trivial|hard|easy|medium> - Add to stack")
    print("  POST /stack with JSON: {'level': '<trivial|hard|easy|medium>'} - Add to stack")
    print("  GET /stack?level=<trivial|hard|easy|medium> - Get and clear stack")
    print("  GET /stack/status - View current stack without clearing")
    print("\nServer running on http://localhost:5000")
    
    app.run(debug=True, host='localhost', port=5000)