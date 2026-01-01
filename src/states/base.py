class BaseState:
    def __init__(self, app):
        self.app = app
        self.done = False
        self.quit = False
        self.next_state = None
        self.persistent_data = {}

    def startup(self, persistent):
        self.persistent_data = persistent

    def cleanup(self):
        return self.persistent_data

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass