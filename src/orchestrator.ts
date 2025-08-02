
import type { Agent, AgentMessage } from './agent.ts';
import { BaseAgent } from './agent.ts';
import { OllamaAgent } from './worker.ts';
import { QueenAgent } from './queenAgent.ts';
import { SubQueenAgent } from './subQueenAgent.ts';

export class Orchestrator {
  private agents: Map<string, Agent>;

  constructor() {
    this.agents = new Map<string, Agent>();

    // Instantiate OllamaAgents
    const ollamaAgent1 = new OllamaAgent('ollama-agent-1', 'Ollama Worker 1');
    const ollamaAgent2 = new OllamaAgent('ollama-agent-2', 'Ollama Worker 2');
    const ollamaAgent3 = new OllamaAgent('ollama-agent-3', 'Ollama Worker 3');
    const ollamaAgent4 = new OllamaAgent('ollama-agent-4', 'Ollama Worker 4');

    // Instantiate SubQueenAgents and assign OllamaAgents to them
    const subQueen1 = new SubQueenAgent('sub-queen-1', 'Sub Queen Alpha');
    subQueen1.initializeGroupAgents([ollamaAgent1, ollamaAgent2]);

    const subQueen2 = new SubQueenAgent('sub-queen-2', 'Sub Queen Beta');
    subQueen2.initializeGroupAgents([ollamaAgent3, ollamaAgent4]);

    // Instantiate Main QueenAgent
    const queenAgent = new QueenAgent('queen-agent-1', 'Main Queen');

    // Register all agents
    this.registerAgent(queenAgent);
    this.registerAgent(subQueen1);
    this.registerAgent(subQueen2);
    this.registerAgent(ollamaAgent1);
    this.registerAgent(ollamaAgent2);
    this.registerAgent(ollamaAgent3);
    this.registerAgent(ollamaAgent4);

    // Set orchestrator reference for all BaseAgents
    this.agents.forEach(agent => {
      if (agent instanceof BaseAgent) {
        agent.setOrchestrator(this);
      }
    });

    // Initialize QueenAgent after all agents are registered and orchestrator is set
    const queen = this.agents.get('queen-agent-1');
    if (queen instanceof QueenAgent) {
      queen.initializeAgents();
    }
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

  getAgentsByType<T extends BaseAgent>(type: new (...args: any[]) => T): T[] {
    const foundAgents: T[] = [];
    this.agents.forEach(agent => {
      if (agent instanceof type) {
        foundAgents.push(agent);
      }
    });
    return foundAgents;
  }

  async run(prompt: string): Promise<string> {
    console.log('Orchestrator received prompt:', prompt);
    // Send the initial prompt to the QueenAgent
    const initialMessage: AgentMessage = {
      senderId: 'orchestrator',
      receiverId: 'queen-agent-1',
      type: 'task',
      content: prompt,
    };
    await this.dispatchMessage(initialMessage);

    // In a real scenario, the orchestrator would wait for a response from the QueenAgent
    // and return it. For this basic setup, we just log the action.
    return `Initial prompt sent to QueenAgent (queen-agent-1): ${prompt}`;
  }
}
