# Ollama Flow

Ollama Flow is a multi-agent system designed to orchestrate interactions with Ollama models through various communication architectures. It features a Node.js backend for agent management and a Python Flask dashboard for user interaction and configuration.

## Features

-   **Ollama Integration:** Seamlessly interacts with local Ollama models.
-   **Multi-Agent System:** Supports multiple AI agents working together.
-   **Configurable Architectures:** Choose from different communication patterns:
    -   **Fully Connected:** Every agent can communicate with any other agent (via the orchestrator).
    -   **Centralized:** All communication flows through a central Queen Agent.
    -   **Hierarchical:** Groups of agents communicate via Sub-Queen Agents, with overall coordination by a Main Queen Agent.
-   **Configurable Worker Agents:** Dynamically set the number of Ollama Worker Agents.
-   **Web-based Dashboard:** A user-friendly interface to configure the system and send prompts.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

-   **Node.js** (LTS version recommended) and **npm**
-   **Python 3** and **pip**
-   **Ollama:** Make sure Ollama is installed and running in the background. You can download it from [ollama.ai](https://ollama.ai/).

## Installation

Follow these steps to set up Ollama Flow:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd ollama-flow
    ```

2.  **Run the installation script:**

    -   **For Windows:**
        ```cmd
        .\install.bat
        ```

    -   **For Linux/macOS:**
        ```bash
        ./install.sh
        ```

    The script will:
    -   Check for Node.js, npm, Python, and pip.
    -   Install Node.js dependencies.
    -   Build the TypeScript project.
    -   Set up a Python virtual environment for the dashboard.
    -   Install Python dependencies.

    *If Node.js or Python are not found, the script will provide instructions for manual installation.*

## Usage

To run Ollama Flow, you need to start both the Node.js server and potentially interact with the Python applications.

1.  **Start the Ollama Flow Server (Node.js):**

    Open your terminal or command prompt, navigate to the project root directory, and run:
    ```bash
    npm run start:server
    ```
    This server will listen on `http://localhost:3000`.

2.  **Run the Ollama Flow Python CLI Application (`ollama-flow-python/main.py`):**

    This application allows you to interact with the Ollama Flow framework directly from the command line, providing tasks and configuration.

    Navigate to the `ollama-flow-python` directory:
    ```bash
    cd ollama-flow-python
    ```
    Activate the virtual environment (if you created one during installation):
    ```bash
    # For Windows:
    .\venv\Scripts\activate
    # For Linux/macOS:
    source venv/bin/activate
    ```

    You can run `main.py` in a few ways:

    *   **Interactive Wizard (no arguments):**
        If you run `main.py` without any arguments, it will prompt you for the task and project folder.
        ```bash
        python main.py
        ```
        Follow the on-screen prompts.

    *   **Using Command-Line Arguments:**
        Provide the task and project folder directly as arguments.
        ```bash
        python main.py --task "Please write a simple Python Flask app that says 'Hello, World!' and save it to app.py." --project-folder "/tmp/my_project" --worker-count 2 --architecture-type CENTRALIZED --ollama-model llama3
        ```
        Replace the example task, project folder, worker count, architecture type, and Ollama model with your desired values.

    *   **Using a `.env` file:**
        For persistent configuration, you can create a `.env` file in the `ollama-flow-python` directory with the following variables:
        ```
        OLLAMA_PROJECT_FOLDER=/path/to/your/project
        OLLAMA_WORKER_COUNT=4
        OLLAMA_ARCHITECTURE_TYPE=HIERARCHICAL
        OLLAMA_MODEL=llama3
        ```
        When `main.py` is run, it will read these values. Command-line arguments will override `.env` values.

    Deactivate the virtual environment when done (optional):
    ```bash
    deactivate
    ```

3.  **Start the Ollama Flow Dashboard (Python Flask - `dashboard/app.py`):**

    This is a separate web-based interface for configuring the system and sending prompts.

    Open a **separate** terminal or command prompt, navigate to the `dashboard` directory:
    ```bash
    cd dashboard
    ```
    Activate the virtual environment:
    ```bash
    # For Windows:
    .\venv\Scripts\activate
    # For Linux/macOS:
    source venv/bin/activate
    ```

    Run the Flask application:
    ```bash
    python app.py
    ```
    The dashboard will be accessible in your web browser at `http://localhost:5000`.

    **Configure and Interact via the Dashboard:**
    -   Open your web browser and go to `http://localhost:5000`.
    -   You will find options to select the **Agent Architecture** (Hierarchical, Centralized, Fully Connected) and set the **Number of Worker Agents**.
    -   Apply your desired configuration.
    -   Enter your prompt in the provided text area and click "Run Ollama Flow" to send it to the configured multi-agent system.

    *Note: The number of worker agents can also be set via the `OLLAMA_WORKER_COUNT` environment variable before starting the Node.js server. The dashboard configuration will override this for subsequent changes.*

    Deactivate the virtual environment when done (optional):
    ```bash
    deactivate
    ```

## Running Tests

To run all unit tests for both the TypeScript backend and the Python dashboard:

```bash
npm test
```

This command will execute Jest tests for the Node.js part and Pytest tests for the Flask dashboard.

## Project Structure

```
ollama-flow/
├───.git/
├───dashboard/              # Python Flask dashboard application
│   ├───app.py
│   ├───templates/
│   │   └───index.html
│   ├───venv/               # Python Virtual Environment
│   └───test_app.py         # Python unit tests
├───dist/                   # Compiled TypeScript output
├───node_modules/           # Node.js dependencies
├───src/                    # TypeScript source code
│   ├───agent.ts            # Base Agent and Message definitions
│   ├───orchestrator.ts     # Manages agents and message dispatching
│   ├───server.ts           # Node.js Express server
│   ├───worker.ts           # OllamaAgent (renamed from worker.ts)
│   ├───queenAgent.ts       # Main Queen Agent logic
│   ├───subQueenAgent.ts    # Sub-Queen Agent logic for hierarchical architecture
│   └───__tests__/          # TypeScript unit tests
│       └───orchestrator.test.ts
├───.gitignore
├───package.json
├───package-lock.json
├───tsconfig.json
├───jest.config.cjs         # Jest configuration for TypeScript tests
├───install.bat             # Windows installation script
└───install.sh              # Linux/macOS installation script
```
