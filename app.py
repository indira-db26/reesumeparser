import os
import json
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Import your core parser function
from parser_api import parse_resume 

# --- FLASK SETUP ---
app = Flask(__name__)
# Define a temporary folder to save uploaded files before parsing
UPLOAD_FOLDER = 'temp_uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/parse_resume', methods=['POST'])
def parse_resume_endpoint():
    """
    Web endpoint to receive a file, process it using the parser_api, 
    and return the structured JSON result.
    """
    
    # 1. Check if a file was uploaded in the request
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    
    # 2. Check for empty filename or disallowed extension
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "No selected file or file type not allowed (must be PDF or DOCX)"}), 400
    
    try:
        # 3. Securely save the uploaded file to the temporary folder
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 4. Call your core parsing logic
        print(f"--- Calling parser_api for: {filename} ---")
        structured_data = parse_resume(file_path)
        
        # 5. Clean up the temporary file
        os.remove(file_path)
        print(f"--- Successfully processed and removed temp file: {filename} ---")
        
        # 6. Return the structured JSON result
        return jsonify(structured_data), 200
        
    except Exception as e:
        # Handle unexpected errors gracefully
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    print("Starting Flask API server...")
    # Run the server on http://127.0.0.1:5000/
    app.run(debug=True)