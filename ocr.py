import easyocr
from PIL import Image
import re
import os
import logging
import uuid

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    "coconut water": 0.3, "bottled juice": 1.0, "snack bar": 1.1, "large eggs": 0.8,"cottage cheese": 13.0,
    "natural yogurt": 2.5,
    "cherry tomatoes": 1.2,
    "bananas": 0.8,
    "cheese crackers": 1.5,
    "chocolate cookies": 2.0,
    "chicken breast": 6.6,
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