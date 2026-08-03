"""
Iron Frontier: Rails & Raiders - MVP
A Wild West train-management roguelite

Core Loop: Buy → Prepare → Choose Route → Travel → Survive → Profit → Upgrade
"""

import random
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

GOODS = {
    "coal": {"base_price": 15, "category": "fuel"},
    "wood": {"base_price": 10, "category": "fuel"},
    "water": {"base_price": 5, "category": "consumable"},
    "food": {"base_price": 20, "category": "consumable"},
    "cattle": {"base_price": 50, "category": "livestock"},
    "ore": {"base_price": 40, "category": "raw"},
    "tools": {"base_price": 35, "category": "manufactured"},
    "gold": {"base_price": 100, "category": "valuable"},
}

STATION_TYPES = ["town", "mining_camp", "railway_yard"]

LOCOMOTIVES = {
    "pioneer": {"name": "Pioneer", "pulling_power": 500, "speed": 60, "fuel_efficiency": 1.0, "cost": 500},
    "ironhorse": {"name": "Iron Horse", "pulling_power": 800, "speed": 45, "fuel_efficiency": 0.8, "cost": 1000},
}

CARRIAGES = {
    "boxcar": {"name": "Boxcar", "capacity": 100, "weight": 50, "cost": 200, "defense": 5},
    "flatbed": {"name": "Flatbed", "capacity": 150, "weight": 40, "cost": 150, "defense": 2},
    "guard_car": {"name": "Guard Car", "capacity": 0, "weight": 60, "cost": 400, "defense": 20, "guards": 3},
    "passenger_car": {"name": "Passenger Car", "capacity": 50, "weight": 70, "cost": 350, "defense": 8},
    "workshop": {"name": "Workshop", "capacity": 20, "weight": 80, "cost": 500, "repair_bonus": 0.5},
    "caboose": {"name": "Caboose", "capacity": 10, "weight": 30, "cost": 150, "visibility": 10},
}

CREW_ROLES = ["engineer", "fireman", "conductor", "mechanic", "guard"]

ENEMY_TYPES = [
    {"name": "Rustler Gang", "strength": 30, "loot_min": 50, "loot_max": 150},
    {"name": "River Raiders", "strength": 50, "loot_min": 100, "loot_max": 250},
    {"name": "Outlaw Convoy", "strength": 80, "loot_min": 200, "loot_max": 400},
]

COMBAT_DOCTRINES = [
    "aggressive",  # Higher damage, higher risk
    "defensive",   # Lower damage, lower risk
    "balanced",    # Standard approach
    "retreat",     # Try to escape with minimal losses
]

EMERGENCY_COMMANDS = [
    "full_steam",      # Increase speed, higher fuel use
    "emergency_brake", # Stop quickly, risk damage
    "detach_carriage", # Sacrifice a carriage to escape
    "return_fire",     # Focus on defense
    "call_bluff",      # Risky intimidation attempt
]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CrewMember:
    name: str
    role: str
    skill: int
    stamina: int = 100
    morale: int = 100
    
    def rest(self):
        self.stamina = min(100, self.stamina + 20)
        self.morale = min(100, self.morale + 10)


@dataclass
class Contract:
    id: str
    type: str  # "delivery", "transport", "escort"
    description: str
    reward: int
    deadline: int  # turns remaining
    completed: bool = False


@dataclass
class Node:
    id: str
    type: str
    name: str
    connections: List[str] = field(default_factory=list)
    goods_available: Dict[str, int] = field(default_factory=dict)
    goods_demand: Dict[str, int] = field(default_factory=dict)
    visited: bool = False


@dataclass
class Event:
    id: str
    title: str
    description: str
    choices: List[Dict]  # Each choice has text, effect function


# ============================================================================
# GAME SYSTEMS
# ============================================================================

class MarketSystem:
    """Handles buying and selling of goods with dynamic pricing."""
    
    def __init__(self):
        self.current_prices: Dict[str, float] = {}
        self.price_modifiers: Dict[str, float] = {}
    
    def update_prices(self, station_type: str):
        """Update market prices based on station type and random factors."""
        for good, info in GOODS.items():
            base = info["base_price"]
            
            # Station type modifier
            if station_type == "mining_camp":
                if good in ["tools", "food"]:
                    self.price_modifiers[good] = 1.3
                elif good in ["ore", "coal"]:
                    self.price_modifiers[good] = 0.7
            elif station_type == "town":
                if good in ["food", "cattle"]:
                    self.price_modifiers[good] = 1.2
                elif good in ["tools"]:
                    self.price_modifiers[good] = 0.9
            elif station_type == "railway_yard":
                if good in ["coal", "wood"]:
                    self.price_modifiers[good] = 1.1
            
            # Random fluctuation (±20%)
            fluctuation = random.uniform(0.8, 1.2)
            
            self.current_prices[good] = base * self.price_modifiers.get(good, 1.0) * fluctuation
    
    def get_price(self, good: str) -> float:
        return self.current_prices.get(good, GOODS[good]["base_price"])


class CombatSystem:
    """Automated combat resolution based on train composition and doctrine."""
    
    def __init__(self):
        self.combat_log: List[str] = []
    
    def resolve_combat(self, player_train: 'Train', enemy: Dict, 
                      doctrine: str, crew: List[CrewMember]) -> Tuple[bool, int, List[str]]:
        """
        Resolve automated combat.
        Returns: (victory, loot_amount, combat_log)
        """
        self.combat_log = []
        
        # Calculate player strength
        player_strength = 0
        
        # Add guard cars
        for carriage in player_train.carriages:
            if carriage.get("guards", 0) > 0:
                player_strength += carriage["defense"] * carriage["guards"]
            player_strength += carriage.get("defense", 0)
        
        # Add crew bonus
        for member in crew:
            if member.role == "guard":
                player_strength += member.skill * 2
            elif member.role == "engineer":
                player_strength += member.skill // 2
        
        # Apply doctrine modifier
        doctrine_multipliers = {
            "aggressive": 1.3,
            "defensive": 1.1,
            "balanced": 1.0,
            "retreat": 0.7,
        }
        player_strength *= doctrine_multipliers.get(doctrine, 1.0)
        
        # Add randomness
        player_roll = random.uniform(0.8, 1.2)
        enemy_roll = random.uniform(0.8, 1.2)
        
        final_player = player_strength * player_roll
        final_enemy = enemy["strength"] * enemy_roll
        
        self.combat_log.append(f"Combat started against {enemy['name']}!")
        self.combat_log.append(f"Player strength: {final_player:.1f} vs Enemy: {final_enemy:.1f}")
        
        if final_player >= final_enemy:
            # Victory
            loot = random.randint(enemy["loot_min"], enemy["loot_max"])
            self.combat_log.append(f"Victory! Looted ${loot}")
            
            # Apply damage based on how close the fight was
            damage_ratio = final_enemy / final_player if final_player > 0 else 1
            if damage_ratio > 0.8:
                self.combat_log.append("Heavy damage sustained!")
                player_train.damage += 20
            elif damage_ratio > 0.5:
                self.combat_log.append("Moderate damage sustained.")
                player_train.damage += 10
            else:
                self.combat_log.append("Minor damage only.")
                player_train.damage += 5
            
            return True, loot, self.combat_log
        else:
            # Defeat - still might escape with some cargo
            self.combat_log.append("Defeated! Forced to retreat.")
            player_train.damage += 30
            
            # Lose some cargo
            if player_train.cargo:
                lost_good = random.choice(list(player_train.cargo.keys()))
                lost_amount = min(player_train.cargo[lost_good], 20)
                player_train.cargo[lost_good] -= lost_amount
                self.combat_log.append(f"Lost {lost_amount} units of {lost_good}")
            
            return False, 0, self.combat_log


class EventSystem:
    """Random events during travel."""
    
    def __init__(self):
        self.events = self._create_events()
    
    def _create_events(self) -> List[Event]:
        return [
            Event(
                id="broken_track",
                title="Broken Track Ahead",
                description="You discover a section of damaged track blocking the route.",
                choices=[
                    {"text": "Repair it (takes time, costs resources)", "effect": "repair"},
                    {"text": "Go around (longer route, more fuel)", "effect": "detour"},
                    {"text": "Risk it at high speed (dangerous)", "effect": "risk"},
                ]
            ),
            Event(
                id="stranded_passengers",
                title="Stranded Passengers",
                description="A group of travelers waves you down from the platform.",
                choices=[
                    {"text": "Take them aboard (earn money, slower)", "effect": "take_passengers"},
                    {"text": "Keep going (no change)", "effect": "ignore"},
                ]
            ),
            Event(
                id="merchant_caravan",
                title="Merchant Caravan",
                description="A traveling merchant offers to trade goods.",
                choices=[
                    {"text": "Buy supplies (discount)", "effect": "buy_discount"},
                    {"text": "Sell cargo (good price)", "effect": "sell_premium"},
                    {"text": "Decline politely", "effect": "decline"},
                ]
            ),
            Event(
                id="weather_storm",
                title="Approaching Storm",
                description="Dark clouds gather on the horizon.",
                choices=[
                    {"text": "Push through (risk damage)", "effect": "push_through"},
                    {"text": "Wait it out (lose time)", "effect": "wait"},
                    {"text": "Seek shelter (find station)", "effect": "shelter"},
                ]
            ),
            Event(
                id="coal_deposit",
                title="Abandoned Coal Deposit",
                description="You spot an accessible coal seam near the tracks.",
                choices=[
                    {"text": "Mine some coal (takes time)", "effect": "mine_coal"},
                    {"text": "Keep moving", "effect": "ignore"},
                ]
            ),
        ]
    
    def trigger_random_event(self) -> Optional[Event]:
        """30% chance of random event."""
        if random.random() < 0.3:
            return random.choice(self.events)
        return None


# ============================================================================
# CORE GAME OBJECTS
# ============================================================================

@dataclass
class Train:
    locomotive: str
    carriages: List[Dict] = field(default_factory=list)
    cargo: Dict[str, int] = field(default_factory=dict)
    coal: int = 100
    water: int = 100
    damage: int = 0
    money: int = 500
    
    @property
    def total_weight(self) -> int:
        weight = LOCOMOTIVES[self.locomotive]["pulling_power"]
        for carriage in self.carriages:
            weight += carriage.get("weight", 0)
        return weight
    
    @property
    def total_capacity(self) -> int:
        capacity = 0
        for carriage in self.carriages:
            capacity += carriage.get("capacity", 0)
        return capacity
    
    @property
    def current_cargo(self) -> int:
        return sum(self.cargo.values())
    
    @property
    def available_capacity(self) -> int:
        return self.total_capacity - self.current_cargo
    
    def can_pull(self) -> bool:
        """Check if locomotive can pull current weight."""
        loco = LOCOMOTIVES[self.locomotive]
        total_weight = sum(c.get("weight", 0) for c in self.carriages)
        return total_weight <= loco["pulling_power"]


@dataclass
class GameState:
    turn: int = 1
    region: str = "The Plains"
    current_node: str = "start"
    charter: str = "Frontier Merchant"
    company_value: int = 500
    reputation: int = 50
    
    # Run tracking
    stations_visited: int = 0
    contracts_completed: int = 0
    combats_won: int = 0
    total_profit: int = 0


# ============================================================================
# MAIN GAME ENGINE
# ============================================================================

class Game:
    """Main game engine managing the core loop."""
    
    def __init__(self):
        self.state = GameState()
        self.train = Train(locomotive="pioneer")
        self.crew: List[CrewMember] = []
        self.contracts: List[Contract] = []
        self.map_nodes: Dict[str, Node] = {}
        
        self.market = MarketSystem()
        self.combat = CombatSystem()
        self.events = EventSystem()
        
        self.running = True
        self.game_over = False
        self.victory = False
    
    def initialize_run(self):
        """Set up a new run."""
        print("=" * 60)
        print("IRON FRONTIER: RAILS & RAIDERS")
        print("=" * 60)
        print("\nStarting new run with Frontier Merchant Charter...")
        print("Objective: Reach the final railhead with $2000+ company value\n")
        
        # Generate procedural map
        self._generate_map()
        
        # Starting crew
        self.crew = [
            CrewMember(name="Jake", role="engineer", skill=70),
            CrewMember(name="Mary", role="fireman", skill=60),
            CrewMember(name="Tom", role="conductor", skill=65),
        ]
        
        # Starting train configuration
        self.train.carriages = [
            {"name": "Tender", "weight": 40, "capacity": 0},
            {"name": "Boxcar", "weight": 50, "capacity": 100},
        ]
    
    def _generate_map(self):
        """Generate procedural railway map for The Plains."""
        node_names = [
            "Startington", "Greenfield", "Copper Ridge", "Oakhaven",
            "Silver Creek", "Dusty Plains", "Rockford", "Meadowbrook",
            "Coalport", "Harvest Town", "Iron Junction", "Final Railhead"
        ]
        
        for i, name in enumerate(node_names):
            node_type = "town"
            if i % 3 == 0 and i > 0:
                node_type = "mining_camp"
            elif i == len(node_names) - 1:
                node_type = "railway_yard"
            
            node = Node(
                id=f"node_{i}",
                type=node_type,
                name=name,
                connections=[]
            )
            
            # Connect to next nodes (forward progression with branching)
            if i < len(node_names) - 1:
                # Always connect to next node
                node.connections.append(f"node_{i+1}")
                
                # Add branch to alternate path (creates interesting choices)
                if i < len(node_names) - 2 and random.random() < 0.4:
                    node.connections.append(f"node_{i+2}")
            
            self.map_nodes[f"node_{i}"] = node
        
        # Set start position
        self.state.current_node = "node_0"
    
    def station_phase(self):
        """Handle station activities."""
        node = self.map_nodes[self.state.current_node]
        node.visited = True
        self.state.stations_visited += 1
        
        print(f"\n{'='*60}")
        print(f"STATION: {node.name} ({node.type.replace('_', ' ').title()})")
        print(f"{'='*60}")
        
        # Update market
        self.market.update_prices(node.type)
        
        while True:
            print(f"\nTurn {self.state.turn} | Money: ${self.train.money} | Coal: {self.train.coal} | Water: {self.train.water}")
            print(f"Damage: {self.train.damage}% | Company Value: ${self.state.company_value}")
            print("\nOptions:")
            print("1. Trade Goods")
            print("2. Manage Train")
            print("3. View Crew")
            print("4. Accept Contracts")
            print("5. Depart")
            
            choice = input("\nChoose action (1-5): ").strip()
            
            if choice == "1":
                self._trade_goods(node)
            elif choice == "2":
                self._manage_train()
            elif choice == "3":
                self._view_crew()
            elif choice == "4":
                self._accept_contracts()
            elif choice == "5":
                break
    
    def _trade_goods(self, node: Node):
        """Handle trading at station."""
        print("\n--- MARKET ---")
        print("Goods Available:")
        for good, price in self.market.current_prices.items():
            print(f"  {good.capitalize()}: ${price:.2f}")
        
        print("\nYour Cargo:")
        if not self.train.cargo:
            print("  (empty)")
        else:
            for good, amount in self.train.cargo.items():
                print(f"  {good.capitalize()}: {amount}")
        
        action = input("\n(B)uy, (S)ell, or (C)ancel: ").strip().upper()
        
        if action == "B":
            good = input("Which good? ").strip().lower()
            if good in GOODS:
                try:
                    amount = int(input("How many units? ").strip())
                    cost = amount * self.market.get_price(good)
                    if cost <= self.train.money:
                        if self.train.available_capacity >= amount:
                            self.train.money -= cost
                            self.train.cargo[good] = self.train.cargo.get(good, 0) + amount
                            print(f"Bought {amount} {good} for ${cost}")
                        else:
                            print("Not enough cargo space!")
                    else:
                        print("Not enough money!")
                except ValueError:
                    print("Invalid amount.")
        
        elif action == "S":
            if self.train.cargo:
                good = input("Which good? ").strip().lower()
                if good in self.train.cargo:
                    try:
                        amount = int(input("How many units? ").strip())
                        amount = min(amount, self.train.cargo[good])
                        if amount > 0:
                            revenue = amount * self.market.get_price(good)
                            self.train.money += revenue
                            self.train.cargo[good] -= amount
                            if self.train.cargo[good] <= 0:
                                del self.train.cargo[good]
                            print(f"Sold {amount} {good} for ${revenue}")
                            self.state.total_profit += revenue
                    except ValueError:
                        print("Invalid amount.")
    
    def _manage_train(self):
        """View and manage train configuration."""
        print("\n--- TRAIN STATUS ---")
        print(f"Locomotive: {LOCOMOTIVES[self.train.locomotive]['name']}")
        print(f"Carriages: {len(self.train.carriages)}")
        for i, carriage in enumerate(self.train.carriages):
            print(f"  [{i}] {carriage.get('name', 'Unknown')}")
        print(f"Cargo: {self.train.current_cargo}/{self.train.total_capacity}")
        print(f"Coal: {self.train.coal}/100")
        print(f"Water: {self.train.water}/100")
        print(f"Damage: {self.train.damage}%")
        
        # Simple repair option
        if self.train.damage > 0:
            repair_cost = self.train.damage * 5
            print(f"\nRepair train for ${repair_cost}?")
            if input("(Y/N): ").strip().upper() == "Y":
                if self.train.money >= repair_cost:
                    self.train.money -= repair_cost
                    self.train.damage = 0
                    print("Train repaired!")
                else:
                    print("Not enough money!")
    
    def _view_crew(self):
        """View crew status."""
        print("\n--- CREW ---")
        for member in self.crew:
            print(f"{member.name} ({member.role}): Skill={member.skill}, Stamina={member.stamina}, Morale={member.morale}")
    
    def _accept_contracts(self):
        """View and accept contracts."""
        print("\n--- AVAILABLE CONTRACTS ---")
        # Generate simple contracts
        contract_types = ["delivery", "transport", "escort"]
        for i, ctype in enumerate(contract_types[:2]):
            reward = random.randint(100, 300)
            print(f"[{i+1}] {ctype.title()} - Reward: ${reward}")
        
        choice = input("Accept contract (number) or (C)ancel: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= 2:
            ctype = contract_types[int(choice) - 1]
            reward = random.randint(100, 300)
            contract = Contract(
                id=f"contract_{self.state.turn}",
                type=ctype,
                description=f"{ctype.title()} contract",
                reward=reward,
                deadline=self.state.turn + 5
            )
            self.contracts.append(contract)
            print(f"Accepted {ctype} contract for ${reward}")
    
    def route_planning_phase(self):
        """Choose next destination."""
        current = self.map_nodes[self.state.current_node]
        
        print(f"\n{'='*60}")
        print("ROUTE PLANNING")
        print(f"{'='*60}")
        print(f"Current Location: {current.name}")
        print("\nAvailable Routes:")
        
        destinations = current.connections
        for i, dest_id in enumerate(destinations):
            dest = self.map_nodes[dest_id]
            status = "✓" if dest.visited else " "
            print(f"  [{i+1}] {status} {dest.name} ({dest.type.replace('_', ' ')})")
        
        choice = input("\nChoose destination (number): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(destinations):
            return destinations[int(choice) - 1]
        return destinations[0]  # Default to first
    
    def travel_phase(self, destination_id: str):
        """Handle travel between nodes."""
        print(f"\n{'='*60}")
        print("TRAVELING...")
        print(f"{'='*60}")
        
        # Consume resources
        coal_used = random.randint(5, 15)
        water_used = random.randint(5, 15)
        
        self.train.coal -= coal_used
        self.train.water -= water_used
        
        print(f"Consumed: {coal_used} coal, {water_used} water")
        
        # Check resource depletion
        if self.train.coal <= 0 or self.train.water <= 0:
            print("\nWARNING: Running low on resources!")
            if self.train.coal <= 0:
                print("Train is out of coal!")
            if self.train.water <= 0:
                print("Train is out of water!")
        
        # Random events
        event = self.events.trigger_random_event()
        if event:
            self._handle_event(event)
        
        # Combat encounter (25% chance)
        if random.random() < 0.25:
            enemy = random.choice(ENEMY_TYPES)
            print(f"\n⚠️  AMBUSH! {enemy['name']} approaching!")
            
            print("\nCombat Doctrines:")
            for i, doctrine in enumerate(COMBAT_DOCTRINES):
                print(f"  [{i+1}] {doctrine.title()}")
            
            choice = input("Choose doctrine (1-4): ").strip()
            doctrine_idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= 4 else 2
            doctrine = COMBAT_DOCTRINES[doctrine_idx]
            
            victory, loot, log = self.combat.resolve_combat(
                self.train, enemy, doctrine, self.crew
            )
            
            for line in log:
                print(f"  {line}")
            
            if victory:
                self.train.money += loot
                self.state.combats_won += 1
                print(f"Victory! Gained ${loot}")
            else:
                print("Defeated...")
        
        self.state.turn += 1
    
    def _handle_event(self, event: Event):
        """Handle a random event."""
        print(f"\n📜 EVENT: {event.title}")
        print(event.description)
        
        for i, choice in enumerate(event.choices):
            print(f"  [{i+1}] {choice['text']}")
        
        selection = input("Choose (number): ").strip()
        if selection.isdigit() and 1 <= int(selection) <= len(event.choices):
            effect = event.choices[int(selection) - 1]["effect"]
            
            # Apply effects
            if effect == "repair":
                self.train.damage = max(0, self.train.damage - 10)
                self.train.coal -= 5
                print("Track repaired. Used 5 coal.")
            elif effect == "detour":
                self.train.coal -= 10
                print("Took detour. Used extra 10 coal.")
            elif effect == "take_passengers":
                earnings = random.randint(30, 80)
                self.train.money += earnings
                print(f"Took passengers aboard. Earned ${earnings}.")
            elif effect == "buy_discount":
                print("Bought supplies at 20% discount.")
                self.train.coal = min(100, self.train.coal + 20)
                self.train.water = min(100, self.train.water + 20)
                self.train.money -= 50
            elif effect == "mine_coal":
                self.train.coal = min(100, self.train.coal + 15)
                print("Mined 15 coal.")
    
    def arrival_phase(self, destination_id: str):
        """Handle arrival at destination."""
        node = self.map_nodes[destination_id]
        self.state.current_node = destination_id
        
        # Complete contracts
        for contract in self.contracts:
            if not contract.completed:
                contract.completed = True
                self.train.money += contract.reward
                self.state.contracts_completed += 1
                print(f"\n✓ Contract completed! Earned ${contract.reward}")
        
        # Update company value
        self.state.company_value = (
            self.train.money +
            sum(c.get("cost", 0) for c in self.train.carriages) +
            LOCOMOTIVES[self.train.locomotive]["cost"]
        )
        
        # Rest crew
        for member in self.crew:
            member.rest()
        
        # Check for victory/defeat
        self._check_game_state()
    
    def _check_game_state(self):
        """Check win/loss conditions."""
        # Victory condition
        if "node_11" in self.state.current_node:  # Final railhead
            if self.state.company_value >= 2000:
                self.victory = True
                self.game_over = True
                print("\n🎉 VICTORY! You reached the Final Railhead with sufficient funds!")
                return
        
        # Defeat conditions
        if self.train.money < 0:
            self.game_over = True
            print("\n💀 GAME OVER: Bankruptcy!")
            return
        
        if self.train.damage >= 100:
            self.game_over = True
            print("\n💀 GAME OVER: Train destroyed!")
            return
        
        if self.train.coal <= 0 and self.train.water <= 0:
            self.game_over = True
            print("\n💀 GAME OVER: Stranded without resources!")
            return
    
    def run(self):
        """Main game loop."""
        self.initialize_run()
        
        while self.running and not self.game_over:
            # Station phase
            self.station_phase()
            
            if self.game_over:
                break
            
            # Route planning
            next_node = self.route_planning_phase()
            
            # Travel
            self.travel_phase(next_node)
            
            if self.game_over:
                break
            
            # Arrival
            self.arrival_phase(next_node)
        
        # End game summary
        self._end_game()
    
    def _end_game(self):
        """Display end game summary."""
        print("\n" + "=" * 60)
        print("RUN SUMMARY")
        print("=" * 60)
        print(f"Turns survived: {self.state.turn}")
        print(f"Stations visited: {self.state.stations_visited}")
        print(f"Contracts completed: {self.state.contracts_completed}")
        print(f"Combats won: {self.state.combats_won}")
        print(f"Total profit: ${self.state.total_profit}")
        print(f"Final company value: ${self.state.company_value}")
        
        if self.victory:
            print("\n🏆 CONGRATULATIONS! You completed your charter!")
        else:
            print("\n☠️ Better luck next time, partner...")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    game = Game()
    game.run()
