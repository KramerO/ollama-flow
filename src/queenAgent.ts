import { BaseAgent, type AgentMessage, type ArchitectureType } from './agent.ts';
import { OllamaAgent } from './worker.ts'; // Import OllamaAgent to use its type
import { SubQueenAgent } from './subQueenAgent.ts';

export class QueenAgent extends BaseAgent {
  private subQueenAgents: SubQueenAgent[] = [];
  private ollamaAgents: OllamaAgent[] = []; // Added for CENTRALIZED/FULLY_CONNECTED
  private currentSubQueenIndex: number = 0;
  private currentOllamaAgentIndex: number = 0; // Added for CENTRALIZED/FULLY_CONNECTED
  private architectureType: ArchitectureType;

  constructor(id: string, name: string, architectureType: ArchitectureType) {
    super(id, name);
    this.architectureType = architectureType;
  }

  // This method will be called by the Orchestrator after all agents are registered
  // and the orchestrator reference is set.
  initializeAgents(): void {
    if (this.orchestrator) {
      if (this.architectureType === 'HIERARCHICAL') {
        this.subQueenAgents = this.orchestrator.getAgentsByType(SubQueenAgent);
        console.log(`QueenAgent ${this.name} found ${this.subQueenAgents.length} SubQueenAgents.`);
      } else if (this.architectureType === 'CENTRALIZED' || this.architectureType === 'FULLY_CONNECTED') {
        this.ollamaAgents = this.orchestrator.getAgentsByType(OllamaAgent);
        console.log(`QueenAgent ${this.name} found ${this.ollamaAgents.length} OllamaAgents.`);
      }
    }
  }

  async receiveMessage(message: AgentMessage): Promise<void> {
    console.log(`QueenAgent ${this.name} (${this.id}) received message from ${message.senderId}: ${message.content}`);

    if (message.type === 'task') {
      if (this.architectureType === 'HIERARCHICAL') {
        if (this.subQueenAgents.length === 0) {
          console.warn('No SubQueenAgents available to delegate tasks.');
          return;
        }

        // Select a SubQueenAgent in a round-robin fashion
        const targetSubQueen = this.subQueenAgents[this.currentSubQueenIndex];
        this.currentSubQueenIndex = (this.currentSubQueenIndex + 1) % this.subQueenAgents.length;

        if (!targetSubQueen) {
          console.error('No valid SubQueenAgent found for delegation.');
          return;
        }

        const delegatedTask = `Delegated task from Main Queen to ${targetSubQueen.name}: ${message.content}`;
        console.log(`QueenAgent delegating task to ${targetSubQueen.name} (${targetSubQueen.id})`);
        await this.sendMessage(targetSubQueen.id, 'sub-task-to-subqueen', delegatedTask);
      } else if (this.architectureType === 'CENTRALIZED' || this.architectureType === 'FULLY_CONNECTED') {
        if (this.ollamaAgents.length === 0) {
          console.warn('No OllamaAgents available to delegate tasks.');
          return;
        }

        // Select an OllamaAgent in a round-robin fashion
        const targetOllamaAgent = this.ollamaAgents[this.currentOllamaAgentIndex];
        this.currentOllamaAgentIndex = (this.currentOllamaAgentIndex + 1) % this.ollamaAgents.length;

        if (!targetOllamaAgent) {
          console.error('No valid OllamaAgent found for delegation.');
          return;
        }

        const delegatedTask = `Delegated task from Queen to ${targetOllamaAgent.name}: ${message.content}`;
        console.log(`QueenAgent delegating task to ${targetOllamaAgent.name} (${targetOllamaAgent.id})`);
        await this.sendMessage(targetOllamaAgent.id, 'sub-task', delegatedTask);
      }
    } else if (message.type === 'group-response') {
      console.log(`QueenAgent received group response from ${message.senderId}: ${JSON.stringify(message.content)}`);
      // Process the response from the SubQueenAgent
      // For now, just forward it as a final response to the orchestrator
      await this.sendMessage('orchestrator', 'final-response', `Aggregated response from ${message.content.fromSubQueen}: ${message.content.content}`);
    } else if (message.type === 'response') {
      // This is a direct response from an OllamaAgent in CENTRALIZED or FULLY_CONNECTED
      console.log(`QueenAgent received direct response from ${message.senderId}: ${message.content}`);
      await this.sendMessage('orchestrator', 'final-response', `Response from ${message.senderId}: ${message.content}`);
    } else if (message.type === 'error') {
      console.error(`QueenAgent received error from ${message.senderId}: ${message.content}`);
      await this.sendMessage('orchestrator', 'final-error', `Error from ${message.senderId}: ${message.content}`);
    }
  }
}
