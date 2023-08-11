from utils import CID
from machine import Machine
from service_provider import ServiceProvider


class ResourceProvider(ServiceProvider):
    def __init__(self, public_key: str, url: str):
        # machines maps CIDs -> machine metadata
        super().__init__(public_key, url)
        self.machines = {}

    def add_machine(self, machine_id: CID, machine: Machine):
        self.machines[machine_id.hash] = machine

    def remove_machine(self, machine_id):
        self.machines.pop(machine_id)

    def get_machines(self):
        return self.machines

    def create_resource_offer(self):
        pass