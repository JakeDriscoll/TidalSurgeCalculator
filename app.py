from flask import Flask, request, render_template, redirect, url_for, send_file
import matplotlib.pyplot as plt
import requests
import io
import numpy as np
from datetime import datetime

app = Flask(__name__)

def get_noaa_data(params, data_key):
    api_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        predictions = data[data_key]
        values_array = []
        
        for entry in predictions:
            time = entry["t"] 
            value_str = entry["v"]
            
            # Check if the value is not an empty string
            if value_str:
                values_array.append({"time": time, "value": float(value_str)})
            else:
                values_array.append({"time": time, "value": None})  # or simply skip this entry

        return sorted(values_array, key=lambda x: x["time"])
    return None

def get_difference(predicted, actual):
    def binary_search(sorted_array, target_time):
        left, right = 0, len(sorted_array) - 1
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

    diff_values_array = []
    for entry in predicted:
        found_value = binary_search(actual, entry["time"])
        if found_value is not None:
            diff_values_array.append({"time": entry["time"], "value": found_value - entry["value"]})
    return diff_values_array

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        begin_date = request.form['begin_date']
        end_date = request.form['end_date']
        return redirect(url_for('plot_graph', begin_date=begin_date, end_date=end_date))
    return render_template('index.html')

@app.route('/plot/<begin_date>/<end_date>')
def plot_graph(begin_date, end_date):
    # NOAA API parameters
    params = {
        "product": "predictions",
        "begin_date": begin_date,
        "end_date": end_date,
        "datum": "MLLW",
        "station": "8726607",
        "time_zone": "LST_LDT",
        "units": "english",
        "format": "json"
    }

    # Fetch predicted and actual data
    predicted_data = get_noaa_data(params, "predictions")
    params['product'] = "water_level"
    actual_data = get_noaa_data(params, "data")
    if predicted_data is None or actual_data is None:
        return render_template('error.html')
    surge_data = get_difference(predicted_data, actual_data)
    max_actual_entry = max(actual_data, key=lambda x: x['value'])
    max_water_height = max_actual_entry['value']

    # Create the graph
    plt.figure(figsize=(20, 12))
    plt.plot([entry['time'] for entry in predicted_data], [entry['value'] for entry in predicted_data], 'b-', label="Predicted Tide")
    plt.plot([entry['time'] for entry in actual_data], [entry['value'] for entry in actual_data], 'g-', label="Actual Water Level")
    plt.plot([entry['time'] for entry in surge_data], [entry['value'] for entry in surge_data], 'r-', label="Surge Difference")
    # Select every 10th tick for the X-axis
    x_ticks_positions = np.arange(0, len(predicted_data), 20)
    x_tick_labels = [predicted_data[i]['time'] for i in x_ticks_positions]

    plt.xticks(x_ticks_positions, x_tick_labels, rotation=45)
    plt.xlabel("Date Time")
    plt.ylabel("Value")
    datetime_format = "%Y%m%d"
    plt.title(f"Tide & Water Level Data: {datetime.strptime(begin_date, datetime_format).date()} to {datetime.strptime(end_date, datetime_format).date()}")

    # Add gridlines (horizontal only)
    plt.grid(True, which='both', axis='y', linestyle='-', linewidth=0.5)

    #y_values_to_label = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]  # You can modify these values based on your data
    # Initialize an empty list
    y_values_to_label = []

    # Start from 0, increment by 0.5 until reaching max_value
    current_value = 0.0
    while current_value <= max_water_height:
        y_values_to_label.append(current_value)
        current_value += 0.5

    i = 0
    for y_val in y_values_to_label:
        plt.axhline(y=y_val, color='gray', linestyle='--', linewidth=0.5)  # Add a line for the y value
        # Place text near the y-axis (adjust the x position slightly based on your plot range)
        for x_val in x_ticks_positions:
            if x_val % 3 == 0:
                if y_val <= max_water_height:
                    plt.text(x_val + 0.5, y_val, f"{y_val} ft", color='black', fontsize=9, verticalalignment='bottom')
        # plt.text(x_ticks_positions[0], y_val, f"{y_val}", color='black', fontsize=9, verticalalignment='bottom')
    plt.legend()
    plt.tight_layout()

    # Save the graph to a BytesIO object and return it as an image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
