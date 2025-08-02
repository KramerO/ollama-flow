
import { AgentMessage, type Agent } from './agent.ts';
import { OllamaAgent } from './worker.ts';

export class Orchestrator {
  private agents: Map<string, Agent>;

  constructor() {
    this.agents = new Map<string, Agent>();
    // Register a default OllamaAgent for initial testing
    const defaultOllamaAgent = new OllamaAgent('ollama-agent-1', 'Default Ollama Agent');
    this.registerAgent(defaultOllamaAgent);
  }

  registerAgent(agent: Agent): void {
    if (this.agents.has(agent.id)) {
      console.warn(`Agent with ID ${agent.id} already registered. Overwriting.`);
    }
    this.agents.set(agent.id, agent);
    console.log(`Agent ${agent.name} (${agent.id}) registered.`);
  }

  async dispatchMessage(message: AgentMessage): Promise<void> {
    const receiver = this.agents.get(message.receiverId);
    if (receiver) {
      console.log(`Dispatching message from ${message.senderId} to ${message.receiverId}`);
      await receiver.receiveMessage(message);
    } else {
      console.error(`Agent with ID ${message.receiverId} not found.`);
    }
  }

  async run(prompt: string): Promise<string> {
    console.log('Orchestrator received prompt:', prompt);
    // For now, we'll hardcode sending the prompt to the default OllamaAgent
    const message: AgentMessage = {
      senderId: 'orchestrator',
      receiverId: 'ollama-agent-1',
      type: 'task',
      content: prompt,
    };
    await this.dispatchMessage(message);
    // In a real scenario, the orchestrator would wait for a response from the agent
    // and return it. For this basic setup, we just log the action.
    return `Prompt sent to ollama-agent-1: ${prompt}`;
  }
}
