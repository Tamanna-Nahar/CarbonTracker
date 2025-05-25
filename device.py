regional_intensities = {
    'global': 475,
    'india': 790,
    'usa': 400,
    'eu': 250,
    'china': 550,
    'uk': 200,
    'australia': 600
}

def calculate_emissions(power_watts, hours, carbon_intensity):
    """Calculate energy consumption and carbon emissions for a device"""
    if hours <= 0:
        raise ValueError("Usage hours must be positive")
    if power_watts <= 0:
        raise ValueError("Power consumption must be positive")
    
    energy_kwh = (power_watts / 1000) * hours
    emissions_g = energy_kwh * carbon_intensity
    return energy_kwh, emissions_g

def get_reduction_tips(emissions_kg):
    """Get personalized tips based on emission levels"""
    tips = [
        "💡 Enable power saving mode when not doing intensive tasks",
        "🖥️ Lower screen brightness to reduce power consumption",
        "⏰ Set your device to sleep/hibernate when idle",
        "🔌 Unplug chargers and peripherals when not in use",
        "❄️ Keep your device cool - overheating increases power usage",
        "💾 Use SSDs instead of HDDs - they consume less power",
        "🔄 Close unnecessary programs and browser tabs",
        "⚙️ Update software regularly for better energy efficiency",
        "🌙 Use dark mode themes to save display power",
        "🔋 For portable devices: avoid keeping battery at 100% constantly"
    ]
    
    if emissions_kg > 2:
        specific_tips = [
            "⚠️ Your daily emissions are quite high. Consider:",
            "🎯 Reducing intensive tasks during peak grid hours",
            "☀️ Using renewable energy sources if possible"
        ]
    elif emissions_kg > 1:
        specific_tips = [
            "📊 Your emissions are moderate. Small changes can help:",
            "⏱️ Take regular breaks to let your device cool down"
        ]
    else:
        specific_tips = [
            "✅ Great! Your carbon footprint is relatively low.",
            "🌱 Keep up the efficient habits!"
        ]
    
    return tips[:5] + specific_tips

def analyze_device(request_data):
    """Analyze carbon emissions for multiple devices"""
    try:
        carbon_intensity = float(request_data.get('carbon_intensity', 475))  
        electricity_rate = float(request_data.get('electricity_rate', 10))   
        
        devices = request_data.get('devices', [])
        
        if not devices:
            return {"error": "No devices provided"}
        
        total_energy = 0
        total_emissions = 0
        device_breakdown = []
        
        for device in devices:
            try:
                wattage = float(device.get('wattage', 0))
                hours = float(device.get('hours', 0))
                device_name = device.get('device', 'Unknown Device')
                
                if wattage <= 0 or hours <= 0:
                    continue
                
                energy_kwh, emissions_g = calculate_emissions(wattage, hours, carbon_intensity)
                total_energy += energy_kwh
                total_emissions += emissions_g
                
                device_breakdown.append({
                    'device': device_name,
                    'wattage': wattage,
                    'hours': hours,
                    'energy_kwh': round(energy_kwh, 3),
                    'emissions_g': round(emissions_g, 1)
                })
            except (ValueError, TypeError) as e:
                continue  
        
        if total_energy == 0:
            return {"error": "No valid devices found"}
        
        emissions_kg = total_emissions / 1000
        daily_cost = total_energy * electricity_rate
        annual_emissions_kg = emissions_kg * 365
        monthly_emissions_kg = emissions_kg * 30
        tips = get_reduction_tips(emissions_kg)
        
        return {
            'success': True,
            'total_energy': round(total_energy, 3),
            'total_emissions': round(total_emissions, 2),  # instead of 'total_emissions_g'
            'total_emissions_kg': round(emissions_kg, 3),
            'daily_cost': round(daily_cost, 2),
            'monthly_projection': round(monthly_emissions_kg, 2),
            'annual_projection': round(annual_emissions_kg, 2),
            'device_breakdown': device_breakdown,
            'tips': tips,
            'carbon_intensity': carbon_intensity,
            'electricity_rate': electricity_rate
        }
        
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def get_device_presets():
    """Return common device power consumption presets"""
    return {
        'laptop': {'wattage': 65, 'name': 'Laptop'},
        'desktop': {'wattage': 200, 'name': 'Desktop Computer'},
        'monitor': {'wattage': 30, 'name': 'Monitor (24")'},
        'smartphone': {'wattage': 5, 'name': 'Smartphone'},
        'tablet': {'wattage': 12, 'name': 'Tablet'},
        'gaming_console': {'wattage': 150, 'name': 'Gaming Console'},
        'tv': {'wattage': 100, 'name': 'LED TV (42")'},
        'router': {'wattage': 10, 'name': 'Wi-Fi Router'},
        'printer': {'wattage': 50, 'name': 'Inkjet Printer'},
        'external_hdd': {'wattage': 8, 'name': 'External Hard Drive'}
    }