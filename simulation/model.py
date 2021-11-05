from datetime import date, timedelta

import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import ContinuousSpace
from mesa.time import RandomActivation
from numpy import ndarray

from .cattle_agent import FemaleCattle, MaleCattle

constants = {
    'start_age_min': 356 * 1,
    'start_age_max': 356 * 10
}

one_day_delta = timedelta(days=1)


class CattleFarmModel(Model):
    def __init__(self, size: float, init_cattle_count: int, males_per_female: float, cattle_move_speed: int, mating_vision: int):
        super().__init__()
        self.init_cattle_count = init_cattle_count
        self.males_per_female = males_per_female
        self.cattle_count = 0
        self.__cattle_id_sequence = 0

        self.cattle_move_speed = cattle_move_speed
        self.mating_vision = mating_vision

        self.male_cattles = []
        self.males_in_cage = False

        self.current_date = date(date.today().year, 1, 1)

        self.space = ContinuousSpace(size, size, False)
        self.schedule = RandomActivation(self)

        self.init_agents()
        self.datacollector = DataCollector(
            {"Cattle count": "cattle_count"}
        )
        self.datacollector.collect(self)
        self.running = True

    def init_agents(self):
        male_count = int(round(self.init_cattle_count * self.males_per_female, 0))
        # create males
        for i in range(male_count):
            pos = self.__random_position()
            agent = MaleCattle(self.cattle_id_sequence, self, pos, self.cattle_move_speed, self.mating_vision)
            print("Created male agent: ", agent.unique_id)
            self.male_cattles.append(agent)

        # create females
        for i in range(self.init_cattle_count):
            age_days = self.random.randint(constants['start_age_min'], constants['start_age_max'])
            pos = self.__random_position()
            agent = FemaleCattle(self.cattle_id_sequence, self, pos, age_days, self.cattle_move_speed)
            self.add_agent(agent)

    def add_agent(self, agent):
        print("Adding agent: ", agent.unique_id)
        self.space.place_agent(agent, agent.pos)
        self.schedule.add(agent)
        self.cattle_count += 1

    def remove_agent(self, agent):
        self.space.remove_agent(agent)
        self.schedule.remove(agent)
        self.cattle_count -= 1

    def step(self) -> None:
        self.__handle_mating_seasons()
        self.schedule.step()
        self.current_date += one_day_delta
        self.datacollector.collect(self)

    @property
    def mating_season(self) -> bool:
        return 4 <= self.current_date.month <= 5

    @property
    def cattle_id_sequence(self) -> int:
        current_id = self.__cattle_id_sequence
        self.__cattle_id_sequence += 1
        return current_id

    def __random_position(self) -> ndarray:
        new_x = self.random.random() * self.space.x_max
        new_y = self.random.random() * self.space.y_max
        return np.array((new_x, new_y))

    def __handle_mating_seasons(self):
        if self.mating_season and not self.males_in_cage:
            print("Mating season! Adding males to cage...")
            self.males_in_cage = True
            for male in self.male_cattles:
                male.reset_age()
                male.pos = self.__random_position()
                self.add_agent(male)
        if not self.mating_season and self.males_in_cage:
            print("Mating season is over, removing males from cage...")
            self.males_in_cage = False
            for male in self.male_cattles:
                self.remove_agent(male)
