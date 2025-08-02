from flask import Flask, request, jsonify
from phi.agent import Agent
from phi.model.ollama import Ollama
from phi.tools.duckduckgo import DuckDuckGo

app = Flask(__name__)

@app.route('/run_phi_agent', methods=['POST'])
def run_phi_agent():
    data = request.json
    prompt = data.get('prompt')
    ollama_model_name = data.get('ollama_model_name', 'llama3') # Default to llama3

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    try:
        # Initialize Ollama model with the provided name
        model = Ollama(model=ollama_model_name)
        
        # Initialize the agent with the model and tools
        web_agent = Agent(
            name="Web-Agent",
            model=model,
            tools=[DuckDuckGo()],
            instructions=["Always include sources in your response."],
            show_tool_calls=True,
            markdown=True,
        )

        # Run the agent with the prompt
        response = web_agent.print_response(prompt, stream=False) # stream=False for direct response
        
        return jsonify({'result': response}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) # Run on a different port than Ollama Flow server