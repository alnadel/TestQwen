# Iron Frontier: Rails & Raiders - MVP

A Wild West train-management roguelite about trade, survival, route planning, and automated convoy combat.

## MVP Scope

- One procedural region (The Plains)
- 15–20 nodes
- Three station types (Town, Mining Camp, Railway Yard)
- Two locomotive types
- Six carriage types
- Eight goods
- Five crew roles
- Three contract types
- Three enemy types
- Twenty events
- Four combat doctrines
- Five emergency commands
- One rival company
- One regional boss
- One charter (Frontier Merchant)
- 45–75 minute run

## Core Loop

**Station → Prepare → Choose Route → Travel → Survive → Profit → Upgrade**

## Features Demonstrated

✓ Procedural railway map generation with branching paths
✓ Station phase with dynamic market trading
✓ Route planning with risk/reward decisions
✓ Resource management (coal, water, cargo capacity)
✓ Automated combat system with doctrine selection
✓ Random events during travel (storms, broken track, merchants)
✓ Contract system with rewards
✓ Crew management with stamina and morale
✓ Train configuration and damage tracking
✓ Company value and reputation system
✓ Roguelite run structure with victory/defeat conditions

## Quick Start

### Interactive Mode

Play the full game with manual controls:

```bash
cd iron_frontier
python main.py
```

### Demo Mode

Watch an automated demonstration of the gameplay loop:

```bash
cd iron_frontier
python demo.py
```

## Controls

### Interactive Mode
- **Number keys**: Select menu options
- **B/S**: Buy or Sell goods
- **Y/N**: Confirm actions

### Demo Mode
- Fully automated - no input required

## Tech Stack

- Python 3.x
- Pure standard library (no external dependencies)
- Text-based UI for MVP
- Dataclasses for game entities
- Modular system design (Market, Combat, Events)

## Game Systems

### Market System
Dynamic pricing based on station type and random fluctuations. Buy low, sell high!

### Combat System
Automated resolution based on:
- Train composition (guard cars, armor)
- Crew assignments and skills
- Combat doctrine (aggressive, defensive, balanced, retreat)
- Random factors

### Event System
Random encounters during travel including:
- Broken track (repair/detour/risk)
- Stranded passengers
- Merchant caravans
- Weather storms
- Resource deposits

### Train Management
- Locomotive attributes (pulling power, speed, efficiency)
- Carriage order matters (defense, fire spread, boarding)
- Cargo capacity and weight limits
- Damage and repairs

## Project Structure

```
iron_frontier/
├── main.py          # Main game engine and systems
├── demo.py          # Automated demonstration script
└── README.md        # This file
```

## Example Run

```
============================================================
IRON FRONTIER: RAILS & RAIDERS
============================================================

Starting new run with Frontier Merchant Charter...
Objective: Reach the final railhead with $2000+ company value

STATION: Startington (Town)
Turn 1 | Money: $500 | Coal: 100 | Water: 100
Damage: 0% | Company Value: $500

Options:
1. Trade Goods
2. Manage Train
3. View Crew
4. Accept Contracts
5. Depart
```

## License

MIT License - Built for educational/demo purposes
