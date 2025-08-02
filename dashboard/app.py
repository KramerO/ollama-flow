
from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import json

app = Flask(__name__)

OLLAMA_FLOW_SERVER_URL = "http://localhost:3000"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_prompt', methods=['POST'])
def run_prompt():
    prompt = request.form['prompt']
    try:
        response = requests.post(f"{OLLAMA_FLOW_SERVER_URL}/run", json={'prompt': prompt})
        response.raise_for_status()  # Raise an exception for HTTP errors
        result = response.json().get('result', 'No result from Ollama Flow')
    except requests.exceptions.ConnectionError:
        result = "Error: Could not connect to Ollama Flow server. Is it running?"
    except requests.exceptions.RequestException as e:
        result = f"Error: {e}"
    
    return render_template('index.html', result=result, prompt=prompt)

@app.route('/configure_architecture', methods=['POST'])
def configure_architecture():
    request_data = request.get_json()
    if not request_data or 'architectureType' not in request_data or 'workerCount' not in request_data:
        return jsonify({'error': 'architectureType and workerCount are required'}), 400

    architecture_type = request_data['architectureType']
    worker_count = request_data['workerCount']
    try:
        response = requests.post(f"{OLLAMA_FLOW_SERVER_URL}/configure_architecture", json={'architectureType': architecture_type, 'workerCount': int(worker_count)})
        response.raise_for_status()  # Raise an exception for HTTP errors
        message = response.json().get('message', 'Configuration updated.')
        return render_template('index.html', config_message=message)
    except requests.exceptions.ConnectionError:
        error_message = "Error: Could not connect to Ollama Flow server. Is it running?"
        return render_template('index.html', config_error=error_message)
    except requests.exceptions.RequestException as e:
        error_message = f"Error reconfiguring architecture: {e}"
        return render_template('index.html', config_error=error_message)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
