import streamlit as st
import random
import json
import os

CARDS = ["C", "F", "K", "L"]

HIGHSCORE_FILE = "highscores.json"

def load_highscores():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            return json.load(f)
    return []

highscores = load_highscores() or []

def save_highscores(scores):
    temp_file = HIGHSCORE_FILE + ".tmp"
    with open(temp_file, "w") as f:
        json.dump(scores, f, indent=2)
    os.replace(temp_file, HIGHSCORE_FILE)

if "best_score" not in st.session_state:
    st.session_state.best_score = None

# --- GAME LOGIC (reuse from before, slightly trimmed) ---

def draw(deck, hand):
    if deck:
        hand.append(deck.pop(0))

def kill_enemy_unit(opponent):
    # prioritize killing knights (they are more valuable)
    if opponent["knights"] > 0:
        opponent["knights"] -= 1
    elif opponent["soldiers"] > 0:
        opponent["soldiers"] -= 1

def play_card(hand, state, opponent):
    played_crystal = state["played_crystal"]

    # Priority:
    # 1. Kill big threats
    # 2. Play strongest unit
    # 3. Ramp (crystal)

    # --- Knight
    if "K" in hand and state["energy"] >= 3:
        hand.remove("K")
        state["energy"] -= 3
        state["knights"] += 1
        return

    # --- Lightning Bolt (if valuable target exists)
    if "L" in hand and state["energy"] >= 2:
        if opponent["knights"] > 0 or opponent["soldiers"] >= 2:
            hand.remove("L")
            state["energy"] -= 2
            kill_enemy_unit(opponent)
            return

    # --- Soldier
    if "F" in hand and state["energy"] >= 1:
        hand.remove("F")
        state["energy"] -= 1
        state["soldiers"] += 1
        return

    # --- Crystal (1 per turn)
    if "C" in hand and not played_crystal:
        hand.remove("C")
        state["crystals"] += 1
        state["played_crystal"] = True
        return

def deal_damage(state, opponent):
    dmg = state["soldiers"] + 3 * state["knights"]
    opponent["health"] -= dmg

def init_player(deck):
    deck_copy = deck[:]
    random.shuffle(deck_copy)
    return {
        "deck": deck_copy[:],
        "hand": deck_copy[:3],
        "health": 20,
        "energy": 0,
        "crystals": 0,
        "soldiers": 0,
        "knights": 0,
        "played_crystal": False,
    }

def take_turn(player, opponent):
    player["energy"] = player["crystals"]
    player["played_crystal"] = False

    draw(player["deck"], player["hand"])
    play_card(player["hand"], player, opponent)  # ← changed
    deal_damage(player, opponent)

def simulate(deck1, deck2, first_player=1):
    p1 = init_player(deck1[:])
    p2 = init_player(deck2[:])

    for _ in range(50):
        if first_player == 1:
            take_turn(p1, p2)
            if p2["health"] <= 0:
                return 1

            take_turn(p2, p1)
            if p1["health"] <= 0:
                return 2
        else:
            take_turn(p2, p1)
            if p1["health"] <= 0:
                return 2

            take_turn(p1, p2)
            if p2["health"] <= 0:
                return 1

    return 0

def run_matchup(deck1, deck2, games=1000):
    score = 0
    wins = losses = draws = 0

    for i in range(games):
        first = 1 if i % 2 == 0 else 2
        result = simulate(deck1, deck2, first_player=first)

        if result == 1:
            wins += 1
            score += 1
        elif result == 2:
            losses += 1
            score -= 1
        else:
            draws += 1

    return score, wins, losses, draws

# --- UI ---

st.title("Deck Simulator")

if st.toggle("Show card descriptions"):
    st.markdown("""
    **Crystal (C)**
    - Cost: 0  
    - Effect: +1 energy every turn  
    - Limit: max 1 played per turn  

    **Foot Soldier (F)**
    - Cost: 1  
    - Effect: Deals 1 damage per turn  

    **Knight (K)**
    - Cost: 3  
    - Effect: Deals 3 damage per turn

    **Lightning Bolt (L)**
    - Cost: 2  
    - Effect: Destroy 1 enemy unit (prioritizes Knight)    
    """)

player_name = st.text_input("Enter your name (or nickname)", "")

st.subheader("Build your deck")

c = st.slider("Crystal", 0, 12, 6)
f = st.slider("Foot Soldier", 0, 12, 2)
k = st.slider("Knight", 0, 12, 2)
l = st.slider("Lightning Bolt", 0, 12, 2)

if c + f + k + l != 12:
    st.warning("Deck must have exactly 12 cards")
else:
    player_deck = (
        ["C"] * c +
        ["F"] * f +
        ["K"] * k +
        ["L"] * l
    )

    opponents = {
        "Aggro": ["F"] * 8 + ["C"] * 4,
        "Ramp": ["C"] * 6 + ["K"] * 4 + ["F"] * 2,
        "Balanced": ["C"] * 4 + ["F"] * 4 + ["K"] * 4,
    }

    if st.button("Simulate"):
        total_score = 0

        for name, opp_deck in opponents.items():
            score, w, l, d = run_matchup(player_deck, opp_deck)

            total_score += score
            total_games = w + l + d

            st.write(
                f"{name}: {w/total_games*100:.1f}% "
                f"({w}-{l}-{d}) | Score: {score}"
            )

        st.subheader(f"Total Score: {total_score}")

        # update best score
        if (
            st.session_state.best_score is None
            or total_score > st.session_state.best_score
        ):
            st.session_state.best_score = total_score

        st.write(f"🏆 Best Score: {st.session_state.best_score}")

        deck_data = {
            "C": c,
            "F": f,
            "K": k,
            "L": l
        }

        if player_name == "":
            st.caption("Tip: enter a name to track your scores")

        player = player_name if player_name else "Anonymous"

        updated = False

        for entry in highscores:
            if entry["name"] == player and entry["deck"] == deck_data:
                # same player + same deck
                if total_score > entry["score"]:
                    entry["score"] = total_score  # overwrite with better score
                updated = True
                break

        # if not found, add new entry
        if not updated:
            highscores.append({
                "name": player,
                "deck": deck_data,
                "score": total_score
            })

        # sort and keep top 10
        highscores = sorted(highscores, key=lambda x: x["score"], reverse=True)
        highscores = highscores[:10]

        save_highscores(highscores)

st.subheader("🏆 Top 10 Leaderboard")

for i, entry in enumerate(highscores, 1):
    deck = entry["deck"]

    st.write(
        f"{i}. {entry['name']} — {entry['score']}"
    )