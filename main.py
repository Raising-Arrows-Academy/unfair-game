import random

# --- CONFIG ---
TEAMS = ["Blue", "Green", "Red", "Yellow"]  # edit for your class
START_POINTS = 10

# (label, function_name, weight)
WHEEL = [
    ("+5 points",           "add_fixed:5",           3),
    ("+10 points",          "add_fixed:10",          2),
    ("+15 points",          "add_fixed:15",          1),
    ("-5 points",           "add_fixed:-5",          2),
    ("-10 points",          "add_fixed:-10",         1),
    ("Steal 5",             "steal:5",               2),
    ("Steal 10",            "steal:10",              1),
    ("Share +5 to all",     "share_all:5",           2),
    ("Swap scores",         "swap_random",           1),
    ("Double your score",   "multiply:2",            1),
    ("Halve your score",    "divide:2",              1),
    ("Wildcard",            "wildcard",              1),
]

# --- GAME STATE ---
scores = {team: START_POINTS for team in TEAMS}
steal_cooldown = {team: 0 for team in TEAMS}  # optional limiter on steals

def pick_outcome():
    labels = [w[0] for w in WHEEL]
    actions = [w[1] for w in WHEEL]
    weights = [w[2] for w in WHEEL]
    choice = random.choices(list(zip(labels, actions)), weights=weights, k=1)[0]
    return choice

def clamp_positive_negatives(team, delta):
    """Rubber-banding: if team ≤ 0 and delta < 0, give +5 instead."""
    if scores[team] <= 0 and delta < 0:
        return 5
    return delta

def apply_action(team, action):
    global scores
    if ":" in action:
        name, value = action.split(":")
        if name == "add_fixed":
            delta = clamp_positive_negatives(team, int(value))
            scores[team] += delta
            return f"{team} {'gains' if delta>=0 else 'loses'} {abs(delta)} points."
        if name == "steal":
            if steal_cooldown[team] > 0:
                return f"{team} attempted a steal but is on cooldown."
            victims = [t for t in TEAMS if t != team and scores[t] > 0]
            if not victims:
                return f"No valid team to steal from."
            victim = random.choice(victims)
            amt = min(int(value), scores[victim])
            scores[victim] -= amt
            scores[team] += amt
            steal_cooldown[team] = 2  # can’t steal for next 2 spins
            return f"{team} steals {amt} from {victim}."
        if name == "share_all":
            for t in TEAMS:
                scores[t] += int(value)
            return f"Everyone gains {value}."
        if name == "multiply":
            scores[team] = min(scores[team] * int(value), 100)  # cap
            return f"{team} doubles their score (cap 100)."
        if name == "divide":
            scores[team] = max((scores[team] + 1) // int(value), 0)
            return f"{team} halves their score."
    elif action == "swap_random":
        others = [t for t in TEAMS if t != team]
        other = random.choice(others)
        scores[team], scores[other] = scores[other], scores[team]
        return f"{team} swaps scores with {other}!"
    elif action == "wildcard":
        # Teacher’s Choice: here we just award +5
        scores[team] += 5
        return f"Wildcard! {team} completes a mini-challenge: +5."
    return "No action."

def print_scores():
    board = " | ".join(f"{t}: {scores[t]}" for t in TEAMS)
    print(f"\nSCORES → {board}\n")

def decay_cooldowns():
    for t in steal_cooldown:
        steal_cooldown[t] = max(0, steal_cooldown[t] - 1)

def main():
    print("=== Unfair Review Game ===")
    print("Commands:")
    print("  spin <TEAM>   → team spins the wheel (after all members answered correctly)")
    print("  scores        → show scoreboard")
    print("  next          → next question/round (decays steal cooldowns)")
    print("  quit          → end game\n")
    print_scores()

    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if cmd == "quit":
            break
        elif cmd == "scores":
            print_scores()
        elif cmd.startswith("spin "):
            team = cmd.split(" ", 1)[1].strip()
            if team not in TEAMS:
                print(f"Unknown team '{team}'.")
                continue
            label, action = pick_outcome()
            print(f"{team} spins… → {label}")
            result = apply_action(team, action)
            print(result)
            print_scores()
        elif cmd == "next":
            decay_cooldowns()
            print("(New question: steal cooldowns decayed.)")
        else:
            print("Unknown command.")
    print("Final scores:")
    print_scores()

if __name__ == "__main__":
    main()
