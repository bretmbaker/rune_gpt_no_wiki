# agent/trial_engine.py

import random
import time
import json

class TrialEngine:
    def __init__(self, screen_parser, state_path="state/trial_engine_state.json"):
        self.screen_parser = screen_parser
        self.state_path = state_path
        self.load_state()

        # Define hardcoded actions for Tutorial Island
        self.valid_actions = [
            "Talk to Survival Expert",
            "Chop Tree",
            "Light Fire",
            "Open Gate",
            "Catch Shrimp",
            "Cook Shrimp",
            "Open Inventory",
            "Equip Axe"
        ]

    def load_state(self):
        try:
            with open(self.state_path, "r") as f:
                self.state = json.load(f)
        except FileNotFoundError:
            self.state = {"attempts": {}, "successes": {}}

    def save_state(self):
        with open(self.state_path, "w") as f:
            json.dump(self.state, f, indent=2)

    def decide_action(self):
        """Simple exploration-based decision: try new or previously successful actions."""
        weights = []
        for action in self.valid_actions:
            success = self.state["successes"].get(action, 1)
            attempts = self.state["attempts"].get(action, 1)
            confidence = success / attempts
            weights.append(confidence)

        chosen = random.choices(self.valid_actions, weights=weights)[0]
        return chosen

    def perform_action(self, action):
        print(f"🧪 Attempting: {action}")
        self.state["attempts"][action] = self.state["attempts"].get(action, 0) + 1

        # Simulate action execution
        time.sleep(1)
        screen_output = self.screen_parser.get_current_text()

        if action.split()[0] in screen_output:
            print(f"✅ Success: {action}")
            self.state["successes"][action] = self.state["successes"].get(action, 0) + 1
        else:
            print(f"❌ Failure: {action}")

        self.save_state()

    def run(self, steps=10):
        for _ in range(steps):
            action = self.decide_action()
            self.perform_action(action)


# Minimal screen parser simulation
class MockScreenParser:
    def get_current_text(self):
        return random.choice([
            "You chopped some logs",
            "You lit the fire",
            "You cooked the shrimp",
            "You opened your inventory",
            "You talked to the Survival Expert",
            "Nothing happened",
            "Try again"
        ])


if __name__ == "__main__":
    parser = MockScreenParser()
    engine = TrialEngine(parser)
    engine.run(steps=15)
