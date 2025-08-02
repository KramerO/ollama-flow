#!/usr/bin/env node

import { Command } from 'commander';
import { Orchestrator } from './orchestrator.ts';

const program = new Command();
const orchestrator = new Orchestrator();

program
  .version('1.0.0')
  .description('Ollama Flow CLI');

program
  .command('run <prompt>')
  .description('Run a prompt through the orchestrator')
  .action(async (prompt) => {
    try {
      const result = await orchestrator.run(prompt);
      console.log(result);
    } catch (error) {
      console.error('Error running command:', error);
    }
  });

program.parse(process.argv);