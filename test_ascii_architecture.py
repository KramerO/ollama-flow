#!/usr/bin/env python3
"""
Test Script for ASCII Architecture Visualization
Demonstrates all three architecture types with ASCII art
"""

def generate_ascii_architecture(architecture: str) -> str:
    """Generate ASCII art diagram for the given architecture"""
    
    if architecture == 'HIERARCHICAL':
        return """
                    ┌─────────────┐
                    │    QUEEN    │
                    │   (Master)  │
                    └──────┬──────┘
                           │
               ┌───────────┼───────────┐
               │                       │
        ┌──────▼──────┐        ┌──────▼──────┐
        │  SUB-QUEEN  │        │  SUB-QUEEN  │
        │     (A)     │        │     (B)     │
        └──────┬──────┘        └──────┬──────┘
               │                       │
         ┌─────┼─────┐           ┌─────┼─────┐
         │           │           │           │
    ┌────▼───┐  ┌────▼───┐  ┌────▼───┐  ┌────▼───┐
    │ DRONE  │  │ DRONE  │  │ DRONE  │  │ DRONE  │
    │   #1   │  │   #2   │  │   #3   │  │   #4   │
    │analyst │  │data-sci│  │architect│  │developer│
    └────────┘  └────────┘  └────────┘  └────────┘
        """
    
    elif architecture == 'CENTRALIZED':
        return """
                    ┌─────────────┐
                    │    QUEEN    │
                    │ (Centralized)│
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            │         ┌────┼────┐         │
            │         │         │         │
       ┌────▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼────┐
       │ DRONE  │ │ DRONE │ │ DRONE │ │ DRONE  │
       │   #1   │ │   #2  │ │   #3  │ │   #4   │
       │analyst │ │data-sci│ │architect│ │developer│
       └────────┘ └───────┘ └───────┘ └────────┘
               ▲       ▲       ▲       ▲
               │       │       │       │
               └───────┼───────┼───────┘
                       │       │
                   Direct Communication
        """
    
    elif architecture == 'FULLY_CONNECTED':
        return """
           ┌─────────┐ ◄──────────► ┌─────────┐
           │ AGENT 1 │               │ AGENT 2 │
           │ analyst │ ◄─────┐ ┌────► │data-sci │
           └─────────┘       │ │     └─────────┘
                 ▲           │ │           ▲
                 │           │ │           │
                 ▼           │ │           ▼
           ┌─────────┐       │ │     ┌─────────┐
           │ AGENT 4 │ ◄─────┘ └────► │ AGENT 3 │
           │developer│               │architect│
           └─────────┘ ◄──────────► └─────────┘
           
           ═══ Peer-to-Peer Network ═══
           All agents communicate directly
        """
    
    else:
        return """
                ┌─────────────┐
                │   UNKNOWN   │
                │ ARCHITECTURE│
                └─────────────┘
        """

def main():
    """Test all architecture visualizations"""
    print("🏗️ OLLAMA FLOW ARCHITECTURE VISUALIZATIONS")
    print("=" * 60)
    
    architectures = ['HIERARCHICAL', 'CENTRALIZED', 'FULLY_CONNECTED', 'UNKNOWN']
    
    for arch in architectures:
        print(f"\n📐 {arch} ARCHITECTURE:")
        print("-" * 40)
        ascii_art = generate_ascii_architecture(arch)
        print(ascii_art)
        
        # Architecture description
        if arch == 'HIERARCHICAL':
            print("📋 Description: Master Queen coordinates Sub-Queens, who manage specialized Drone agents")
            print("✅ Best for: Complex tasks requiring specialized coordination")
            
        elif arch == 'CENTRALIZED':
            print("📋 Description: Single Queen directly manages all Drone agents")
            print("✅ Best for: Simple tasks with direct coordination needs")
            
        elif arch == 'FULLY_CONNECTED':
            print("📋 Description: All agents communicate directly with each other")
            print("✅ Best for: Collaborative tasks requiring peer-to-peer communication")
        
        print()
        input("Press Enter to continue to next architecture...")

if __name__ == "__main__":
    main()