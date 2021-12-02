from datetime import date, timedelta
from enum import Enum

import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import ContinuousSpace
from mesa.time import RandomActivation
from numpy import ndarray

from .cattle_agent import CattleBuilder, FemaleCattle
from .handlers import RemovalReasons

constants = {
    'start_age_min': 356 * 1,
    'start_age_max': 356 * 9
}

one_day_delta = timedelta(days=1)


class Statistics:
    def __init__(self):
        self.cattle_count = 0
        self.infected_count = 0
        self.vaccinated_count = 0
        self.died_of_age = 0
        self.died_of_disease = 0
        self.removed_by_random_check = 0
        self.virus_located = False
        self.total_cost = 0
        self.total_value = 0


class CattleFarmModel(Model):

    def __init__(self,
                 size: float,
                 init_cattle_count: int,
                 males_per_female: float,
                 init_infection_count: int,
                 infection_check_sample_size: int,
                 infection_check_accuracy: float,
                 infection_check_interval: int,
                 infection_radius: int,
                 chance_of_virus_transmission: float,
                 infection_radius_vaccinated: int,
                 chance_of_virus_transmission_vaccinated: float,
                 vaccinations_per_day: int):
        super().__init__()
        self.__cattle_id_sequence = 0
        self.infection_check_sample_size = infection_check_sample_size
        self.infection_radius_vaccinated = infection_radius_vaccinated
        self.chance_of_virus_transmission_vaccinated = chance_of_virus_transmission_vaccinated
        self.vaccinations_per_day = vaccinations_per_day
        self.infection_check_accuracy = infection_check_accuracy
        self.infection_check_interval = infection_check_interval

        self.cattle_builder = CattleBuilder(self, infection_radius, chance_of_virus_transmission)
        self.male_cattle = []
        self.males_in_cage = False

        self.current_date = date(date.today().year, 1, 1)

        self.statistics = Statistics()

        self.space = ContinuousSpace(size, size, False)
        self.schedule = RandomActivation(self)

        self.init_agents(init_cattle_count, males_per_female, init_infection_count)

        self.datacollector = DataCollector(
            {
                "Cattle count": lambda m: m.statistics.cattle_count,
                "Infected count": lambda m: m.statistics.infected_count,
                "Vaccinated count": lambda m: m.statistics.vaccinated_count,
                "Virus located": lambda m: m.statistics.virus_located
            },
        )
        self.datacollector.collect(self)
        self.running = True

    def init_agents(self, init_cattle_count, males_per_female, init_infection_count):
        male_count = int(round(init_cattle_count * males_per_female, 0))
        # create males
        for _ in range(male_count):
            pos = self.__random_position()
            heading = np.random.random(2) * 2 - 1
            agent = self.cattle_builder.build(self.cattle_id_sequence, heading, constants['start_age_min'], True)
            print("Created male agent: ", agent.unique_id)
            self.male_cattle.append(agent)

        # create females
        infection_count = 0
        for i in range(init_cattle_count):
            age_days = self.random.randint(constants['start_age_min'], constants['start_age_max'])
            pos = self.__random_position()
            heading = np.random.random(2) * 2 - 1
            agent = self.cattle_builder.build(self.cattle_id_sequence, heading, age_days)
            if infection_count < init_infection_count:
                agent.gets_infected()
                infection_count += 1
            self.add_agent(agent, pos)

    def add_agent(self, agent, pos, should_account_agent=True):
        self.space.place_agent(agent, pos)
        self.schedule.add(agent)
        if should_account_agent:
            self.statistics.cattle_count += 1

    def remove_agent(self, agent, reason):
        if agent.is_infected:
            self.statistics.infected_count -= 1
        if reason != RemovalReasons.NONE:
            self.statistics.cattle_count -= 1
            if reason == RemovalReasons.AGE:
                self.statistics.died_of_age += 1
            elif reason == RemovalReasons.DISEASE:
                self.statistics.died_of_disease += 1
            elif reason == RemovalReasons.RANDOM_CHECK:
                self.statistics.removed_by_random_check += 1
        self.space.remove_agent(agent)
        self.schedule.remove(agent)

    def step(self) -> None:
        self.__handle_mating_seasons()
        self.__handle_vaccination()

        if self.current_date.timetuple().tm_yday % self.infection_check_interval == 0:
            self.__random_infection_check()

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

    def __random_infection_check(self):
        if self.infection_check_sample_size <= 0:
            return

        random_selection = self.schedule.agents if len(self.schedule.agents) <= self.infection_check_sample_size else \
            self.random.sample(self.schedule.agents, k=self.infection_check_sample_size)

        infected_of_selection = filter(lambda a: type(a) is FemaleCattle and a.is_infected, random_selection)

        for agent in infected_of_selection:
            if agent.random.random() <= self.infection_check_accuracy:
                print("Random infection check found infected cattle, vaccinations should start")
                self.remove_agent(agent, RemovalReasons.RANDOM_CHECK)
                self.statistics.virus_located = True

    def __handle_mating_seasons(self):
        if self.mating_season and not self.males_in_cage:
            print("Mating season! Adding males to cage...")
            self.males_in_cage = True
            for male in self.male_cattle:
                self.add_agent(male, self.__random_position(), False)
        if not self.mating_season and self.males_in_cage:
            print("Mating season is over, removing males from cage...")
            self.males_in_cage = False
            for male in self.male_cattle:
                self.remove_agent(male, RemovalReasons.NONE)

    def __handle_vaccination(self):
        if not self.statistics.virus_located or \
                self.vaccinations_per_day == 0:
            return

        non_vaccinated_cattle = set(x for x in self.schedule.agents if type(x) is FemaleCattle and not x.is_vaccinated)
        selection = non_vaccinated_cattle if len(non_vaccinated_cattle) <= self.vaccinations_per_day else \
            self.random.sample(non_vaccinated_cattle, k=self.vaccinations_per_day)
        for agent in selection:
            agent.gets_vaccinated(self.infection_radius_vaccinated, self.chance_of_virus_transmission_vaccinated)
