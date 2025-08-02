
import type { Agent, AgentMessage } from './agent.ts';
import { BaseAgent } from './agent.ts';
import { OllamaAgent } from './worker.ts';
import { QueenAgent } from './queenAgent.ts';
import { SubQueenAgent } from './subQueenAgent.ts';

export class Orchestrator {
  private agents: Map<string, Agent>;

  constructor() {
    this.agents = new Map<string, Agent>();

    const DEFAULT_WORKER_COUNT = 4;
    const DEFAULT_SUB_QUEEN_COUNT = 2;

    const workerCount = parseInt(process.env.OLLAMA_WORKER_COUNT || '', 10) || DEFAULT_WORKER_COUNT;
    const subQueenCount = DEFAULT_SUB_QUEEN_COUNT; // For now, keep sub-queen count fixed

    const ollamaAgents: OllamaAgent[] = [];
    for (let i = 0; i < workerCount; i++) {
      const agent = new OllamaAgent(`ollama-agent-${i + 1}`, `Ollama Worker ${i + 1}`);
      ollamaAgents.push(agent);
    }

    const subQueenAgents: SubQueenAgent[] = [];
    const subQueenGroups: OllamaAgent[][] = Array.from({ length: subQueenCount }, () => []);

    for (let i = 0; i < subQueenCount; i++) {
      const subQueen = new SubQueenAgent(`sub-queen-${i + 1}`, `Sub Queen ${String.fromCharCode(65 + i)}`);
      subQueenAgents.push(subQueen);
    }

    // Distribute OllamaAgents among SubQueenAgents
    ollamaAgents.forEach((agent, index) => {
      subQueenGroups[index % subQueenCount].push(agent);
    });

    // Initialize SubQueenAgents with their assigned OllamaAgents
    subQueenAgents.forEach((subQueen, index) => {
      subQueen.initializeGroupAgents(subQueenGroups[index]);
    });

    // Register all agents
    const queenAgent = new QueenAgent('queen-agent-1', 'Main Queen');
    this.registerAgent(queenAgent);
    subQueenAgents.forEach(sq => this.registerAgent(sq));
    ollamaAgents.forEach(oa => this.registerAgent(oa));

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
