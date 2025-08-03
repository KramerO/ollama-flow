# Ollama Flow - Python Multi-AI Agent Framework

This project implements a flexible and extensible multi-AI agent framework in Python 3, designed to orchestrate various AI agents for complex task execution. It leverages Ollama for large language model (LLM) interactions and provides agents with controlled access to the command line for dynamic operations.

## Features

-   **Modular Agent Architecture**: Easily define and integrate different types of AI agents (Queen, Sub-Queen, Worker).
-   **Hierarchical Task Decomposition**: Queen and Sub-Queen agents can decompose complex tasks into smaller, manageable subtasks using LLMs.
-   **Ollama LLM Integration**: Seamless interaction with Ollama-hosted language models for natural language understanding and generation.
-   **Command-Line Access for Agents**: Worker agents can execute shell commands, enabling dynamic interaction with the host system.
-   **File Management**: Agents can save generated content (e.g., code) to specified project folders.
-   **Asynchronous Operations**: Built with `asyncio` for efficient handling of concurrent tasks.
-   **Environment Variable Management**: Uses `python-dotenv` for easy configuration.

## Project Structure

```
ollama-flow-python/
├── agents/
│   ├── base_agent.py
│   ├── queen_agent.py
│   ├── sub_queen_agent.py
│   └── worker_agent.py
├── orchestrator/
│   └── orchestrator.py
├── tests/
│   ├── __init__.py
│   ├── test_base_agent.py
│   ├── test_orchestrator.py
│   ├── test_queen_agent.py
│   ├── test_sub_queen_agent.py
│   └── test_worker_agent.py
├── .env.example
├── main.py
├── requirements.txt
└── README.md
└── .gitignore
```

## Setup and Installation

1.  **Clone the repository (if you haven't already):**

    ```bash
    git clone <repository_url>
    cd ollama-flow
    git checkout python # Switch to the python branch
    cd ollama-flow-python
    ```

2.  **Create a Python Virtual Environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**

    Create a `.env` file in the `ollama-flow-python/` directory based on `.env.example`:

    ```ini
    # .env
    OLLAMA_WORKER_COUNT=4
    OLLAMA_ARCHITECTURE_TYPE=HIERARCHICAL # or CENTRALIZED, FULLY_CONNECTED
    OLLAMA_MODEL=llama3 # or any other Ollama model you have downloaded
    OLLAMA_PROJECT_FOLDER=/path/to/your/agent/working/directory # Optional: where agents can save files
    ```

    **Note**: Ensure you have Ollama installed and the specified `OLLAMA_MODEL` downloaded and running.

## Running the Framework

To start the multi-AI agent framework, execute `main.py`:

```bash
python main.py
```

The `main.py` script contains an example prompt. You can modify this prompt to test different functionalities, such as file saving or command execution.

## Testing

Unit tests are provided to ensure the functionality of individual components. To run the tests:

1.  **Ensure you are in the `ollama-flow-python` directory and your virtual environment is active.**

2.  **Run pytest:**

    ```bash
    pytest
    ```

## Security Disclaimer

**WARNING**: This framework provides AI agents with access to the command line. In a real-world or production environment, this poses significant security risks. Malicious or unintended commands executed by an AI agent could lead to data loss, system compromise, or other severe issues. For any deployment beyond development and testing, robust security measures such as sandboxing, strict command whitelisting, and resource limitations are absolutely essential. Use with extreme caution and only in isolated, controlled environments.
