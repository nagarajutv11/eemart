from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from InvoiceExtractor import InvoiceExtractor
import mimetypes
import json
from io import StringIO

app = Flask(__name__)
CORS(app)

ie = InvoiceExtractor("AIzaSyDG861YemUvZMjlrVToPafrZ2cGZ8df9Rc")

# File to store vendor data
FILE_PATH = "vendors.json"

# Load vendors from the file at startup
def load_vendors():
    try:
        with open(FILE_PATH, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Return an empty list if the file doesn't exist or is corrupted

# Save vendors to the file
def save_vendors(vendors):
    with open(FILE_PATH, "w") as file:
        json.dump(vendors, file, indent=4)

# In-memory cache for vendors
vendors = load_vendors()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/voucher')
def voucher():
    return render_template('voucher.html')

@app.route('/vendors', methods=['POST', 'GET'])
def manage_vendors():
    if request.method == 'POST':
        # Save vendor details
        try:
            vendor = request.json
            required_fields = ["name", "contact", "email", "gstn"]

            # Validate input
            if not all(field in vendor for field in required_fields):
                return jsonify({"error": "Missing required fields: name, contact, email, gstn"}), 400

            # Add vendor to the list and save to file
            vendors.append(vendor)
            save_vendors(vendors)
            return jsonify({"message": "Vendor added successfully", "vendor": vendor}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'GET':
        # Fetch all vendors
        return jsonify({"vendors": vendors}), 200

@app.route('/meterial')
def meterial():
    return render_template('meterial.html')

@app.route('/upload-invoice', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    mime_type, _ = mimetypes.guess_type(file.filename)
    file_path = f"./uploads/{file.filename}"
    file.save(file_path)
    
    prompt = "Extract the line items from this Invoice. Need all columns in a structured format suitable for CSV conversion."
    
    if mime_type == 'application/pdf':
        data = ie.process_pdf_file(file_path, prompt)
    elif mime_type in ['image/jpeg', 'image/png']:
        data = ie.process_image_files([file_path], prompt)
    else:
        return jsonify({'error': 'File not supported ' + mime_type}), 400
        
    return jsonify({'data': data}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
