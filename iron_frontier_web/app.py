"""
Iron Frontier: Rails & Raiders - Web Application
Flask backend exposing game logic via REST API
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import random
import json
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

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

COMBAT_DOCTRINES = ["aggressive", "defensive", "balanced", "retreat"]

EVENTS_DATA = [
    {
        "id": "broken_track",
        "title": "Broken Track Ahead",
        "description": "You discover a section of damaged track blocking the route.",
        "choices": [
            {"text": "Repair it (takes time, costs resources)", "effect": "repair"},
            {"text": "Go around (longer route, more fuel)", "effect": "detour"},
            {"text": "Risk it at high speed (dangerous)", "effect": "risk"},
        ]
    },
    {
        "id": "stranded_passengers",
        "title": "Stranded Passengers",
        "description": "A group of travelers waves you down from the platform.",
        "choices": [
            {"text": "Take them aboard (earn money, slower)", "effect": "take_passengers"},
            {"text": "Keep going (no change)", "effect": "ignore"},
        ]
    },
    {
        "id": "merchant_caravan",
        "title": "Merchant Caravan",
        "description": "A traveling merchant offers to trade goods.",
        "choices": [
            {"text": "Buy supplies (discount)", "effect": "buy_discount"},
            {"text": "Sell cargo (good price)", "effect": "sell_premium"},
            {"text": "Decline politely", "effect": "decline"},
        ]
    },
    {
        "id": "weather_storm",
        "title": "Approaching Storm",
        "description": "Dark clouds gather on the horizon.",
        "choices": [
            {"text": "Push through (risk damage)", "effect": "push_through"},
            {"text": "Wait it out (lose time)", "effect": "wait"},
            {"text": "Seek shelter (find station)", "effect": "shelter"},
        ]
    },
    {
        "id": "coal_deposit",
        "title": "Abandoned Coal Deposit",
        "description": "You spot an accessible coal seam near the tracks.",
        "choices": [
            {"text": "Mine some coal (takes time)", "effect": "mine_coal"},
            {"text": "Keep moving", "effect": "ignore"},
        ]
    },
]


# ============================================================================
# GAME STATE MANAGEMENT
# ============================================================================

class GameSession:
    """Manages a single game session."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Initialize/reset game state."""
        self.turn = 1
        self.region = "The Plains"
        self.current_node_id = "node_0"
        self.charter = "Frontier Merchant"
        self.company_value = 500
        self.reputation = 50
        
        # Run tracking
        self.stations_visited = 0
        self.contracts_completed = 0
        self.combats_won = 0
        self.total_profit = 0
        
        # Train
        self.train = {
            "locomotive": "pioneer",
            "carriages": [
                {"name": "Tender", "weight": 40, "capacity": 0},
                {"name": "Boxcar", "weight": 50, "capacity": 100},
            ],
            "cargo": {},
            "coal": 100,
            "water": 100,
            "damage": 0,
            "money": 500,
        }
        
        # Crew
        self.crew = [
            {"name": "Jake", "role": "engineer", "skill": 70, "stamina": 100, "morale": 100},
            {"name": "Mary", "role": "fireman", "skill": 60, "stamina": 100, "morale": 100},
            {"name": "Tom", "role": "conductor", "skill": 65, "stamina": 100, "morale": 100},
        ]
        
        # Contracts
        self.contracts = []
        
        # Map
        self.map_nodes = {}
        self._generate_map()
        
        # Market
        self.current_prices = {}
        self._update_market()
        
        # Game state flags
        self.game_over = False
        self.victory = False
        self.phase = "station"  # station, route, travel, arrival
        self.pending_event = None
        self.pending_combat = None
        self.travel_log = []
    
    def _generate_map(self):
        """Generate procedural railway map."""
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
            
            node = {
                "id": f"node_{i}",
                "type": node_type,
                "name": name,
                "connections": [],
                "goods_available": {},
                "goods_demand": {},
                "visited": i == 0,
            }
            
            # Connect to next nodes
            if i < len(node_names) - 1:
                node["connections"].append(f"node_{i+1}")
                if i < len(node_names) - 2 and random.random() < 0.4:
                    node["connections"].append(f"node_{i+2}")
            
            self.map_nodes[f"node_{i}"] = node
    
    def _update_market(self):
        """Update market prices based on current station."""
        node = self.map_nodes.get(self.current_node_id, {})
        station_type = node.get("type", "town")
        
        for good, info in GOODS.items():
            base = info["base_price"]
            modifier = 1.0
            
            if station_type == "mining_camp":
                if good in ["tools", "food"]:
                    modifier = 1.3
                elif good in ["ore", "coal"]:
                    modifier = 0.7
            elif station_type == "town":
                if good in ["food", "cattle"]:
                    modifier = 1.2
                elif good in ["tools"]:
                    modifier = 0.9
            elif station_type == "railway_yard":
                if good in ["coal", "wood"]:
                    modifier = 1.1
            
            fluctuation = random.uniform(0.8, 1.2)
            self.current_prices[good] = round(base * modifier * fluctuation, 2)
    
    def get_total_capacity(self) -> int:
        """Calculate total cargo capacity."""
        return sum(c.get("capacity", 0) for c in self.train["carriages"])
    
    def get_current_cargo(self) -> int:
        """Calculate current cargo amount."""
        return sum(self.train["cargo"].values())
    
    def get_available_capacity(self) -> int:
        """Calculate available cargo space."""
        return self.get_total_capacity() - self.get_current_cargo()
    
    def update_company_value(self):
        """Update company value based on assets."""
        self.company_value = (
            self.train["money"] +
            sum(c.get("cost", 200) for c in self.train["carriages"]) +
            LOCOMOTIVES[self.train["locomotive"]]["cost"]
        )
    
    def check_game_state(self) -> Dict:
        """Check win/loss conditions."""
        result = {"game_over": False, "victory": False, "reason": ""}
        
        # Victory condition
        if self.current_node_id == "node_11":
            if self.company_value >= 2000:
                result["game_over"] = True
                result["victory"] = True
                result["reason"] = "Reached Final Railhead with sufficient funds!"
                self.game_over = True
                self.victory = True
                return result
        
        # Defeat conditions
        if self.train["money"] < 0:
            result["game_over"] = True
            result["reason"] = "Bankruptcy!"
            self.game_over = True
        elif self.train["damage"] >= 100:
            result["game_over"] = True
            result["reason"] = "Train destroyed!"
            self.game_over = True
        elif self.train["coal"] <= 0 and self.train["water"] <= 0:
            result["game_over"] = True
            result["reason"] = "Stranded without resources!"
            self.game_over = True
        
        return result


# Global game sessions (in production, use proper session management)
game_sessions: Dict[str, GameSession] = {}


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main game page."""
    return render_template('index.html')


@app.route('/api/game/new', methods=['POST'])
def new_game():
    """Start a new game session."""
    session_id = f"session_{random.randint(1000, 9999)}"
    game = GameSession()
    game_sessions[session_id] = game
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "state": get_game_state(game)
    })


@app.route('/api/game/<session_id>/state', methods=['GET'])
def get_state(session_id):
    """Get current game state."""
    if session_id not in game_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    game = game_sessions[session_id]
    return jsonify(get_game_state(game))


def get_game_state(game: GameSession) -> Dict:
    """Convert game state to JSON-serializable dict."""
    current_node = game.map_nodes.get(game.current_node_id, {})
    
    return {
        "turn": game.turn,
        "region": game.region,
        "charter": game.charter,
        "company_value": game.company_value,
        "reputation": game.reputation,
        "phase": game.phase,
        "game_over": game.game_over,
        "victory": game.victory,
        "stats": {
            "stations_visited": game.stations_visited,
            "contracts_completed": game.contracts_completed,
            "combats_won": game.combats_won,
            "total_profit": game.total_profit,
        },
        "train": {
            **game.train,
            "total_capacity": game.get_total_capacity(),
            "current_cargo": game.get_current_cargo(),
            "available_capacity": game.get_available_capacity(),
        },
        "crew": game.crew,
        "contracts": game.contracts,
        "current_node": current_node,
        "available_destinations": [
            game.map_nodes[nid] 
            for nid in current_node.get("connections", [])
        ] if current_node else [],
        "market_prices": game.current_prices,
        "pending_event": game.pending_event,
        "pending_combat": game.pending_combat,
        "travel_log": game.travel_log,
    }


@app.route('/api/game/<session_id>/trade', methods=['POST'])
def trade(session_id):
    """Handle buying/selling goods."""
    if session_id not in game_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    game = game_sessions[session_id]
    data = request.json
    
    action = data.get("action")  # "buy" or "sell"
    good = data.get("good")
    amount = data.get("amount", 1)
    
    if good not in GOODS:
        return jsonify({"error": "Invalid good"}), 400
    
    price = game.current_prices.get(good, GOODS[good]["base_price"])
    
    if action == "buy":
        cost = amount * price
        if cost > game.train["money"]:
            return jsonify({"error": "Not enough money", "cost": cost}), 400
        if amount > game.get_available_capacity():
            return jsonify({"error": "Not enough cargo space"}), 400
        
        game.train["money"] -= cost
        game.train["cargo"][good] = game.train["cargo"].get(good, 0) + amount
        
        return jsonify({
            "success": True,
            "message": f"Bought {amount} {good} for ${cost}",
            "cost": cost,
        })
    
    elif action == "sell":
        if good not in game.train["cargo"]:
            return jsonify({"error": "You don't have this good"}), 400
        
        amount = min(amount, game.train["cargo"][good])
        if amount <= 0:
            return jsonify({"error": "Invalid amount"}), 400
        
        revenue = amount * price
        game.train["money"] += revenue
        game.train["cargo"][good] -= amount
        if game.train["cargo"][good] <= 0:
            del game.train["cargo"][good]
        
        game.total_profit += revenue
        
        return jsonify({
            "success": True,
            "message": f"Sold {amount} {good} for ${revenue}",
            "revenue": revenue,
        })
    
    return jsonify({"error": "Invalid action"}), 400


@app.route('/api/game/<session_id>/repair', methods=['POST'])
def repair(session_id):
    """Repair train damage."""
    if session_id not in game_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    game = game_sessions[session_id]
    damage = game.train["damage"]
    
    if damage <= 0:
        return jsonify({"error": "No damage to repair"}), 400
    
    cost = damage * 5
    if game.train["money"] < cost:
        return jsonify({"error": "Not enough money", "cost": cost}), 400
    
    game.train["money"] -= cost
    game.train["damage"] = 0
    
    return jsonify({
        "success": True,
        "message": "Train repaired!",
        "cost": cost,
    })


@app.route('/api/game/<session_id>/rest_crew', methods=['POST'])
def rest_crew(session_id):
    """Rest crew members."""
    if session_id not in game_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    game = game_sessions[session_id]
    
    for member in game.crew:
        member["stamina"] = min(100, member["stamina"] + 20)
        member["morale"] = min(100, member["morale"] + 10)
    
    return jsonify({
        "success": True,
        "message": "Crew rested!",
    })


@app.route('/api/game/<session_id>/accept_contract', methods=['POST'])
def accept_contract(session_id):
    """Accept a contract."""
    if session_id not in game_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    game = game_sessions[session_id]
    data = request.json
    
    contract_type = data.get("type", "delivery")
    reward = random.randint(100, 300)
    
    contract = {
        "id": f"contract_{game.turn}_{len(game.contracts)}",
        "type": contract_type,
        "description": f"{contract_type.title()} contract",
        "reward": reward,
        "deadline": game.turn + 5,
        "completed": False,
    }
    
    game.contracts.append(contract)
    
    return jsonify({
        "success": True,
        "contract": contract,
    })


@app.route('/api/game/<session_id>/depart', methods=['POST'])
def depart(session_id):
    """Depart from station - choose destination."""
    if session_id not in game_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    game = game_sessions[session_id]
    data = request.json
    
    destination_id = data.get("destination")
    if not destination_id or destination_id not in game.map_nodes:
        return jsonify({"error": "Invalid destination"}), 400
    
    current_node = game.map_nodes.get(game.current_node_id)
    if destination_id not in current_node.get("connections", []):
        return jsonify({"error": "Destination not reachable"}), 400
    
    # Start travel
    game.phase = "travel"
    game.travel_log = []
    
    # Consume resources
    coal_used = random.randint(5, 15)
    water_used = random.randint(5, 15)
    
    game.train["coal"] -= coal_used
    game.train["water"] -= water_used
    
    game.travel_log.append(f"Consumed: {coal_used} coal, {water_used} water")
    
    # Check resource depletion
    if game.train["coal"] <= 0 or game.train["water"] <= 0:
        game.travel_log.append("WARNING: Running low on resources!")
    
    # Random event (30% chance)
    if random.random() < 0.3:
        event = random.choice(EVENTS_DATA)
        game.pending_event = {
            **event,
            "destination_id": destination_id,
        }
        game.phase = "event"
        
        return jsonify({
            "success": True,
            "phase": "event",
            "event": game.pending_event,
            "travel_log": game.travel_log,
        })
    
    # Combat encounter (25% chance)
    if random.random() < 0.25:
        enemy = random.choice(ENEMY_TYPES)
        game.pending_combat = {
            "enemy": enemy,
            "destination_id": destination_id,
        }
        game.phase = "combat"
        
        return jsonify({
            "success": True,
            "phase": "combat",
            "combat": game.pending_combat,
            "travel_log": game.travel_log,
        })
    
    # No events - proceed to arrival
    game.phase = "arrival"
    game.pending_destination = destination_id
    
    return jsonify({
        "success": True,
        "phase": "arrival",
        "destination_id": destination_id,
        "travel_log": game.travel_log,
    })


@app.route('/api/game/<session_id>/event_choice', methods=['POST'])
def event_choice(session_id):
    """Handle event choice."""
    if session_id not in game_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    game = game_sessions[session_id]
    data = request.json
    
    if not game.pending_event:
        return jsonify({"error": "No pending event"}), 400
    
    choice_idx = data.get("choice", 0)
    event = game.pending_event
    destination_id = event["destination_id"]
    
    if choice_idx < 0 or choice_idx >= len(event["choices"]):
        return jsonify({"error": "Invalid choice"}), 400
    
    effect = event["choices"][choice_idx]["effect"]
    choice_text = event["choices"][choice_idx]["text"]
    
    game.travel_log.append(f"Event: {event['title']}")
    game.travel_log.append(f"Choice: {choice_text}")
    
    # Apply effects
    if effect == "repair":
        game.train["damage"] = max(0, game.train["damage"] - 10)
        game.train["coal"] -= 5
        game.travel_log.append("Track repaired. Used 5 coal.")
    elif effect == "detour":
        game.train["coal"] -= 10
        game.travel_log.append("Took detour. Used extra 10 coal.")
    elif effect == "risk":
        if random.random() < 0.5:
            game.train["damage"] += 15
            game.travel_log.append("Risky passage caused damage!")
        else:
            game.travel_log.append("Risky passage succeeded!")
    elif effect == "take_passengers":
        earnings = random.randint(30, 80)
        game.train["money"] += earnings
        game.travel_log.append(f"Took passengers aboard. Earned ${earnings}.")
    elif effect == "buy_discount":
        game.train["coal"] = min(100, game.train["coal"] + 20)
        game.train["water"] = min(100, game.train["water"] + 20)
        game.train["money"] = max(0, game.train["money"] - 50)
        game.travel_log.append("Bought supplies at discount.")
    elif effect == "sell_premium":
        if game.train["cargo"]:
            good = list(game.train["cargo"].keys())[0]
            amount = min(game.train["cargo"][good], 10)
            price = game.current_prices.get(good, 20) * 1.3
            revenue = int(amount * price)
            game.train["money"] += revenue
            game.train["cargo"][good] -= amount
            if game.train["cargo"][good] <= 0:
                del game.train["cargo"][good]
            game.travel_log.append(f"Sold goods for premium: ${revenue}")
    elif effect == "mine_coal":
        game.train["coal"] = min(100, game.train["coal"] + 15)
        game.travel_log.append("Mined 15 coal.")
    elif effect == "push_through":
        if random.random() < 0.4:
            game.train["damage"] += 10
            game.travel_log.append("Storm caused damage!")
        else:
            game.travel_log.append("Made it through the storm!")
    elif effect == "wait":
        game.turn += 1
        game.travel_log.append("Waited out the storm.")
    
    game.pending_event = None
    game.phase = "arrival"
    game.pending_destination = destination_id
    
    return jsonify({
        "success": True,
        "phase": "arrival",
        "destination_id": destination_id,
        "travel_log": game.travel_log,
    })


@app.route('/api/game/<session_id>/combat', methods=['POST'])
def combat(session_id):
    """Handle combat resolution."""
    if session_id not in game_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    game = game_sessions[session_id]
    data = request.json
    
    if not game.pending_combat:
        return jsonify({"error": "No pending combat"}), 400
    
    doctrine = data.get("doctrine", "balanced")
    if doctrine not in COMBAT_DOCTRINES:
        return jsonify({"error": "Invalid doctrine"}), 400
    
    enemy = game.pending_combat["enemy"]
    destination_id = game.pending_combat["destination_id"]
    
    # Calculate player strength
    player_strength = 0
    
    for carriage in game.train["carriages"]:
        if carriage.get("guards", 0) > 0:
            player_strength += carriage["defense"] * carriage["guards"]
        player_strength += carriage.get("defense", 0)
    
    for member in game.crew:
        if member["role"] == "guard":
            player_strength += member["skill"] * 2
        elif member["role"] == "engineer":
            player_strength += member["skill"] // 2
    
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
    
    combat_log = [
        f"Combat started against {enemy['name']}!",
        f"Player strength: {final_player:.1f} vs Enemy: {final_enemy:.1f}",
    ]
    
    victory = final_player >= final_enemy
    
    if victory:
        loot = random.randint(enemy["loot_min"], enemy["loot_max"])
        game.train["money"] += loot
        game.combats_won += 1
        
        combat_log.append(f"Victory! Looted ${loot}")
        
        # Apply damage based on fight difficulty
        damage_ratio = final_enemy / final_player if final_player > 0 else 1
        if damage_ratio > 0.8:
            game.train["damage"] += 20
            combat_log.append("Heavy damage sustained!")
        elif damage_ratio > 0.5:
            game.train["damage"] += 10
            combat_log.append("Moderate damage sustained.")
        else:
            game.train["damage"] += 5
            combat_log.append("Minor damage only.")
    else:
        combat_log.append("Defeated! Forced to retreat.")
        game.train["damage"] += 30
        
        # Lose some cargo
        if game.train["cargo"]:
            lost_good = random.choice(list(game.train["cargo"].keys()))
            lost_amount = min(game.train["cargo"][lost_good], 20)
            game.train["cargo"][lost_good] -= lost_amount
            if game.train["cargo"][lost_good] <= 0:
                del game.train["cargo"][lost_good]
            combat_log.append(f"Lost {lost_amount} units of {lost_good}")
    
    game.pending_combat = None
    game.phase = "arrival"
    game.pending_destination = destination_id
    
    return jsonify({
        "success": True,
        "victory": victory,
        "combat_log": combat_log,
        "phase": "arrival",
        "destination_id": destination_id,
    })


@app.route('/api/game/<session_id>/arrive', methods=['POST'])
def arrive(session_id):
    """Arrive at destination."""
    if session_id not in game_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    game = game_sessions[session_id]
    data = request.json
    
    destination_id = data.get("destination_id", getattr(game, 'pending_destination', None))
    
    if not destination_id or destination_id not in game.map_nodes:
        return jsonify({"error": "Invalid destination"}), 400
    
    # Update position
    game.current_node_id = destination_id
    node = game.map_nodes[destination_id]
    
    if not node["visited"]:
        node["visited"] = True
        game.stations_visited += 1
    
    # Complete contracts
    completed_contracts = []
    for contract in game.contracts:
        if not contract["completed"]:
            contract["completed"] = True
            game.train["money"] += contract["reward"]
            game.contracts_completed += 1
            completed_contracts.append(contract)
    
    # Rest crew
    for member in game.crew:
        member["stamina"] = min(100, member["stamina"] + 20)
        member["morale"] = min(100, member["morale"] + 10)
    
    # Update market
    game._update_market()
    
    # Update company value
    game.update_company_value()
    
    # Increment turn
    game.turn += 1
    
    # Check game state
    game_result = game.check_game_state()
    
    # Set phase back to station
    game.phase = "station"
    game.pending_destination = None
    
    return jsonify({
        "success": True,
        "node": node,
        "completed_contracts": completed_contracts,
        "game_over": game_result["game_over"],
        "victory": game_result["victory"],
        "reason": game_result.get("reason", ""),
    })


@app.route('/api/game/<session_id>/summary', methods=['GET'])
def get_summary(session_id):
    """Get end-game summary."""
    if session_id not in game_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    game = game_sessions[session_id]
    
    return jsonify({
        "turns_survived": game.turn,
        "stations_visited": game.stations_visited,
        "contracts_completed": game.contracts_completed,
        "combats_won": game.combats_won,
        "total_profit": game.total_profit,
        "final_company_value": game.company_value,
        "victory": game.victory,
    })


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("IRON FRONTIER: RAILS & RAIDERS - WEB EDITION")
    print("=" * 60)
    print("\nStarting server...")
    print("Open http://localhost:5000 in your browser to play!\n")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
