#!/usr/bin/env python3
"""
GPU-Based Auto-Scaling System
Skaliert Agents basierend auf verfügbarem GPU-Speicher und GPU-Auslastung
"""

import asyncio
import time
import statistics
import subprocess
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging
import psutil
from pathlib import Path

logger = logging.getLogger(__name__)

class GPUVendor(Enum):
    """Unterstützte GPU-Hersteller"""
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    UNKNOWN = "unknown"

@dataclass
class GPUInfo:
    """GPU-Informationen und Status"""
    index: int
    name: str
    vendor: GPUVendor
    total_memory_mb: int
    used_memory_mb: int
    free_memory_mb: int
    utilization_percent: float
    temperature: Optional[float] = None
    power_usage_w: Optional[float] = None
    driver_version: str = ""
    
    @property
    def memory_utilization_percent(self) -> float:
        """GPU-Memory-Auslastung in Prozent"""
        return (self.used_memory_mb / self.total_memory_mb * 100) if self.total_memory_mb > 0 else 0.0
    
    @property
    def available_memory_percent(self) -> float:
        """Verfügbarer GPU-Speicher in Prozent"""
        return 100.0 - self.memory_utilization_percent

@dataclass
class ModelMemoryRequirements:
    """Memory-Anforderungen für verschiedene LLM-Modelle"""
    model_name: str
    min_memory_mb: int
    recommended_memory_mb: int
    context_length: int
    parameters: str
    quantization: str = "fp16"

class GPUMonitor:
    """Überwacht GPU-Status für Auto-Scaling-Entscheidungen"""
    
    def __init__(self):
        self.gpus: List[GPUInfo] = []
        self.vendor = GPUVendor.UNKNOWN
        self.monitoring_interval = 10.0  # Sekunden
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Model Memory Requirements (basierend auf gängigen LLM-Größen)
        self.model_requirements = {
            "phi3:mini": ModelMemoryRequirements(
                model_name="phi3:mini", 
                min_memory_mb=2048, 
                recommended_memory_mb=3072,
                context_length=4096,
                parameters="3.8B"
            ),
            "llama3:8b": ModelMemoryRequirements(
                model_name="llama3:8b",
                min_memory_mb=5120,
                recommended_memory_mb=6144,
                context_length=8192,
                parameters="8B"
            ),
            "codellama:7b": ModelMemoryRequirements(
                model_name="codellama:7b",
                min_memory_mb=4608,
                recommended_memory_mb=5632,
                context_length=16384,
                parameters="7B"
            ),
            "llama3:13b": ModelMemoryRequirements(
                model_name="llama3:13b", 
                min_memory_mb=8192,
                recommended_memory_mb=10240,
                context_length=8192,
                parameters="13B"
            ),
            "llama3:70b": ModelMemoryRequirements(
                model_name="llama3:70b",
                min_memory_mb=40960,
                recommended_memory_mb=49152,
                context_length=8192,
                parameters="70B"
            )
        }
        
        self._detect_gpu_vendor()
    
    def _detect_gpu_vendor(self) -> GPUVendor:
        """Erkennt den GPU-Hersteller"""
        try:
            # NVIDIA GPU Check
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                self.vendor = GPUVendor.NVIDIA
                logger.info("🎮 Detected NVIDIA GPU(s)")
                return self.vendor
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # AMD GPU Check (rocm-smi)
            result = subprocess.run(['rocm-smi', '--showproductname'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.vendor = GPUVendor.AMD
                logger.info("🎮 Detected AMD GPU(s)")
                return self.vendor
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Intel GPU Check (intel_gpu_top)
            result = subprocess.run(['intel_gpu_top', '-l'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.vendor = GPUVendor.INTEL
                logger.info("🎮 Detected Intel GPU(s)")
                return self.vendor
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("🎮 No GPU detected or unsupported vendor")
        self.vendor = GPUVendor.UNKNOWN
        return self.vendor
    
    async def refresh_gpu_info(self) -> List[GPUInfo]:
        """Aktualisiert GPU-Informationen"""
        if self.vendor == GPUVendor.NVIDIA:
            return await self._get_nvidia_info()
        elif self.vendor == GPUVendor.AMD:
            return await self._get_amd_info()
        elif self.vendor == GPUVendor.INTEL:
            return await self._get_intel_info()
        else:
            return []
    
    async def _get_nvidia_info(self) -> List[GPUInfo]:
        """Sammelt NVIDIA GPU-Informationen"""
        try:
            # GPU Memory Info
            cmd = [
                'nvidia-smi', 
                '--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw,driver_version',
                '--format=csv,noheader,nounits'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            if process.returncode != 0:
                logger.error(f"nvidia-smi failed: {stderr.decode()}")
                return []
            
            gpus = []
            for line in stdout.decode().strip().split('\n'):
                if not line.strip():
                    continue
                
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 7:
                    try:
                        gpu_info = GPUInfo(
                            index=int(parts[0]),
                            name=parts[1],
                            vendor=GPUVendor.NVIDIA,
                            total_memory_mb=int(parts[2]),
                            used_memory_mb=int(parts[3]),
                            free_memory_mb=int(parts[4]),
                            utilization_percent=float(parts[5]) if parts[5] != 'N/A' else 0.0,
                            temperature=float(parts[6]) if parts[6] != 'N/A' else None,
                            power_usage_w=float(parts[7]) if len(parts) > 7 and parts[7] != 'N/A' else None,
                            driver_version=parts[8] if len(parts) > 8 else ""
                        )
                        gpus.append(gpu_info)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing GPU info line '{line}': {e}")
            
            self.gpus = gpus
            return gpus
            
        except asyncio.TimeoutError:
            logger.error("nvidia-smi command timeout")
        except Exception as e:
            logger.error(f"Error getting NVIDIA GPU info: {e}")
        
        return []
    
    async def _get_amd_info(self) -> List[GPUInfo]:
        """Sammelt AMD GPU-Informationen"""
        try:
            # AMD ROCm Info
            process = await asyncio.create_subprocess_exec(
                'rocm-smi', '--showmeminfo', 'vram', '--showuse',
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            if process.returncode != 0:
                logger.error(f"rocm-smi failed: {stderr.decode()}")
                return []
            
            # AMD Output parsing (simplified)
            gpus = []
            output = stdout.decode()
            
            # Basic AMD GPU detection - would need more sophisticated parsing
            gpu_info = GPUInfo(
                index=0,
                name="AMD GPU",
                vendor=GPUVendor.AMD,
                total_memory_mb=8192,  # Fallback values
                used_memory_mb=1024,
                free_memory_mb=7168,
                utilization_percent=0.0
            )
            gpus.append(gpu_info)
            
            self.gpus = gpus
            return gpus
            
        except Exception as e:
            logger.error(f"Error getting AMD GPU info: {e}")
        
        return []
    
    async def _get_intel_info(self) -> List[GPUInfo]:
        """Sammelt Intel GPU-Informationen"""
        try:
            # Intel GPU Info (limited support)
            gpu_info = GPUInfo(
                index=0,
                name="Intel GPU",
                vendor=GPUVendor.INTEL,
                total_memory_mb=4096,  # Estimated
                used_memory_mb=512,
                free_memory_mb=3584,
                utilization_percent=0.0
            )
            
            self.gpus = [gpu_info]
            return self.gpus
            
        except Exception as e:
            logger.error(f"Error getting Intel GPU info: {e}")
        
        return []
    
    async def start_monitoring(self):
        """Startet das GPU-Monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🎮 GPU monitoring started")
    
    async def stop_monitoring(self):
        """Stoppt das GPU-Monitoring"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("🎮 GPU monitoring stopped")
    
    async def _monitoring_loop(self):
        """Haupt-Monitoring-Schleife"""
        while self.running:
            try:
                await self.refresh_gpu_info()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in GPU monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    def get_total_gpu_memory(self) -> int:
        """Gibt den gesamten verfügbaren GPU-Speicher zurück (MB)"""
        return sum(gpu.total_memory_mb for gpu in self.gpus)
    
    def get_available_gpu_memory(self) -> int:
        """Gibt den verfügbaren GPU-Speicher zurück (MB)"""
        return sum(gpu.free_memory_mb for gpu in self.gpus)
    
    def get_gpu_utilization(self) -> float:
        """Gibt die durchschnittliche GPU-Auslastung zurück"""
        if not self.gpus:
            return 0.0
        return statistics.mean(gpu.utilization_percent for gpu in self.gpus)
    
    def get_memory_utilization(self) -> float:
        """Gibt die durchschnittliche Memory-Auslastung zurück"""
        if not self.gpus:
            return 0.0
        return statistics.mean(gpu.memory_utilization_percent for gpu in self.gpus)

class GPUAutoScaler:
    """GPU-basiertes Auto-Scaling für AI-Agents"""
    
    def __init__(self, default_model: str = "phi3:mini"):
        self.gpu_monitor = GPUMonitor()
        self.default_model = default_model
        self.current_model = default_model
        self.running = False
        self.scaling_task: Optional[asyncio.Task] = None
        
        # Scaling-Konfiguration
        self.scaling_config = {
            'min_agents': 1,
            'max_agents': 8,  # Wird basierend auf GPU-Memory angepasst
            'memory_buffer_mb': 1024,  # Reserve-Speicher
            'memory_safety_margin': 0.15,  # 15% Sicherheitsspielraum
            'scale_up_threshold': 0.75,  # Scale up wenn Memory > 75% genutzt
            'scale_down_threshold': 0.40,  # Scale down wenn Memory < 40% genutzt
            'scale_check_interval': 15.0,  # Sekunden
            'cooldown_period': 30.0,  # Sekunden zwischen Scaling-Aktionen
        }
        
        self.last_scale_action = 0.0
        self.current_agent_count = 0
        self.target_agent_count = 0
        self.scaling_callback: Optional[callable] = None
    
    def set_scaling_callback(self, callback: callable):
        """Setzt die Callback-Funktion für Scaling-Aktionen"""
        self.scaling_callback = callback
    
    def set_model(self, model_name: str):
        """Setzt das aktuelle Modell und passt Scaling-Parameter an"""
        self.current_model = model_name
        logger.info(f"🎮 GPU Auto-Scaler switched to model: {model_name}")
        
        # Max Agents basierend auf GPU-Memory und Modell-Requirements neu berechnen
        self._recalculate_max_agents()
    
    def _recalculate_max_agents(self):
        """Berechnet die maximale Anzahl Agents basierend auf GPU-Memory"""
        total_memory = self.gpu_monitor.get_total_gpu_memory()
        if total_memory == 0:
            logger.warning("🎮 No GPU memory detected, using CPU-based limits")
            self.scaling_config['max_agents'] = 4
            return
        
        model_req = self.gpu_monitor.model_requirements.get(self.current_model)
        if not model_req:
            logger.warning(f"🎮 Unknown model {self.current_model}, using default memory requirements")
            memory_per_agent = 3072  # Default: 3GB per agent
        else:
            memory_per_agent = model_req.recommended_memory_mb
        
        # Berücksichtige Sicherheitsspielraum und Buffer
        usable_memory = total_memory * (1 - self.scaling_config['memory_safety_margin'])
        usable_memory -= self.scaling_config['memory_buffer_mb']
        
        max_agents = max(1, int(usable_memory // memory_per_agent))
        self.scaling_config['max_agents'] = min(max_agents, 16)  # Hardware-Limit
        
        logger.info(f"🎮 GPU Memory: {total_memory}MB total, max {self.scaling_config['max_agents']} agents "
                   f"for {self.current_model} ({memory_per_agent}MB per agent)")
    
    async def start_autoscaling(self):
        """Startet das automatische Scaling"""
        if self.running:
            return
        
        await self.gpu_monitor.start_monitoring()
        await asyncio.sleep(2)  # Warte auf erste GPU-Daten
        
        self._recalculate_max_agents()
        
        self.running = True
        self.scaling_task = asyncio.create_task(self._scaling_loop())
        logger.info(f"🎮 GPU Auto-Scaling started (model: {self.current_model})")
    
    async def stop_autoscaling(self):
        """Stoppt das automatische Scaling"""
        self.running = False
        if self.scaling_task:
            self.scaling_task.cancel()
            try:
                await self.scaling_task
            except asyncio.CancelledError:
                pass
        
        await self.gpu_monitor.stop_monitoring()
        logger.info("🎮 GPU Auto-Scaling stopped")
    
    async def _scaling_loop(self):
        """Haupt-Scaling-Schleife"""
        while self.running:
            try:
                await self._check_and_scale()
                await asyncio.sleep(self.scaling_config['scale_check_interval'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in GPU scaling loop: {e}")
                await asyncio.sleep(self.scaling_config['scale_check_interval'])
    
    async def _check_and_scale(self):
        """Prüft GPU-Status und führt Scaling aus"""
        # Cooldown prüfen
        if time.time() - self.last_scale_action < self.scaling_config['cooldown_period']:
            return
        
        await self.gpu_monitor.refresh_gpu_info()
        
        if not self.gpu_monitor.gpus:
            logger.warning("🎮 No GPU data available for scaling decisions")
            return
        
        available_memory = self.gpu_monitor.get_available_gpu_memory()
        total_memory = self.gpu_monitor.get_total_gpu_memory()
        memory_utilization = self.gpu_monitor.get_memory_utilization()
        gpu_utilization = self.gpu_monitor.get_gpu_utilization()
        
        # Entscheidungslogik
        scale_decision = self._make_scaling_decision(
            available_memory, total_memory, memory_utilization, gpu_utilization
        )
        
        if scale_decision['action'] != 'none':
            await self._execute_scaling(scale_decision)
    
    def _make_scaling_decision(self, available_memory: int, total_memory: int, 
                             memory_util: float, gpu_util: float) -> Dict[str, Any]:
        """Trifft Scaling-Entscheidung basierend auf GPU-Metriken"""
        
        model_req = self.gpu_monitor.model_requirements.get(self.current_model)
        memory_per_agent = model_req.recommended_memory_mb if model_req else 3072
        
        # Kann ein weiterer Agent gestartet werden?
        can_add_agent = (available_memory >= memory_per_agent + self.scaling_config['memory_buffer_mb'] and 
                        self.current_agent_count < self.scaling_config['max_agents'])
        
        # Sollte ein Agent entfernt werden?
        should_remove_agent = (self.current_agent_count > self.scaling_config['min_agents'] and
                              memory_util < self.scaling_config['scale_down_threshold'] and
                              gpu_util < 30.0)  # Niedrige GPU-Nutzung
        
        # Scale-Up Bedingungen
        if can_add_agent:
            # Memory-Druck
            if memory_util > self.scaling_config['scale_up_threshold']:
                return {
                    'action': 'scale_up',
                    'target_count': self.current_agent_count + 1,
                    'reason': f'High memory utilization: {memory_util:.1f}%'
                }
            
            # Hohe GPU-Nutzung aber noch Memory verfügbar
            if gpu_util > 80.0 and available_memory > memory_per_agent * 1.5:
                return {
                    'action': 'scale_up',
                    'target_count': self.current_agent_count + 1,
                    'reason': f'High GPU utilization: {gpu_util:.1f}%, memory available'
                }
            
            # Proaktives Scaling wenn viel Memory frei ist
            if memory_util < 30.0 and self.current_agent_count < self.scaling_config['max_agents'] // 2:
                return {
                    'action': 'scale_up',
                    'target_count': min(self.current_agent_count + 1, self.scaling_config['max_agents'] // 2),
                    'reason': f'Proactive scaling: {memory_util:.1f}% memory used, plenty available'
                }
        
        # Scale-Down Bedingungen
        if should_remove_agent:
            # Niedrige Auslastung über längere Zeit
            if memory_util < self.scaling_config['scale_down_threshold'] and gpu_util < 20.0:
                return {
                    'action': 'scale_down',
                    'target_count': self.current_agent_count - 1,
                    'reason': f'Low utilization: {memory_util:.1f}% memory, {gpu_util:.1f}% GPU'
                }
        
        return {'action': 'none', 'reason': f'Stable: {memory_util:.1f}% memory, {gpu_util:.1f}% GPU'}
    
    async def _execute_scaling(self, decision: Dict[str, Any]):
        """Führt die Scaling-Aktion aus"""
        action = decision['action']
        target_count = decision['target_count']
        reason = decision['reason']
        
        if self.scaling_callback:
            try:
                success = await self.scaling_callback(action, self.current_agent_count, target_count, reason)
                if success:
                    self.last_scale_action = time.time()
                    self.current_agent_count = target_count
                    logger.info(f"🎮 GPU Auto-Scale {action}: {self.current_agent_count} agents ({reason})")
                else:
                    logger.warning(f"🎮 GPU Auto-Scale {action} failed")
            except Exception as e:
                logger.error(f"Error executing scaling callback: {e}")
        else:
            logger.warning(f"🎮 GPU Auto-Scale {action} requested but no callback set")
    
    def update_agent_count(self, count: int):
        """Aktualisiert die aktuelle Agent-Anzahl"""
        self.current_agent_count = count
    
    def get_gpu_status(self) -> Dict[str, Any]:
        """Gibt detaillierten GPU-Status zurück"""
        gpus_info = []
        for gpu in self.gpu_monitor.gpus:
            gpus_info.append({
                'index': gpu.index,
                'name': gpu.name,
                'vendor': gpu.vendor.value,
                'total_memory_mb': gpu.total_memory_mb,
                'used_memory_mb': gpu.used_memory_mb,
                'free_memory_mb': gpu.free_memory_mb,
                'memory_utilization': gpu.memory_utilization_percent,
                'gpu_utilization': gpu.utilization_percent,
                'temperature': gpu.temperature,
                'power_usage_w': gpu.power_usage_w
            })
        
        return {
            'gpus': gpus_info,
            'total_memory_mb': self.gpu_monitor.get_total_gpu_memory(),
            'available_memory_mb': self.gpu_monitor.get_available_gpu_memory(),
            'average_gpu_utilization': self.gpu_monitor.get_gpu_utilization(),
            'average_memory_utilization': self.gpu_monitor.get_memory_utilization(),
            'current_model': self.current_model,
            'current_agent_count': self.current_agent_count,
            'max_agents': self.scaling_config['max_agents'],
            'scaling_config': self.scaling_config,
            'model_requirements': {
                name: {
                    'min_memory_mb': req.min_memory_mb,
                    'recommended_memory_mb': req.recommended_memory_mb,
                    'parameters': req.parameters
                }
                for name, req in self.gpu_monitor.model_requirements.items()
            }
        }
    
    def get_scaling_recommendations(self) -> Dict[str, Any]:
        """Gibt aktuelle Scaling-Empfehlungen zurück"""
        if not self.gpu_monitor.gpus:
            return {'error': 'No GPU data available'}
        
        available_memory = self.gpu_monitor.get_available_gpu_memory()
        total_memory = self.gpu_monitor.get_total_gpu_memory()
        memory_util = self.gpu_monitor.get_memory_utilization()
        gpu_util = self.gpu_monitor.get_gpu_utilization()
        
        decision = self._make_scaling_decision(available_memory, total_memory, memory_util, gpu_util)
        
        model_req = self.gpu_monitor.model_requirements.get(self.current_model)
        memory_per_agent = model_req.recommended_memory_mb if model_req else 3072
        
        max_theoretical_agents = (available_memory + self.current_agent_count * memory_per_agent) // memory_per_agent
        max_safe_agents = min(max_theoretical_agents, self.scaling_config['max_agents'])
        
        return {
            'current_agents': self.current_agent_count,
            'recommended_action': decision['action'],
            'recommended_count': decision.get('target_count', self.current_agent_count),
            'reason': decision['reason'],
            'max_possible_agents': max_safe_agents,
            'memory_per_agent_mb': memory_per_agent,
            'gpu_status': {
                'total_memory_mb': total_memory,
                'available_memory_mb': available_memory,
                'memory_utilization': memory_util,
                'gpu_utilization': gpu_util
            },
            'cooldown_remaining': max(0, self.scaling_config['cooldown_period'] - (time.time() - self.last_scale_action))
        }