import json
import logging
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Emission factors for transportation (kg CO2 per km)
TRANSPORT_EMISSION_FACTORS = {
    'car_petrol': 0.192,
    'car_diesel': 0.168,
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
        'carbon_emissions_kg': round(emissions, 2)
    }

    # Save to JSON
    try:
        json_file = 'static/transport_emissions.json'
        # Ensure static directory exists
        os.makedirs('static', exist_ok=True)
        # Append to JSON file
        with open(json_file, 'a') as f:
            json.dump([result], f)
            f.write('\n')
        logger.debug(f"Saved transport emissions to {json_file}")
    except Exception as e:
        logger.warning(f"Failed to save transport emissions to JSON: {str(e)}")

    return result