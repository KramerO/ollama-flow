import type { Orchestrator } from './orchestrator.ts';

export type ArchitectureType = 'FULLY_CONNECTED' | 'CENTRALIZED' | 'HIERARCHICAL';

export interface AgentMessage {
  senderId: string;
  receiverId: string;
  type: string; // e.g., 'task', 'response', 'query'
  content: any; // The actual message payload
  requestId?: string | undefined; // Optional: ID to link messages in a conversation flow
}

export interface Agent {
  id: string;
  name: string;
  receiveMessage(message: AgentMessage): Promise<void>;
}

export abstract class BaseAgent implements Agent {
  id: string;
  name: string;
  protected orchestrator: Orchestrator | null = null;

  constructor(id: string, name: string) {
    this.id = id;
    this.name = name;
  }

  setOrchestrator(orchestrator: Orchestrator): void {
    this.orchestrator = orchestrator;
  }

  abstract receiveMessage(message: AgentMessage): Promise<void>;

  protected async sendMessage(receiverId: string, type: string, content: any, requestId?: string | undefined): Promise<void> {
    if (!this.orchestrator) {
      console.error(`Agent ${this.name} (${this.id}) cannot send message: Orchestrator not set.`);
      return;
    }
    const message: AgentMessage = {
      senderId: this.id,
      receiverId: receiverId,
      type: type,
      content: content,
      requestId: requestId as string | undefined,
    };
    await this.orchestrator.dispatchMessage(message);
  }
}