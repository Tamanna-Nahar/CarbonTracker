import psutil
import time

def get_carbon_intensity():
    """Returns carbon intensity in gCO2e/kWh."""
    default_intensity = 475  # Global average in gCO2e/kWh
    print(f"Default carbon intensity: {default_intensity} gCO2e/kWh (global average).")
    try:
        user_input = input("Enter custom carbon intensity (gCO2e/kWh) or press Enter to use default: ")
        return float(user_input) if user_input.strip() else default_intensity
    except ValueError:
        print("Invalid input. Using default carbon intensity.")
        return default_intensity

def estimate_power_psutil():
    """Estimate power usage based on CPU utilization."""
    # Typical power ranges (in watts): adjust based on your system
    laptop_idle = 20  # Idle power for a typical laptop
    laptop_full = 60  # Full load power for a typical laptop
    desktop_idle = 50  # Idle power for a typical desktop
    desktop_full = 200  # Full load power for a typical desktop
    
    system_type = input("Is this a laptop or desktop? (Enter 'laptop' or 'desktop', default: laptop): ").lower()
    if system_type == 'desktop':
        idle_power, full_power = desktop_idle, desktop_full
    else:
        idle_power, full_power = laptop_idle, laptop_full
    
    # Get CPU usage percentage (average over 1 second)
    cpu_percent = psutil.cpu_percent(interval=1)
    # Linearly interpolate power based on CPU usage
    power_watts = idle_power + (full_power - idle_power) * (cpu_percent / 100)
    return power_watts, cpu_percent

def calculate_emissions(power_watts, hours, carbon_intensity):
    """Calculate carbon emissions for the computer."""
    energy_kwh = (power_watts / 1000) * hours
    emissions_g = energy_kwh * carbon_intensity
    return energy_kwh, emissions_g

def main():
    print("Computer Carbon Emissions Calculator")
    print("Estimates carbon emissions based on CPU usage (note: running on Colab server, not your local device).\n")
    
    carbon_intensity = get_carbon_intensity()
    
    # Get usage hours
    try:
        hours = float(input("Enter usage hours for today (e.g., 8 for 8 hours): "))
    except ValueError:
        print("Invalid input. Using default 8 hours.")
        hours = 8
    
    # Estimate power using psutil
    print("Estimating power based on CPU usage (Colab server environment).")
    power_watts, cpu_percent = estimate_power_psutil()
    
    # Calculate emissions
    energy_kwh, emissions_g = calculate_emissions(power_watts, hours, carbon_intensity)
    
    # Display results
    print("\nCarbon Emissions Summary")
    print(f"Carbon intensity used: {carbon_intensity} gCO2e/kWh")
    print("-" * 40)
    print(f"Device: Colab Server")
    print(f"  Estimated Power: {power_watts:.2f} W")
    print(f"  CPU Usage: {cpu_percent:.1f}%")
    print(f"  Daily Usage: {hours:.2f} hours")
    print(f"  Energy: {energy_kwh:.2f} kWh")
    print(f"  Emissions: {emissions_g:.2f} gCO2e")
    print(f"  Emissions: {(emissions_g / 1000):.2f} kgCO2e")
    print("-" * 40)
    print("Note: This is an estimate for the Colab server, not your local computer.")

if __name__ == "__main__":
    main()