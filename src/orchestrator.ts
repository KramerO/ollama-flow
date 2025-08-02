
import type { Agent, AgentMessage, ArchitectureType } from './agent.ts';
import { BaseAgent } from './agent.ts';
import { OllamaAgent } from './worker.ts';
import { QueenAgent } from './queenAgent.ts';
import { SubQueenAgent } from './subQueenAgent.ts';

export class Orchestrator {
  private agents: Map<string, Agent>;
  private currentArchitecture: ArchitectureType;

  constructor() {
    this.agents = new Map<string, Agent>();
    this.currentArchitecture = 'HIERARCHICAL'; // Default architecture
    this.reconfigureAgents(this.currentArchitecture, parseInt(process.env.OLLAMA_WORKER_COUNT || '', 10) || 4);
  }

  reconfigureAgents(architectureType: ArchitectureType, workerCount: number): void {
    console.log(`Reconfiguring agents for architecture: ${architectureType} with ${workerCount} workers.`);
    this.agents.clear(); // Clear existing agents
    this.currentArchitecture = architectureType;

    const DEFAULT_SUB_QUEEN_COUNT = 2; // For now, keep sub-queen count fixed

    const ollamaAgents: OllamaAgent[] = [];
    for (let i = 0; i < workerCount; i++) {
      const agent = new OllamaAgent(`ollama-agent-${i + 1}`, `Ollama Worker ${i + 1}`);
      ollamaAgents.push(agent);
    }

    const queenAgent = new QueenAgent('queen-agent-1', 'Main Queen');
    this.registerAgent(queenAgent);

    if (architectureType === 'HIERARCHICAL') {
      const subQueenAgents: SubQueenAgent[] = [];
      const subQueenGroups: OllamaAgent[][] = Array.from({ length: DEFAULT_SUB_QUEEN_COUNT }, () => []);

      for (let i = 0; i < DEFAULT_SUB_QUEEN_COUNT; i++) {
        const subQueen = new SubQueenAgent(`sub-queen-${i + 1}`, `Sub Queen ${String.fromCharCode(65 + i)}`);
        subQueenAgents.push(subQueen);
      }

      // Distribute OllamaAgents among SubQueenAgents
      ollamaAgents.forEach((agent, index) => {
        subQueenGroups[index % DEFAULT_SUB_QUEEN_COUNT]!.push(agent);
      });

      // Initialize SubQueenAgents with their assigned OllamaAgents
      subQueenAgents.forEach((subQueen, index) => {
        subQueen.initializeGroupAgents(subQueenGroups[index]!);
        this.registerAgent(subQueen);
      });
    } else if (architectureType === 'FULLY_CONNECTED' || architectureType === 'CENTRALIZED') {
      // For these architectures, OllamaAgents are directly managed by the Queen or Orchestrator
      // No SubQueens needed
    }

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
    let targetReceiverId: string;

    switch (this.currentArchitecture) {
      case 'FULLY_CONNECTED':
      case 'CENTRALIZED':
      case 'HIERARCHICAL':
        targetReceiverId = 'queen-agent-1';
        break;
      default:
        targetReceiverId = 'queen-agent-1'; // Fallback
    }

    const initialMessage: AgentMessage = {
      senderId: 'orchestrator',
      receiverId: targetReceiverId,
      type: 'task',
      content: prompt,
    };
    await this.dispatchMessage(initialMessage);

    return `Initial prompt sent to ${targetReceiverId}: ${prompt}`;
  }
}
