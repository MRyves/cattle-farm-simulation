import random

from numpy import ndarray

from .boid import Boid
import model

constants = {
    'cohere': 0.05,  # the relative importance of matching neighbors' positions
    'separate': 0.1,  # the relative importance of avoiding close neighbors
    'match': 0.8,  # the relative importance of matching neighbors' headings

    'min_mating_age': 1 * 356,
    'max_mating_age': 10 * 356,
    'max_age': 11 * 356,

    'mating_chance': 0.8,
    'fertilization_chance': 0.6,
    'female_fetus_chance': 0.5,
    'gestation_length_days': 285
}


class Cattle(Boid):
    def __init__(self, unique_id: int, model: model.CattleFarmModel, pos: ndarray, age_days: int, speed: float,
                 heading: ndarray, vision: float, separation: float):
        """
        The base class of the agents which implements common methods.

        :param unique_id: the unique id of the agent in the model
        :param model: the model the agent lives in
        :param pos: the current position of the agent
        :param age_days: the age of the agent in days
        :param speed: the distance one agent moves in one day
        :param heading: numpy array defining where the cattle heads to (in which direction does it walk)
        :param vision: how far does a cattle see and recognize its neighbors
        :param separation the minimum distance each cattle will attempt to keep from its neighbors
        """
        super().__init__(unique_id, model, pos, speed, heading, vision, separation, constants['cohere'],
                         constants['separate'], constants['match'])
        self.age_days = age_days
        self.pos = pos
        self.space = model.space
        self.move_speed = speed

    def step(self) -> None:
        """
        Each agent is activated once per simulation iterator (once per day). This method implements the actions taken
        by an agent once it is activated.
        """
        self.age_days += 1
        if self.age_days >= constants['max_age']:
            self.space.remove_agent(self)
            return
        super().step()


class FemaleCattle(Cattle):
    def __init__(self, unique_id: int, model, pos: ndarray, age_days: int, speed: float, heading: ndarray,
                 vision: float, separation: float):
        """
       Create a new female cattle. The FemaleCattle is a very simple agent, all it does is move around. A female
       cattle may also be fertilized by a bull. The pregnancy lasts for 285 days, then a new baby cattle is placed at
       the same location of the cattle in the model.
       See Cattle base class for parameter doc.
        """
        super().__init__(unique_id, model, pos, age_days, speed, heading, vision, separation)
        self.days_pregnant = -1

    def step(self):
        super().step()
        if self.days_pregnant != -1:
            if self.days_pregnant >= constants['gestation_length_days']:
                if self.random.random() < constants['female_fetus_chance']:
                    # add baby cattle at position of mother
                    new_agent = FemaleCattle(self.model.cattle_id_sequence, self.model, self.pos, 0, self.move_speed,
                                             self.heading, self.vision, self.separation)
                    self.model.add_agent(new_agent)
                    self.days_pregnant = -1
                else:
                    self.days_pregnant = -1
            else:
                self.days_pregnant += 1

    def gets_fertilized(self):
        self.days_pregnant = 0

    @property
    def is_fertile(self):
        return self.days_pregnant == -1 and constants['min_mating_age'] < self.age_days < constants['max_mating_age']


class MaleCattle(Cattle):
    def __init__(self, unique_id: int, model, pos: ndarray, age_days: int, speed: float, heading: ndarray,
                 vision: float, separation: float):
        """
        A male cattle moves around and mates with a female agent in his vision (see cattle_vision). Since males are
        only seasonally placed in the model a male does not age, hence the reset age method.
        See base class for parameter doc
        """
        super().__init__(unique_id, model, pos, constants['min_mating_age'], speed, heading, vision, separation)
        self.vision = vision

    def step(self):
        super().step()
        self.look_for_mating()

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
