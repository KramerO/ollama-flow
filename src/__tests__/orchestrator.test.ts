import { Orchestrator } from '../orchestrator.ts';
import { OllamaAgent } from '../worker.ts';
import { QueenAgent } from '../queenAgent.ts';
import { SubQueenAgent } from '../subQueenAgent.ts';
import type { AgentMessage } from '../agent.ts';

// Mock the ollama module to prevent actual API calls during tests
jest.mock('ollama', () => ({
  chat: jest.fn(() => Promise.resolve({ message: { content: 'Mocked Ollama Response' } })),
}));

describe('Orchestrator and Agent Communication', () => {
  let orchestrator: Orchestrator;
  let consoleSpy: jest.SpyInstance;

  beforeEach(() => {
    // Reset environment variable for consistent testing
    process.env.OLLAMA_WORKER_COUNT = '4';
    orchestrator = new Orchestrator();
    consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleSpy.mockRestore();
    jest.restoreAllMocks();
  });

  it('should register agents correctly', () => {
    expect(orchestrator['agents'].size).toBeGreaterThan(0);
    expect(orchestrator['agents'].has('queen-agent-1')).toBe(true);
    expect(orchestrator['agents'].has('sub-queen-1')).toBe(true);
    expect(orchestrator['agents'].has('ollama-agent-1')).toBe(true);
  });

  it('should dispatch a message to the correct receiver', async () => {
    const mockReceiver = {
      id: 'mock-receiver',
      name: 'Mock Receiver',
      receiveMessage: jest.fn(),
    };
    orchestrator['agents'].set(mockReceiver.id, mockReceiver);

    const message: AgentMessage = {
      senderId: 'test-sender',
      receiverId: 'mock-receiver',
      type: 'test',
      content: 'Hello',
    };

    await orchestrator.dispatchMessage(message);
    expect(mockReceiver.receiveMessage).toHaveBeenCalledWith(message);
  });

  it('should handle unknown receiver IDs', async () => {
    const message: AgentMessage = {
      senderId: 'test-sender',
      receiverId: 'unknown-receiver',
      type: 'test',
      content: 'Hello',
    };

    await orchestrator.dispatchMessage(message);
    expect(console.error).toHaveBeenCalledWith('Agent with ID unknown-receiver not found.');
  });

  describe('Hierarchical Architecture Flow', () => {
    it('should send initial prompt to QueenAgent', async () => {
      const prompt = 'Test prompt for Queen';
      const queenAgent = orchestrator['agents'].get('queen-agent-1') as QueenAgent;
      const queenReceiveMessageSpy = jest.spyOn(queenAgent, 'receiveMessage');

      await orchestrator.run(prompt);

      expect(queenReceiveMessageSpy).toHaveBeenCalledWith(expect.objectContaining({
        senderId: 'orchestrator',
        receiverId: 'queen-agent-1',
        type: 'task',
        content: prompt,
      }));
    });

    it('QueenAgent should delegate task to a SubQueenAgent', async () => {
      const prompt = 'Task for SubQueen';
      const queenAgent = orchestrator['agents'].get('queen-agent-1') as QueenAgent;
      const subQueen1 = orchestrator['agents'].get('sub-queen-1') as SubQueenAgent;
      const subQueenReceiveMessageSpy = jest.spyOn(subQueen1, 'receiveMessage');

      // Manually trigger QueenAgent to receive a task message
      await queenAgent.receiveMessage({
        senderId: 'orchestrator',
        receiverId: 'queen-agent-1',
        type: 'task',
        content: prompt,
      });

      // Expect the Queen to delegate to a SubQueen
      expect(subQueenReceiveMessageSpy).toHaveBeenCalledWith(expect.objectContaining({
        senderId: 'queen-agent-1',
        type: 'sub-task-to-subqueen',
        content: expect.stringContaining('Delegated task from Main Queen to'),
      }));
    });

    it('SubQueenAgent should delegate task to an OllamaAgent', async () => {
      const prompt = 'Task for Ollama';
      const subQueen1 = orchestrator['agents'].get('sub-queen-1') as SubQueenAgent;
      const ollamaAgent1 = orchestrator['agents'].get('ollama-agent-1') as OllamaAgent;
      const ollamaAgentReceiveMessageSpy = jest.spyOn(ollamaAgent1, 'receiveMessage');

      // Manually trigger SubQueenAgent to receive a sub-task message
      await subQueen1.receiveMessage({
        senderId: 'queen-agent-1',
        receiverId: 'sub-queen-1',
        type: 'sub-task-to-subqueen',
        content: prompt,
      });

      // Expect the SubQueen to delegate to an OllamaAgent
      expect(ollamaAgentReceiveMessageSpy).toHaveBeenCalledWith(expect.objectContaining({
        senderId: 'sub-queen-1',
        type: 'sub-task',
        content: expect.stringContaining('Delegated by Sub Queen A to'),
      }));
    });

    it('OllamaAgent should process task and send response back to its SubQueenAgent', async () => {
      const prompt = 'Ollama task';
      const ollamaAgent1 = orchestrator['agents'].get('ollama-agent-1') as OllamaAgent;
      const subQueen1 = orchestrator['agents'].get('sub-queen-1') as SubQueenAgent;
      const subQueenReceiveMessageSpy = jest.spyOn(subQueen1, 'receiveMessage');

      // Manually trigger OllamaAgent to receive a sub-task message
      await ollamaAgent1.receiveMessage({
        senderId: 'sub-queen-1',
        receiverId: 'ollama-agent-1',
        type: 'sub-task',
        content: prompt,
      });

      // Expect OllamaAgent to send response back to its SubQueenAgent
      expect(subQueenReceiveMessageSpy).toHaveBeenCalledWith(expect.objectContaining({
        senderId: 'ollama-agent-1',
        receiverId: 'sub-queen-1',
        type: 'response',
        content: 'Mocked Ollama Response',
      }));
    });

    it('QueenAgent should receive group response and send final response to orchestrator', async () => {
      const responseContent = { fromSubQueen: 'sub-queen-1', originalSender: 'ollama-agent-1', type: 'response', content: 'SubQueen processed' };
      const queenAgent = orchestrator['agents'].get('queen-agent-1') as QueenAgent;
      const orchestratorDispatchMessageSpy = jest.spyOn(orchestrator, 'dispatchMessage');

      // Manually trigger QueenAgent to receive a group-response message
      await queenAgent.receiveMessage({
        senderId: 'sub-queen-1',
        receiverId: 'queen-agent-1',
        type: 'group-response',
        content: responseContent,
      });

      // Expect QueenAgent to send final response to orchestrator
      expect(orchestratorDispatchMessageSpy).toHaveBeenCalledWith(expect.objectContaining({
        senderId: 'queen-agent-1',
        receiverId: 'orchestrator',
        type: 'final-response',
        content: expect.stringContaining('Aggregated response from sub-queen-1'),
      }));
    });
  });
});
