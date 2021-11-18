import random

from mesa import Agent
from numpy import ndarray

from .handlers import MovementHandler

constants = {
    'min_mating_age': 1 * 356,
    'max_mating_age': 10 * 356,
    'max_age': 11 * 356,

    'mating_chance': 0.8,
    'fertilization_chance': 0.6,
    'female_fetus_chance': 0.5,
    'gestation_length_days': 285
}


class Cattle(Agent):
    def __init__(self, unique_id: int, model, age_days: int, heading: ndarray):
        """
        The base class of the agents which implements common methods.

        :param unique_id: the unique id of the agent in the model
        :param model: the model the agent lives in
        :param age_days: the age of the agent in days
        :param heading: numpy array defining where the cattle heads to (in which direction does it walk)
        """
        super().__init__(unique_id, model)
        self.infected_since_day = -1
        self.age_days = age_days
        self.space = model.space
        self.heading = heading
        self.movement_handler = MovementHandler(self)

    @property
    def is_infected(self):
        return self.infected_since_day > -1

    def step(self) -> None:
        """
        Each agent is activated once per simulation iterator (once per day). This method implements the actions taken
        by an agent once it is activated.
        """
        self.age_days += 1
        if self.age_days >= constants['max_age']:
            self.model.remove_agent(self)
            return
        if self.is_infected:
            self.infected_since_day += 1
        self.movement_handler.handle()


class FemaleCattle(Cattle):
    def __init__(self,
                 unique_id: int,
                 model,
                 age_days: int,
                 heading: ndarray,
                 infection_radius: int,
                 chance_of_virus_transmission: float):
        """
       Create a new female cattle. The FemaleCattle is a very simple agent, all it does is move around. A female
       cattle may also be fertilized by a bull. The pregnancy lasts for 285 days, then a new baby cattle is placed at
       the same location of the cattle in the model.
       See Cattle base class for parameter doc.
        """

        super().__init__(unique_id, model, age_days, heading)
        self.infection_radius = infection_radius
        self.chance_of_virus_transmission = chance_of_virus_transmission
        self.days_pregnant = -1

    def step(self):
        self.handle_pregnancy()
        self.handle_infection()
        super().step()

    def handle_pregnancy(self):
        if self.days_pregnant != -1:
            if self.days_pregnant >= constants['gestation_length_days']:
                if self.random.random() < constants['female_fetus_chance']:
                    # add baby cattle at position of mother
                    new_agent = self.model.cattle_builder.build(self.model.cattle_id_sequence, self.heading, 0)
                    self.model.add_agent(new_agent, self.pos)

                self.days_pregnant = -1
            else:
                self.days_pregnant += 1

    def handle_infection(self):
        if self.is_infected:
            healthy_friends_around = list(filter(
                lambda c: type(c) is FemaleCattle and not c.is_infected,
                self.space.get_neighbors(self.pos, self.infection_radius, False)))
            for neighbor in healthy_friends_around:
                if self.random.random() <= self.chance_of_virus_transmission:
                    neighbor.infected_since_day = 0
                    self.model.statistics.infected_count += 1

    def gets_fertilized(self):
        self.days_pregnant = 0

    @property
    def is_fertile(self):
        return self.days_pregnant == -1 and \
               constants['min_mating_age'] < self.age_days < constants['max_mating_age']


class MaleCattle(Cattle):
    def __init__(self, unique_id: int, model, heading: ndarray):
        """
        A male cattle moves around and mates with a female agent in his vision (see cattle_vision). Since males are
        only seasonally placed in the model a male does not age, hence the reset age method.
        See base class for parameter doc
        """
        super().__init__(unique_id, model, constants['min_mating_age'], heading)
        self.vision = self.movement_handler.agent_vision

    def step(self):
        self.look_for_mating()
        super().step()

    def look_for_mating(self):
        females_around = list(filter(
            lambda c: type(c) is FemaleCattle and c.is_fertile,
            self.space.get_neighbors(self.pos, self.vision, False)))
        if len(females_around) > 0:
            chosen_mate = random.choice(females_around)
            if random.random() < constants['mating_chance'] and \
                    random.random() < constants['fertilization_chance']:
                chosen_mate.gets_fertilized()

    def reset_age(self):
        self.age_days = constants['min_mating_age']

    @property
    def is_infected(self):
        """
        Since males are only added to the cage in mating season it is assumed that only healthy males are added
        :return: False
        """
        return False


class CattleBuilder:
    def __init__(self,
                 model,
                 infection_radius,
                 chance_of_virus_transmission):
        self.model = model
        self.infection_radius = infection_radius
        self.chance_of_virus_transmission = chance_of_virus_transmission

    def build(self, unique_id, heading, age_days, is_male=False) -> Cattle:
        if is_male:
            return MaleCattle(unique_id, self.model, heading)
        else:
            return FemaleCattle(unique_id, self.model, age_days, heading, self.infection_radius,
                                self.chance_of_virus_transmission)
