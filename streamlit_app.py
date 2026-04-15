import streamlit as st
import random

CARDS = ["C", "F", "K"]

if "best_score" not in st.session_state:
    st.session_state.best_score = None

# --- GAME LOGIC (reuse from before, slightly trimmed) ---

def draw(deck, hand):
    if deck:
        hand.append(deck.pop(0))

def play_card(hand, state):
    played_crystal = state["played_crystal"]

    if "K" in hand and state["energy"] >= 3:
        hand.remove("K")
        state["energy"] -= 3
        state["knights"] += 1
    elif "F" in hand and state["energy"] >= 1:
        hand.remove("F")
        state["energy"] -= 1
        state["soldiers"] += 1
    elif "C" in hand and not played_crystal:
        hand.remove("C")
        state["crystals"] += 1
        state["played_crystal"] = True

def deal_damage(state, opponent):
    dmg = state["soldiers"] + 3 * state["knights"]
    opponent["health"] -= dmg

def init_player(deck):
    random.shuffle(deck)
    return {
        "deck": deck[:],
        "hand": deck[:3],
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
    play_card(player["hand"], player)
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

def run_matchup(deck1, deck2, games=200):
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
    """)

st.subheader("Build your deck")

c = st.slider("Crystals", 0, 12, 4)
f = st.slider("Soldiers", 0, 12, 4)
k = st.slider("Knights", 0, 12, 4)

if c + f + k != 12:
    st.warning("Deck must have exactly 12 cards")
else:
    player_deck = ["C"] * c + ["F"] * f + ["K"] * k

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