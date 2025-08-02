
from flask import Flask, render_template, request, redirect, url_for
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
