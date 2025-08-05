import json
import random
from collections import defaultdict, deque

class MarkovModel:
    def __init__(self, memory_limit=10000, file_path="memory.json"):
        self.memory_limit = memory_limit
        self.file_path = file_path
        self.messages = deque(maxlen=memory_limit)
        self.model = defaultdict(list)
        self.load_memory()

    def load_memory(self):
        try:
            with open(self.file_path, "r") as f:
                self.messages = deque(json.load(f), maxlen=self.memory_limit)
            self._rebuild_model()
        except FileNotFoundError:
            pass

    def save_memory(self):
        with open(self.file_path, "w") as f:
            json.dump(list(self.messages), f)

    def _rebuild_model(self):
        self.model.clear()
        for msg in self.messages:
            words = msg.split()
            for i in range(len(words) - 1):
                self.model[words[i]].append(words[i + 1])

    def learn(self, message: str):
        self.messages.append(message)
        words = message.split()
        for i in range(len(words) - 1):
            self.model[words[i]].append(words[i + 1])

    def generate(self, max_words=20):
        if not self.model:
            return "هیچی یاد نگرفتم هنوز."
        word = random.choice(list(self.model.keys()))
        result = [word]
        for _ in range(max_words - 1):
            if word not in self.model or not self.model[word]:
                break
            word = random.choice(self.model[word])
            result.append(word)
        return " ".join(result)

    def clear_memory(self):
        self.messages.clear()
        self.model.clear()
        self.save_memory()
