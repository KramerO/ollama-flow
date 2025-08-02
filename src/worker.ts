
import ollama from 'ollama';

export class Worker {
  private model: string;

  constructor(model: string = 'llama3') {
    this.model = model;
  }

  async performTask(prompt: string): Promise<string> {
    try {
      const response = await ollama.chat({
        model: this.model,
        messages: [{ role: 'user', content: prompt }],
      });
      return response.message.content;
    } catch (error) {
      console.error('Error performing task:', error);
      throw error;
    }
  }
}
