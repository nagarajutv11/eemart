from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from InvoiceExtractor import InvoiceExtractor
import mimetypes
import json
from io import StringIO

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app)

def read_dict_from_file(file_path: str) -> dict:
    result = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                result[key.strip()] = value.strip()
    return result
vars = read_dict_from_file('vars.env')
ie = InvoiceExtractor(vars['GEMINI_API_KEY'])

# File to store vendor data
FILE_PATH = "vendors.json"
PRICE_PATH = "prices.json"

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

    if mime_type == 'application/pdf':
        data = ie.process_pdf_file(file_path)
    elif mime_type in ['image/jpeg', 'image/png']:
        data = ie.process_image_files([file_path])
    else:
        return jsonify({'error': 'File not supported ' + mime_type}), 400
        
    return jsonify({'data': data}), 200

def read_json_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except Exception as e:
        return []

def write_json_file(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

@app.route('/price-admin')
def price_admin():
    return render_template('price-admin.html')

@app.route('/price-calculator')
def price_calculator():
    return render_template('price-calculator.html')

@app.route("/price-load", methods=["GET"])
def price_load():
    data = read_json_file(PRICE_PATH)
    return jsonify(data)

@app.route("/price-create", methods=["POST"])
def price_create():
    name = request.get_data(as_text=True)
    data = read_json_file(PRICE_PATH)
    data.append({
        "name": name,
        "note": "",
        "items": []
    })
    write_json_file(PRICE_PATH, data)

    return jsonify({"message": "Object added successfully", "data": name}), 201

@app.route("/price-update", methods=["POST"])
def price_update():
    updated = request.json
    data = read_json_file(PRICE_PATH)
    for obj in data:
        if obj.get("name") == updated.get("name"):
            obj.pop("items")
            obj.update(updated)
            write_json_file(PRICE_PATH, data)
            return jsonify({"message": "Object updated successfully", "data": updated}), 200

    return jsonify({"error": "Object not found"}), 404

@app.route("/price-delete", methods=["POST"])
def price_delete():
    name = request.get_data(as_text=True)
    data = read_json_file(PRICE_PATH)
    new_data = [obj for obj in data if obj.get("name") != name]

    if len(new_data) == len(data):
        return jsonify({"error": "Object not found"}), 404  # No object was removed

    write_json_file(PRICE_PATH, new_data)
    return jsonify({"message": "Object deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
