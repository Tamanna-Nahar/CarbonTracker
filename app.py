from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
from ocr import extract_text, parse_receipt, estimate_carbon_emissions, CARBON_EMISSIONS
import logging
import device
from transport import calculate_transport_emissions

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/')
def serve_index():
    try:
        logger.debug("Serving index.html")
        return send_from_directory('static', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return jsonify({"error": "File not found"}), 404

@app.route('/dashboard')
def serve_dashboard():
    try:
        logger.debug("Serving dashboard.html")
        return send_from_directory('static', 'dashboard.html')
    except Exception as e:
        logger.error(f"Error serving dashboard.html: {str(e)}")
        return jsonify({"error": "File not found"}), 404

@app.route('/ocr')
def serve_receipt_ocr():
    try:
        logger.debug("Serving receipt_ocr_page.html")
        return send_from_directory(app.static_folder, 'receipt_ocr_page.html')
    except Exception as e:
        logger.error(f"Error serving receipt_ocr_page.html: {str(e)}")
        return jsonify({"error": "File not found"}), 404

@app.route('/device')
def serve_device_analyzer():
    try:
        logger.debug("Serving device_carbon_analyzer.html")
        return send_from_directory('static', 'device_carbon_analyzer.html')
    except Exception as e:
        logger.error(f"Error serving device_carbon_analyzer.html: {str(e)}")
        return jsonify({"error": "File not found"}), 404

@app.route('/transport')
def serve_transport_calculator():
    try:
        logger.debug("Serving transport_emissions.html")
        return send_from_directory('static', 'transport_emissions.html')
    except Exception as e:
        logger.error(f"Error serving transport_emissions.html: {str(e)}")
        return jsonify({"error": "File not found"}), 404

@app.route('/upload', methods=['POST'])
def upload_receipt():
    try:
        logger.debug("Received upload request")
        if 'image' not in request.files:
            logger.error("No image uploaded")
            return jsonify({"error": "No image uploaded"}), 400
        
        file = request.files['image']
        shopping_list = request.form.get('shopping_list', '').split(',')
        logger.debug(f"Shopping list: {shopping_list}")

        # Validate file
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({"error": "No file selected"}), 400

        # Save uploaded file
        upload_path = f"static/upload_{uuid.uuid4().hex}.png"
        logger.debug(f"Saving uploaded image to: {upload_path}")
        file.save(upload_path)

        # Update carbon emissions with shopping list
        for item in shopping_list:
            item = item.strip().lower()
            if item and item not in CARBON_EMISSIONS:
                CARBON_EMISSIONS[item] = 1.0

        # Process receipt
        text = extract_text(upload_path)
        if not text:
            logger.error("Failed to extract text from image")
            return jsonify({"error": "Failed to extract text from image"}), 500

        items = parse_receipt(text)
        if not items:
            logger.error("No items detected in receipt")
            return jsonify({"error": "No items detected in receipt"}), 400

        results = estimate_carbon_emissions(items)
        logger.debug(f"Upload response: {results}")

        # Clean up uploaded file
        try:
            os.remove(upload_path)
            logger.debug(f"Removed uploaded file: {upload_path}")
        except Exception as e:
            logger.warning(f"Failed to remove uploaded file {upload_path}: {str(e)}")

        return jsonify(results)

    except Exception as e:
        logger.error(f"Upload endpoint error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/device/calculate', methods=['POST'])
def calculate_device_emissions():
    try:
        logger.debug("Received device calculate request")
        data = request.get_json()
        if not data or 'devices' not in data:
            logger.error("No device data provided")
            return jsonify({"error": "No device data provided"}), 400

        results = device.analyze_device(data)
        logger.debug(f"Device calculate response: {results}")
        return jsonify(results)

    except Exception as e:
        logger.error(f"Device calculate endpoint error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/transport/calculate', methods=['POST'])
def calculate_transport_emissions_endpoint():
    try:
        logger.debug("Received transport calculate request")
        data = request.get_json()
        if not data or 'transport_mode' not in data or 'distance' not in data:
            logger.error("Missing transport mode or distance")
            return jsonify({"error": "Missing transport mode or distance"}), 400

        transport_mode = data['transport_mode'].lower()
        distance = float(data['distance'])

        # Calculate emissions using transport.py
        result = calculate_transport_emissions(transport_mode, distance)
        logger.debug(f"Transport calculate response: {result}")
        return jsonify(result)

    except ValueError as e:
        logger.error(f"Transport calculate validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Transport calculate endpoint error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({"error": f"Unexpected server error: {str(e)}"}), 500

if __name__=='__main__':
    app.run(debug=True,  use_reloader=False, host='0.0.0.0', port=5000)
