import threading

class Runner:
    def __init__(self, configuration_handler):
        self.configuration_handler = configuration_handler
        self.running = False

    def start(self):
        self.running = True
        # Logic to start the simulation
        threading.Thread(target=self.run).start()

    def run(self):
        # Logic to execute simulation
        while self.running:
            # Simulation execution code
            pass

    def stop(self):
        self.running = False
        # Logic to stop the simulation

    def monitor_progress(self):
        # Logic to monitor simulation progress
        pass

    # Additional methods...