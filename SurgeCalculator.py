import matplotlib.pyplot as plt
import requests
from matplotlib.figure import Figure

def binary_search(sorted_array, target_time):
    left = 0
    right = len(sorted_array) - 1

    while left <= right:
        mid = (left + right) // 2
        mid_time = sorted_array[mid]["time"]

        if mid_time == target_time:
            return sorted_array[mid]["value"]
        elif mid_time < target_time:
            left = mid + 1
        else:
            right = mid - 1

    return None

# Fetches the noaa tide data
def get_noaa_data(params, data_key):
    api_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        # Parse JSON response
        data = response.json()

        # Extract predictions
        predictions = data[data_key]
            # Create an array to store the values
        values_array = []
        
        # Populate the values array and perform comparisons
        for entry in predictions:
            value = float(entry["v"])  # Convert value to float
            time = entry["t"]  # Get the time value
            values_array.append({"time": time, "value": value})

        # Sort values_array based on "t" values
        sorted_values = sorted(values_array, key=lambda x: x["time"])
        return sorted_values
    return None

def get_difference(predicted, actual):
    diff_values_array = []

    for entry in predicted:
        if entry['time'] is not None and entry['value']:
            found_value = binary_search(actual, entry['time'])
        if found_value is not None:
            diff_values_array.append({"time": entry['time'], "value": found_value - entry['value']})
    return diff_values_array

# API parameters
params = {
    "product": "predictions",
    "begin_date": "20240924",
    "end_date": "20240926",
    "datum": "MLLW",
    "station": "8726607",
    "time_zone": "LST_LDT",
    "units": "english",
    "format": "json"
}

def get_plot_display():
# Get all of the data
    predict_sorted_values = get_noaa_data(params, "predictions")
    params['product'] = "water_level"
    actual_sorted_values = get_noaa_data(params, "data")
    surge_values_array = get_difference(predict_sorted_values, actual_sorted_values)
    for s in surge_values_array:
        print(f"{s}")

    # Extract time and value arrays from sorted_values
    surge_times = [entry["time"] for entry in surge_values_array]
    surge_values = [entry["value"] for entry in surge_values_array]
    predicted_times = [entry["time"] for entry in predict_sorted_values]
    predicted_values = [entry["value"] for entry in predict_sorted_values]
    actual_times = [entry["time"] for entry in actual_sorted_values]
    actual_values = [entry["value"] for entry in actual_sorted_values]

    # Create the line graph
    plt.figure(figsize=(10, 6))  # Set the figure size
    plt.plot(surge_times, surge_values, marker='o', linestyle='-', color='r', label="Surge Value")  # Plot the data points
    plt.plot(predicted_times, predicted_values, marker='o', linestyle='-', color='b', label="Tide")  # Plot the data points
    plt.plot(actual_times, actual_values, marker='o', linestyle='-', color='g', label="Water Height")  # Plot the data points
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.title("Surge Height At Old Port Tampa")
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.legend()
    plt.tight_layout()

    return plt

    # Display the graph
    # plt.show()


 #plot = get_plot_display()
 #plot.show()
