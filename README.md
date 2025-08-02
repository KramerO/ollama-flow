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

To run Ollama Flow, you need to start both the Node.js server and the Python dashboard.

1.  **Start the Ollama Flow Server (Node.js):**

    Open your terminal or command prompt, navigate to the project root directory, and run:
    ```bash
    npm run start:server
    ```
    This server will listen on `http://localhost:3000`.

2.  **Start the Ollama Flow Dashboard (Python):**

    Open a **separate** terminal or command prompt, navigate to the project root directory, and run:
    ```bash
    cd dashboard
    # Activate the virtual environment
    # For Windows:
    .\venv\Scripts\activate
    # For Linux/macOS:
    source venv/bin/activate

    # Run the Flask application
    python app.py

    # Deactivate the virtual environment when done (optional)
    deactivate
    ```
    The dashboard will be accessible in your web browser at `http://localhost:5000`.

3.  **Configure and Interact via the Dashboard:**

    -   Open your web browser and go to `http://localhost:5000`.
    -   You will find options to select the **Agent Architecture** (Hierarchical, Centralized, Fully Connected) and set the **Number of Worker Agents**.
    -   Apply your desired configuration.
    -   Enter your prompt in the provided text area and click "Run Ollama Flow" to send it to the configured multi-agent system.

    *Note: The number of worker agents can also be set via the `OLLAMA_WORKER_COUNT` environment variable before starting the Node.js server. The dashboard configuration will override this for subsequent changes.*

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
