import random
from abc import ABC, abstractmethod

from mesa import Agent
from numpy import ndarray

from .handlers import MovementHandler, AgingHandler, PregnancyHandler, InfectionHandler, MonetaryValueHandler

constants = {
    'max_mating_age': 10 * 356,
    'max_age': 11 * 356,

    'female_fetus_chance': 0.5,
    'gestation_length_days': 285
}


class Cattle(Agent, ABC):
    def __init__(self, unique_id: int, model, heading: ndarray):
        """
        The base class of the agents which implements common methods.

        :param unique_id: the unique id of the agent in the model
        :param model: the model the agent lives in
        :param heading: numpy array defining where the cattle heads to (in which direction does it walk)
        """
        super().__init__(unique_id, model)
        self.space = model.space
        self.heading = heading
        self.movement_handler = MovementHandler(self)

    def step(self) -> None:
        """
        Each agent is activated once per simulation iterator (once per day). This method implements the actions taken
        by an agent once it is activated.
        """
        self.movement_handler.handle()

    @property
    @abstractmethod
    def age_days(self):
        pass

    @property
    @abstractmethod
    def is_infected(self):
        pass

    @abstractmethod
    def gets_infected(self):
        pass

    @abstractmethod
    def gets_vaccinated(self, virus_spread_radius, chance_of_virus_transmission):
        pass

    @property
    @abstractmethod
    def is_vaccinated(self):
        pass

    @property
    @abstractmethod
    def production_cost(self):
        pass

    @property
    @abstractmethod
    def sale_value(self):
        pass

    @property
    def monetary_value(self):
        return self.sale_value - self.production_cost


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
        super().__init__(unique_id, model, heading)
        self.aging_handler = AgingHandler(self, age_days)
        self.pregnancy_handler = PregnancyHandler(self)
        self.infection_handler = InfectionHandler(self, infection_radius, chance_of_virus_transmission)
        self.monetary_value_handler = MonetaryValueHandler(self)

    def step(self):
        super().step()
        self.aging_handler.handle()
        self.infection_handler.handle()
        self.pregnancy_handler.handle()
        self.monetary_value_handler.handle()

    def gets_fertilized(self):
        self.pregnancy_handler.gets_fertilized()

    @property
    def is_fertile(self):
        return self.pregnancy_handler.is_fertile

    @property
    def is_infected(self):
        return self.infection_handler.is_infected

    def gets_infected(self):
        self.infection_handler.gets_infected()
        self.model.statistics.infected_count += 1

    @property
    def age_days(self):
        return self.aging_handler.age_days

    def gets_vaccinated(self, virus_spread_radius, chance_of_virus_transmission):
        self.infection_handler = InfectionHandler(self, virus_spread_radius, chance_of_virus_transmission,
                                                  self.infection_handler.infected_since_days, True)
        self.model.statistics.vaccinated_count += 1
        pass

    @property
    def is_vaccinated(self):
        return self.infection_handler.is_vaccination_handler

    @property
    def production_cost(self):
        return self.monetary_value_handler.production_cost

    @property
    def sale_value(self):
        return self.monetary_value_handler.sale_value


male_constants = {
    'mating_chance': 0.8,
    'fertilization_chance': 0.6,
}


class MaleCattle(Cattle):
    def __init__(self, unique_id: int, model, heading: ndarray):
        """
        A male cattle moves around and mates with a female agent in his vision (see cattle_vision). Since males are
        only seasonally placed in the model a male does not age, hence the reset age method.
        See base class for parameter doc
        """
        super().__init__(unique_id, model, heading)
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
            if random.random() < male_constants['mating_chance'] and \
                    random.random() < male_constants['fertilization_chance']:
                chosen_mate.gets_fertilized()

    @property
    def age_days(self):
        return male_constants['min_mating_age']

    @property
    def is_infected(self):
        """
        Since males are only added to the cage in mating season it is assumed that only healthy males are added
        :return: False
        """
        return False

    def gets_infected(self):
        pass

    def gets_vaccinated(self, virus_spread_radius, chance_of_virus_transmission):
        pass

    @property
    def is_vaccinated(self):
        return True

    @property
    def production_cost(self):
        return 0

    @property
    def sale_value(self):
        return 0


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
