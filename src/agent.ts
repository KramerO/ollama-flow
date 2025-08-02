export interface AgentMessage {
  senderId: string;
  receiverId: string;
  type: string; // e.g., 'task', 'response', 'query'
  content: any; // The actual message payload
}

export interface Agent {
  id: string;
  name: string;
  receiveMessage(message: AgentMessage): Promise<void>;
}
