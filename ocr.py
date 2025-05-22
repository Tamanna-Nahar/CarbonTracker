from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
import easyocr
import re
import os
import logging
import uuid

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)

# Carbon emission data (kg CO2e per unit)
CARBON_EMISSIONS = {
    "milk": 1.5, "chicken": 6.9, "bread": 1.0, "egg": 0.2, "beef": 60.0,
    "apple": 0.3, "rice": 2.7, "pasta": 1.8, "cheese": 13.5, "tomato": 1.1,
    "coffee": 0.7, "water": 0.2, "soda": 0.5, "plastic bag": 0.05, "paper bag": 0.04,
    "tea": 0.2, "juice": 0.9, "toilet paper": 1.3, "detergent": 2.0, "pizza": 5.0,
    "sandwich": 3.0, "banana": 0.3, "potato": 0.2, "cucumber": 0.2, "onion": 0.3,
    "carrot": 0.25, "fish": 5.0, "mutton": 24.0, "yogurt": 2.2, "butter": 11.9,
    "chocolate": 7.0, "milkshake": 1.8, "beer": 0.6, "wine": 1.5, "energy drink": 1.0,
    "green tea": 0.1, "shampoo": 2.3, "toothpaste": 1.0, "handwash": 1.5, "soap": 0.7,
    "facewash": 1.8, "chips": 2.0, "biscuits": 1.2, "instant noodles": 1.5, "ice cream": 3.0,
    "coconut water": 0.3, "bottled juice": 1.0, "snack bar": 1.1
}

def preprocess_image(image_path):
    try:
        logger.debug(f"Preprocessing image: {image_path}")
        img = Image.open(image_path)
        img = img.convert("L")  # Grayscale
        return img
    except Exception as e:
        logger.error(f"Image preprocessing error: {str(e)}")
        return None

def extract_text(image_path):
    try:
        logger.debug("Initializing EasyOCR reader")
        reader = easyocr.Reader(['en'], gpu=False)
        logger.debug(f"Reading image: {image_path}")
        img = preprocess_image(image_path)
        if img is None:
            logger.error("Image preprocessing failed")
            return ""
        temp_path = f"static/temp_{uuid.uuid4().hex}.png"
        logger.debug(f"Saving preprocessed image to: {temp_path}")
        img.save(temp_path)
        logger.debug("Running OCR")
        results = reader.readtext(temp_path, detail=0)
        text = " ".join(results)
        logger.debug(f"Extracted text: {text}")
        # Clean up temporary file
        try:
            os.remove(temp_path)
            logger.debug(f"Removed temporary file: {temp_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temp file {temp_path}: {str(e)}")
        return text
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        return ""

def parse_receipt(text):
    try:
        logger.debug(f"Parsing text: {text}")
        items = []
        pattern = r"(\d+\.?\d*\s*(?:kg|g|l|liter|litre|bag|unit)?)?\s*([a-zA-Z\s]+)"
        matches = re.findall(pattern, text.lower())
        for quantity, item in matches:
            quantity = quantity.strip() if quantity else "1"
            qty_value = re.search(r"\d+\.?\d*", quantity)
            qty = float(qty_value.group()) if qty_value else 1.0
            if "g" in quantity.lower():
                qty /= 1000  # Convert grams to kg
            items.append({"item": item.strip(), "quantity": qty})
        logger.debug(f"Parsed items: {items}")
        return items
    except Exception as e:
        logger.error(f"Receipt parsing error: {str(e)}")
        return []

def estimate_carbon_emissions(items):
    try:
        logger.debug(f"Estimating emissions for items: {items}")
        results = []
        for entry in items:
            item = entry["item"]
            quantity = entry["quantity"]
            for key in CARBON_EMISSIONS:
                if key in item:
                    emissions = CARBON_EMISSIONS[key] * quantity
                    results.append({"item": item, "quantity": quantity, "emissions": emissions})
                    break
        logger.debug(f"Emissions results: {results}")
        return results
    except Exception as e:
        logger.error(f"Emissions calculation error: {str(e)}")
        return []

@app.route('/')
@app.route('/<path:path>')
def serve_static(path='receipt_ocr_page.html'):
    try:
        logger.debug(f"Serving static file: {path}")
        return send_from_directory('static', path)
    except Exception as e:
        logger.error(f"Static file error: {str(e)}")
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

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({"error": f"Unexpected server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

