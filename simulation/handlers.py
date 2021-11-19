from abc import ABCMeta, abstractmethod, ABC

import numpy as np
from numpy import ndarray


class Handler(metaclass=ABCMeta):
    """
    Base interface for all the handlers of the simulation
    """

    @abstractmethod
    def handle(self) -> None:
        """
        The handle method implements the logic of each handler. Thus it must be overridden in every implementation of
        this interface.
        """
        raise NotImplementedError


aging_constants = {
    'max_age': 11 * 356,
}


class AgingHandler(Handler):
    """
    Handles the aging & dying process of the cattle
    """

    def __init__(self, agent, age_days=0):
        self.agent = agent
        self.model = agent.model
        self.age_days = age_days

    def handle(self) -> None:
        self.age_days += 1
        if self.age_days >= aging_constants['max_age']:
            self.model.remove_agent(self.agent)
            return


movement_constants = {
    'move_speed': 50,
    'vision': 50,
    'separation': 10,

    'cohere_factor': 0.05,  # the relative importance of matching neighbors' positions
    'separate_factor': 0.1,  # the relative importance of avoiding close neighbors
    'match_factor': 0.8,  # the relative importance of matching neighbors' headings
}


class MovementHandler(Handler):
    """
    Handles the movement of the agents using the Boid algorithm. See https://de.wikipedia.org/wiki/Boids
    """

    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.model = agent.model

        self.movement_speed = movement_constants['move_speed']
        self.agent_vision = movement_constants['vision']
        self.agent_separation = movement_constants['separation']

        self.cohere_factor = movement_constants['cohere_factor']
        self.separate_factor = movement_constants['separate_factor']
        self.match_factor = movement_constants['match_factor']

    def handle(self) -> None:
        neighbors = self.model.space.get_neighbors(self.agent.pos, self.agent_vision, False)
        heading = self.agent.heading
        heading += (
                           self.__cohere(neighbors) * self.cohere_factor
                           + self.__separate(neighbors) * self.separate_factor
                           + self.__match_heading(neighbors) * self.match_factor
                   ) / 2
        heading /= np.linalg.norm(self.agent.heading)
        self.agent.heading = self.__assure_boid_stays_in_space(heading)

        new_pos = self.agent.pos + self.agent.heading * self.movement_speed
        self.model.space.move_agent(self.agent, new_pos)

    def __cohere(self, neighbors):
        """
        Return the vector toward the center of mass of the local neighbors.
        """
        cohere = np.zeros(2)
        if neighbors:
            for neighbor in neighbors:
                cohere += self.model.space.get_heading(self.agent.pos, neighbor.pos)
            cohere /= len(neighbors)
        return cohere

    def __separate(self, neighbors):
        """
        Return a vector away from any neighbors closer than separation dist.
        """
        me = self.agent.pos
        them = (n.pos for n in neighbors)
        separation_vector = np.zeros(2)
        for other in them:
            if self.model.space.get_distance(me, other) < self.agent_separation:
                separation_vector -= self.model.space.get_heading(me, other)
        return separation_vector

    def __match_heading(self, neighbors):
        """
        Return a vector of the neighbors' average heading.
        """
        match_vector = np.zeros(2)
        if neighbors:
            for neighbor in neighbors:
                match_vector += neighbor.heading
            match_vector /= len(neighbors)
        return match_vector

    def __assure_boid_stays_in_space(self, heading: ndarray):
        """
        This method makes sure that an agent never leaves the boundaries of the space by changing the heading. If the
        agents next move would lead to it leaving the space the heading is inverted in the other direction.
        :param heading: the new heading of the agent
        :return: the fixed heading
        """
        if (self.agent.pos[0] + (heading[0] * self.movement_speed) <= self.model.space.x_min) or \
                (self.agent.pos[0] + (heading[0] * self.movement_speed) >= self.model.space.x_max):
            heading[0] *= -1

        if (self.agent.pos[1] + (heading[1] * self.movement_speed) >= self.model.space.y_max) or \
                (self.agent.pos[1] + (heading[1] * self.movement_speed) <= self.model.space.y_min):
            heading[1] *= -1

        return heading


pregnancy_constants = {
    'min_mating_age': 1 * 356,
    'max_mating_age': 10 * 356,
    'gestation_length_days': 285,
    'female_fetus_chance': 0.5,
}


class PregnancyHandler(Handler):
    """
    Handles the pregnancy of female cattle.
    """

    def __init__(self, agent):
        self.agent = agent
        self.model = agent.model
        self.pregnant_for_days = -1

    def handle(self) -> None:
        if not self.is_pregnant:
            return
        if self.pregnant_for_days >= pregnancy_constants['gestation_length_days']:
            self.__generate_baby()
            self.pregnant_for_days = -1
        else:
            self.pregnant_for_days += 1

    def gets_fertilized(self):
        self.pregnant_for_days = 0

    @property
    def is_pregnant(self):
        return self.pregnant_for_days != -1

    @property
    def is_fertile(self):
        return pregnancy_constants['max_mating_age'] >= self.agent.age_days >= pregnancy_constants[
            'min_mating_age'] and not self.is_pregnant

    def __generate_baby(self):
        if self.agent.random.random() < pregnancy_constants['female_fetus_chance']:
            # add baby cattle at position of mother
            new_agent = self.model.cattle_builder.build(self.model.cattle_id_sequence, self.agent.heading, 0)
            self.model.add_agent(new_agent, self.agent.pos)


class InfectionHandler(Handler):
    """
    Handles the virus simulation
    """
    def __init__(self, agent, infection_radius, chance_of_virus_transmission):
        self.agent = agent
        self.infection_radius = infection_radius
        self.chance_of_virus_transmission = chance_of_virus_transmission
        self.space = agent.space
        self.model = agent.model
        self.infected_since_days = -1

    def handle(self) -> None:
        if not self.is_infected:
            return

        print("Handling infection...")
        self.infected_since_days += 1
        self.__infect_neighbors()

    def gets_infected(self):
        self.infected_since_days = 0

    @property
    def is_infected(self):
        return self.infected_since_days != -1

    def __infect_neighbors(self):
        healthy_friends_around = list(filter(
            lambda c: not c.is_infected,
            self.space.get_neighbors(self.agent.pos, self.infection_radius, False)))
        print("Healthy friends around: ", healthy_friends_around)
        for neighbor in healthy_friends_around:
            if self.agent.random.random() <= self.chance_of_virus_transmission:
                neighbor.gets_infected()
