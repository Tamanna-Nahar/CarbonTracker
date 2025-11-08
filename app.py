from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
from ocr import extract_text, parse_receipt, estimate_carbon_emissions, CARBON_EMISSIONS
import logging
import device
from transport import calculate_transport_emissions
import json
import datetime
from datetime import timezone



logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = Flask(__name__, static_folder='static')
CORS(app)

ELECTRICITY_HISTORY_PATH = os.path.join(app.static_folder, 'electricity_history.json')
def _load_electricity_history():
    if not os.path.exists(ELECTRICITY_HISTORY_PATH):
        return []
    history = []
    try:
        with open(ELECTRICITY_HISTORY_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    history.append(json.loads(line))
    except Exception as e:
        logger.error(f"Failed to read electricity history: {e}")
    return history

def _append_electricity_history(entry):
    os.makedirs(app.static_folder, exist_ok=True)
    with open(ELECTRICITY_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def _load_device_history():
    if not os.path.exists(DEVICE_HISTORY_PATH):
        return []
    history = []
    try:
        with open(DEVICE_HISTORY_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    history.append(json.loads(line))
    except Exception as e:
        logger.error(f"Failed to read device history: {e}")
    return history

def _append_device_history(entry):
    os.makedirs(os.path.dirname(DEVICE_HISTORY_PATH), exist_ok=True)
    with open(DEVICE_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
def _append_device_history(entry):
    _ensure_static_folder()
    with open(DEVICE_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def _load_device_history():
    if not os.path.exists(DEVICE_HISTORY_PATH):
        return []
    history = []
    try:
        with open(DEVICE_HISTORY_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    history.append(json.loads(line))
    except Exception as e:
        logger.error(f"History read error: {e}")
    return history
def _ensure_static_folder():
    os.makedirs(app.static_folder, exist_ok=True)



import cv2, numpy as np, easyocr, re, os, tempfile

def process_electricity_bill(image_path):
    x,y,w,h = 730,330,118,50                 # crop coordinates
    carbon_intensity = 0.82                  # kg CO₂/kWh

    def calc_bill(u):
        fixed = 20
        slabs = [(200,3.0),(200,4.5),(400,6.5),(400,7.0),(float('inf'),8.0)]
        total,rem = fixed,u
        for sz,rate in slabs:
            if rem<=0: break
            take = min(rem,sz) if sz!=float('inf') else rem
            total += take*rate; rem-=take
        return round(total,2)

    img = cv2.imread(image_path)
    if img is None: raise FileNotFoundError("Cannot read image")
    crop = img[y:y+h, x:x+w]
    if crop.size==0: raise ValueError("Crop empty")
    tight = crop[int(crop.shape[0]*0.6):,:]
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    tight = cv2.filter2D(tight,-1,kernel)
    tight = cv2.resize(tight,None,fx=4,fy=4,interpolation=cv2.INTER_LINEAR)

    reader = easyocr.Reader(['en'], gpu=False)
    txt = " ".join([t for _,t,_ in reader.readtext(tight)])
    cleaned = txt.replace('O','0').replace('o','0').replace('l','1').replace('I','1').replace('g','9')
    m = re.search(r'\d+(\.\d+)?', cleaned)

    if m:
        units = float(m.group(0))
        return {"success":True, "units":units,
                "bill_amount":calc_bill(units),
                "co2_emissions":round(units*carbon_intensity,2)}
    else:
        return {"success":False, "error":"units_not_detected",
                "message":"Units not found - please enter manually."}


# === DEVICE EMISSIONS HISTORY ===
DEVICE_HISTORY_PATH = os.path.join(app.static_folder, 'device_emissions_history.json')
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
    
@app.errorhandler(404)
def not_found_error(e):
    return jsonify({"error": "Route not found"}), 404
@app.route('/api/placeholder/<int:width>/<int:height>')
def placeholder(width, height):
    return f"Placeholder image of {width}x{height}", 200

@app.errorhandler(404)
def not_found(e):
    return "Page not found", 404


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
        data = request.get_json()
        if not data or 'devices' not in data:
            return jsonify({"error": "No device data provided"}), 400

        results = device.analyze_device(data)

        if results.get('success'):
            # Save one entry PER DEVICE
            for item in results['device_breakdown']:
                entry = {
                    "timestamp": datetime.datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "device": item['device'],
                    "emissions_kg": round(item['emissions_g'] / 1000, 3),  # g → kg
                    "energy_kwh": item['energy_kwh'],
                    "wattage": item['wattage'],
                    "hours": item['hours']
                }
                _append_device_history(entry)

            # Also save total
            total_entry = {
                "timestamp": datetime.datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "device": "All Devices",
                "emissions_kg": round(results['total_emissions_kg'], 3),
                "energy_kwh": round(results['total_energy'], 3),
                "daily_cost": round(results['daily_cost'], 2)
            }
            _append_device_history(total_entry)

            logger.info("History saved per device")
        return jsonify(results)

    except Exception as e:
        logger.error(f"Calculate error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500   
# === HISTORY ENDPOINT ===
@app.route('/device/history')
def device_history():
    history = _load_device_history()
    history.sort(key=lambda x: x["timestamp"])
    logger.info(f"History served: {len(history)} entries")
    return jsonify(history)


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
    
@app.route('/transport/history')
def transport_history():
    json_path = os.path.join(app.static_folder, 'transport_emissions.json')

    if not os.path.exists(json_path):
        return jsonify([])

    history = []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if isinstance(record, list) and len(record) > 0:
                        history.append(record[0])
                    else:
                        logger.warning(f"Invalid record format at line {line_num}: {line}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON error at line {line_num}: {e} | Line: {line}")
                    continue  # Skip bad line
    except Exception as e:
        logger.error(f"Failed to read transport history file: {e}")

    return jsonify(history)
@app.route('/electricity')
def serve_electricity_page():
    return send_from_directory('static', 'bill.html')

@app.route('/electricity/upload', methods=['POST'])
def upload_electricity_bill():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image"}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file"}), 400

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            file.save(tmp.name)
            path = tmp.name

        result = process_electricity_bill(path)
        os.unlink(path)

        # === SAVE TO HISTORY IF SUCCESS ===
        if result.get("success"):
            entry = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "units": result["units"],
                "bill_amount": result["bill_amount"],
                "co2_emissions": result["co2_emissions"]
            }
            _append_electricity_history(entry)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Electricity OCR error: {e}")
        return jsonify({"error": str(e)}), 500
# === ELECTRICITY HISTORY FILE ===

@app.route('/electricity/save_manual', methods=['POST'])
def save_manual_bill():
    try:
        data = request.get_json()
        units = float(data.get('units', 0))
        date = data.get('date') or datetime.datetime.now().strftime("%Y-%m-%d")

        # === Delhi Slab Calculation ===
        def calc_bill(u):
            fixed = 20
            slabs = [(200,3.0),(200,4.5),(400,6.5),(400,7.0),(float('inf'),8.0)]
            total, rem = fixed, u
            for sz, rate in slabs:
                if rem <= 0: break
                take = rem if sz == float('inf') else min(rem, sz)
                total += take * rate
                rem -= take
            return round(total, 2)

        bill = calc_bill(units)
        co2 = round(units * 0.82, 2)

        # === SAVE TO HISTORY ===
        entry = {
            "date": date,
            "units": units,
            "bill_amount": bill,
            "co2_emissions": co2
        }
        _append_electricity_history(entry)

        return jsonify({
            "success": True,
            "units": units,
            "bill_amount": bill,
            "co2_emissions": co2
        })

    except Exception as e:
        logger.error(f"Manual save error: {e}")
        return jsonify({"error": str(e)}), 500
@app.route('/electricity/history')
def electricity_history():
    history = _load_electricity_history()
    history.sort(key=lambda x: x["date"], reverse=True)
    return jsonify(history)

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({"error": f"Unexpected server error: {str(e)}"}), 500

if __name__=='__main__':
    app.run(debug=False,  use_reloader=False, host='0.0.0.0', port=10000)