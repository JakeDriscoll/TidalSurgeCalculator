from flask import Flask, request, render_template, redirect, url_for, send_file
import matplotlib.pyplot as plt
import requests
import io
import datetime

app = Flask(__name__)

def get_noaa_data(params, data_key):
    api_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        predictions = data[data_key]
        values_array = [{"time": entry["t"], "value": float(entry["v"])} for entry in predictions]
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
    surge_data = get_difference(predicted_data, actual_data)

    # Create the graph
    plt.figure(figsize=(10, 6))
    plt.plot([entry['time'] for entry in predicted_data], [entry['value'] for entry in predicted_data], 'b-', label="Predicted Tide")
    plt.plot([entry['time'] for entry in actual_data], [entry['value'] for entry in actual_data], 'g-', label="Actual Water Level")
    plt.plot([entry['time'] for entry in surge_data], [entry['value'] for entry in surge_data], 'r-', label="Surge Difference")
    plt.xticks(rotation=45)
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.title(f"Tide & Water Level Data: {begin_date} to {end_date}")
    plt.legend()
    plt.tight_layout()

    # Save the graph to a BytesIO object and return it as an image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
