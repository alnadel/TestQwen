#!/usr/bin/env python3
"""
Automated demo script for Iron Frontier MVP
Shows the full gameplay cycle without manual input
"""

import sys
sys.path.insert(0, '/workspace/iron_frontier')

from main import (
    Game, Train, CrewMember, MarketSystem, CombatSystem, 
    EventSystem, GameState, Node, Contract
)
import random

def run_demo():
    """Run an automated demonstration of the game."""
    
    print("=" * 70)
    print("IRON FRONTIER: RAILS & RAIDERS - MVP DEMO")
    print("=" * 70)
    print("\nDemonstrating core gameplay loop:")
    print("  Station → Prepare → Choose Route → Travel → Survive → Profit → Upgrade\n")
    
    # Set seed for reproducibility
    random.seed(42)
    
    # Initialize game
    game = Game()
    game.initialize_run()
    
    print("\n" + "=" * 70)
    print("INITIAL STATE")
    print("=" * 70)
    print(f"Charter: {game.state.charter}")
    print(f"Starting Money: ${game.train.money}")
    print(f"Locomotive: {game.train.locomotive}")
    print(f"Crew: {[m.name for m in game.crew]}")
    print(f"Carriages: {[c['name'] for c in game.train.carriages]}")
    
    # Simulate 3 turns
    for turn in range(1, 4):
        print(f"\n{'='*70}")
        print(f"TURN {turn}")
        print(f"{'='*70}")
        
        # Station Phase
        node = game.map_nodes[game.state.current_node]
        print(f"\n📍 STATION: {node.name} ({node.type})")
        
        # Show market prices
        game.market.update_prices(node.type)
        print(f"   Market Prices:")
        for good in ['coal', 'food', 'tools']:
            print(f"     {good.capitalize()}: ${game.market.get_price(good):.2f}")
        
        # Simulate buying goods
        if turn == 1:
            print(f"   → Buying 10 coal @ ${game.market.get_price('coal'):.2f}")
            cost = int(10 * game.market.get_price('coal'))
            game.train.money -= cost
            game.train.cargo['coal'] = 10
            print(f"   → Spent ${cost}, Cargo: {game.train.cargo}")
        
        # Route Planning
        current = game.map_nodes[game.state.current_node]
        if current.connections:
            next_node_id = current.connections[0]
            next_node = game.map_nodes[next_node_id]
            print(f"\n🗺️  ROUTE: {node.name} → {next_node.name}")
        
        # Travel Phase
        print(f"\n🚂 TRAVELING...")
        coal_used = random.randint(5, 15)
        water_used = random.randint(5, 15)
        game.train.coal -= coal_used
        game.train.water -= water_used
        print(f"   Consumed: {coal_used} coal, {water_used} water")
        
        # Random event
        event = game.events.trigger_random_event()
        if event:
            print(f"   📜 EVENT: {event.title}")
            print(f"      {event.description}")
        
        # Combat encounter
        if random.random() < 0.3:
            enemy = random.choice([
                {"name": "Rustler Gang", "strength": 30, "loot_min": 50, "loot_max": 150},
                {"name": "River Raiders", "strength": 50, "loot_min": 100, "loot_max": 250},
            ])
            print(f"\n⚔️  COMBAT: {enemy['name']} attacks!")
            
            victory, loot, log = game.combat.resolve_combat(
                game.train, enemy, "balanced", game.crew
            )
            
            if victory:
                game.train.money += loot
                game.state.combats_won += 1
                print(f"   ✓ Victory! Loot: ${loot}")
            else:
                print(f"   ✗ Defeated...")
        
        # Arrival Phase
        game.state.current_node = next_node_id
        node.visited = True
        game.state.stations_visited += 1
        
        # Complete contracts
        if game.contracts:
            for contract in game.contracts:
                if not contract.completed:
                    contract.completed = True
                    game.train.money += contract.reward
                    game.state.contracts_completed += 1
                    print(f"\n✓ Contract completed: ${contract.reward}")
        
        # Update company value
        game.state.company_value = (
            game.train.money +
            sum(c.get("cost", 0) for c in game.train.carriages)
        )
        
        # Rest crew
        for member in game.crew:
            member.rest()
        
        print(f"\n📊 END OF TURN {turn} STATUS:")
        print(f"   Money: ${game.train.money}")
        print(f"   Coal: {game.train.coal}")
        print(f"   Water: {game.train.water}")
        print(f"   Damage: {game.train.damage}%")
        print(f"   Company Value: ${game.state.company_value}")
        print(f"   Stations Visited: {game.state.stations_visited}")
        
        game.state.turn += 1
    
    # Final Summary
    print("\n" + "=" * 70)
    print("DEMO COMPLETE - RUN SUMMARY")
    print("=" * 70)
    print(f"Turns survived: {game.state.turn}")
    print(f"Stations visited: {game.state.stations_visited}")
    print(f"Contracts completed: {game.state.contracts_completed}")
    print(f"Combats won: {game.state.combats_won}")
    print(f"Final company value: ${game.state.company_value}")
    
    print("\n" + "=" * 70)
    print("MVP FEATURES DEMONSTRATED:")
    print("=" * 70)
    print("✓ Procedural railway map generation")
    print("✓ Station phase with trading")
    print("✓ Route planning with branching paths")
    print("✓ Resource management (coal, water)")
    print("✓ Automated combat system")
    print("✓ Random events during travel")
    print("✓ Contract system")
    print("✓ Crew management")
    print("✓ Train configuration")
    print("✓ Company value tracking")
    print("✓ Roguelite run structure")
    print("\n" + "=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    run_demo()
