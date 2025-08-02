
import ollama from 'ollama';
import { type AgentMessage, BaseAgent } from './agent.ts';
import * as fs from 'fs/promises';
import * as path from 'path';

export class OllamaAgent extends BaseAgent {
  private model: string;
  private projectFolderPath: string | null;

  constructor(id: string, name: string, model?: string, projectFolderPath: string | null = null) {
    super(id, name);
    this.model = model || 'llama3'; // Use provided model or default to 'llama3'
    this.projectFolderPath = projectFolderPath;
  }

  async receiveMessage(message: AgentMessage): Promise<void> {
    console.log(`Agent ${this.name} (${this.id}) received message from ${message.senderId}: ${message.content}`);
    // Assuming the content of the message is the prompt for the Ollama model
    try {
      const result = await this.performTask(message.content);
      console.log(`Agent ${this.name} (${this.id}) completed task with result: ${result}`);

      let saveMessage = '';
      const saveMatch = message.content.match(/(?:speichere sie (?:im Projektordner )?unter|speichere sie als)\s+(.+?)(?:\s+ab)?$/i);
      if (saveMatch && this.projectFolderPath) {
        let targetPath = saveMatch[1].trim();
        let fullPath: string;

        // Check if the extracted path is absolute
        if (path.isAbsolute(targetPath)) {
          fullPath = targetPath;
        } else {
          // If relative, join with project folder path
          fullPath = path.join(this.projectFolderPath, targetPath);
        }
        
        // Extract code block from the result
        const codeBlockMatch = result.match(/```[\s\S]*?\n([\s\S]*?)\n```/);
        const codeContent = codeBlockMatch ? codeBlockMatch[1] : result; // Use full result if no code block found
        const contentToWrite = typeof codeContent === 'string' ? codeContent : String(codeContent); // Ensure it's a string

        console.log(`[OllamaAgent] Attempting to save file. Full Path: ${fullPath}, Content Length: ${contentToWrite.length}`);
        try {
          const dirName = path.dirname(fullPath);
          await fs.mkdir(dirName, { recursive: true });
          await fs.writeFile(fullPath, contentToWrite);
          saveMessage = `
File saved to: ${fullPath}`;
          console.log(saveMessage);
        } catch (fileError) {
          saveMessage = `\nError saving file to ${fullPath}: ${fileError instanceof Error ? fileError.message : String(fileError)}`;
          console.error(saveMessage);
        }
      }

      await this.sendMessage(message.senderId, 'response', result + saveMessage);
    } catch (error) {
      console.error(`Agent ${this.name} (${this.id}) failed to perform task:`, error);
      await this.sendMessage(message.senderId, 'error', `Failed to perform task: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async performTask(prompt: string): Promise<string> {
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
