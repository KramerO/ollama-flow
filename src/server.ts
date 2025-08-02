
import express from 'express';
import { Orchestrator } from './orchestrator.ts';

const app = express();
const port = 3000;
const orchestrator = new Orchestrator();

app.use(express.json());

app.post('/run', async (req, res) => {
  const { prompt } = req.body;
  if (!prompt) {
    return res.status(400).send('Prompt is required');
  }
  try {
    const result = await orchestrator.run(prompt);
    res.json({ result });
  } catch (error) {
    console.error('Error processing request:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.post('/configure_architecture', (req, res) => {
  const { architectureType, workerCount } = req.body;
  if (!architectureType || !workerCount) {
    return res.status(400).send('architectureType and workerCount are required');
  }
  try {
    orchestrator.reconfigureAgents(architectureType, workerCount);
    res.json({ message: 'Agent architecture reconfigured successfully' });
  } catch (error) {
    console.error('Error reconfiguring agents:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.post('/set_project_folder', (req, res) => {
  const { projectFolderPath } = req.body;
  if (!projectFolderPath) {
    return res.status(400).send('projectFolderPath is required');
  }
  try {
    orchestrator.setProjectFolder(projectFolderPath);
    res.json({ message: 'Project folder path set successfully' });
  } catch (error) {
    console.error('Error setting project folder:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.get('/get_ollama_models', async (req, res) => {
  try {
    const models = await orchestrator.getOllamaModels();
    res.json({ models });
  } catch (error) {
    console.error('Error getting Ollama models:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.post('/set_ollama_model', (req, res) => {
  const { modelName } = req.body;
  if (!modelName) {
    return res.status(400).send('modelName is required');
  }
  try {
    orchestrator.setCurrentOllamaModel(modelName);
    res.json({ message: `Ollama model set to ${modelName}` });
  } catch (error) {
    console.error('Error setting Ollama model:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.listen(port, () => {
  console.log(`Ollama Flow server listening at http://localhost:${port}`);
});
