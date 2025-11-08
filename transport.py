import json
import logging
import os
import datetime
from datetime import timezone

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Emission factors for transportation (kg CO2 per km)
TRANSPORT_EMISSION_FACTORS = {
    'car_petrol': 0.192,
    'car_diesel': 0.171,
    'car_electric': 0.105,
    'bus': 0.082,
    'train': 0.041,
    'plane': 0.255
}

def calculate_transport_emissions(transport_mode, distance):
    """
    Calculate carbon emissions based on transport mode and distance.
    Args:
        transport_mode (str): Mode of transport (car, bus, train, plane)
        distance (float): Distance traveled in kilometers
    Returns:
        dict: Result containing transport mode, distance, and emissions
    Raises:
        ValueError: If transport mode is invalid or distance is non-positive
    """
    transport_mode = transport_mode.lower()
    if transport_mode not in TRANSPORT_EMISSION_FACTORS:
        raise ValueError(f"Invalid transport mode. Choose from: {', '.join(TRANSPORT_EMISSION_FACTORS.keys())}")
    if distance <= 0:
        raise ValueError("Distance must be greater than 0")

    emissions = distance * TRANSPORT_EMISSION_FACTORS[transport_mode]
    result = {
        'transport_mode': transport_mode,
        'distance_km': distance,
        'carbon_emissions_kg': round(emissions, 2),
        'timestamp': datetime.datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }

    # Save to JSON
    try:
        json_file = 'static/transport_emissions.json'
        os.makedirs('static', exist_ok=True)
        
        # Use 'a+' to allow reading if needed, but mainly for safety
        with open(json_file, 'a', encoding='utf-8') as f:
            json.dump([result], f)
            f.write('\n')  # ← This must always happen
            f.flush()      # ← Force write to disk
        logger.debug(f"Saved transport emissions to {json_file}")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to save transport emissions: {str(e)}")
        # Optional: fallback to in-memory or retry

    return result