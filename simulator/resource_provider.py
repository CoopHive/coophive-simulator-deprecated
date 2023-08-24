from utils import *
from machine import Machine
from service_provider import ServiceProvider
from solver import Solver
from match import Match
from smart_contract import SmartContract
from result import Result


class ResourceProvider(ServiceProvider):
    def __init__(self, public_key: str):
        # machines maps CIDs -> machine metadata
        super().__init__(public_key)
        self.machines = {}
        self.solver_url = None
        self.solver = None
        self.smart_contract = None
        self.current_deals = {}
        self.current_job_running_times = {}

    def get_solver(self):
        return self.solver

    def get_smart_contract(self):
        return self.smart_contract

    def connect_to_solver(self, url: str, solver: Solver):
        self.solver_url = url
        self.solver = solver
        solver.subscribe_event(self.handle_solver_event)

    def connect_to_smart_contract(self, smart_contract: SmartContract):
        self.smart_contract = smart_contract
        smart_contract.subscribe_event(self.handle_smart_contract_event)

    def add_machine(self, machine_id: CID, machine: Machine):
        self.machines[machine_id.hash] = machine

    def remove_machine(self, machine_id):
        self.machines.pop(machine_id)

    def get_machines(self):
        return self.machines

    def create_resource_offer(self):
        pass

    def handle_solver_event(self, event):
        print(f"I, the RP have solver event {event.get_name(), event.get_data().get_id()}")
        # print(event.get_data().get_data()['resource_provider_address'], self.get_public_key())
        if event.get_name() == 'match':
            match = event.get_data()
            if match.get_data()['resource_provider_address'] == self.get_public_key():
                timeout_deposit = match.get_data()['timeout_deposit']
                tx = Tx(sender=self.get_public_key(), value=timeout_deposit)
                self.get_smart_contract().agree_to_match(match, tx)

    def handle_smart_contract_event(self, event):
        print(f"I, the RP have smart contract event {event.get_name(), event.get_data().get_id()}")
        if event.get_name() == 'deal':
            deal = event.get_data()
            deal_data = deal.get_data()
            deal_id = deal.get_id()
            self.current_deals[deal_id] = deal
            if deal_data['resource_provider_address'] == self.get_public_key():
                self.current_job_running_times[deal_id] = 0

    def create_result(self, deal_id):
        print(f"I, the RP am posting the result for deal {deal_id}")
        result = Result()
        result.add_data("deal_id", deal_id)
        result.set_id()
        result.add_data("result_id", result.get_id())
        tx = Tx(sender=self.get_public_key(), value=1)
        self.get_smart_contract().post_result(result, tx)

    def update_job_running_times(self):
        for deal_id, running_time in self.current_job_running_times.items():
            self.current_job_running_times[deal_id] += 1
            expected_running_time = self.current_deals[deal_id].get_data()['actual_honest_time_to_completion']
            if self.current_job_running_times[deal_id] >= expected_running_time:
                self.create_result(deal_id)
