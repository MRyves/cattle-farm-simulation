import random

import numpy as np
from mesa import Agent
from numpy import ndarray

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
    def __init__(self, unique_id: int, model, pos: ndarray, age_days: int, move_speed: int):
        """
       Create a new female cattle. The FemaleCattle is a very simple agent, all it does is move around.
        :param unique_id: the unique id of the cattle
        :param model: the model the cattle lives in
        :param pos: the initial position of the cattle
        :param age_days: the age of the cattle
        """
        super().__init__(unique_id, model)
        self.age_days = age_days
        self.pos = pos
        self.space = model.space
        self.move_speed = move_speed

    def step(self):
        self.age_days += 1

        if self.age_days >= constants['max_age']:
            self.model.remove_agent(self)
            return
        self.move()

    def move(self):
        new_pos = self.__calc_possible_position()
        while self.space.out_of_bounds(new_pos):
            new_pos = self.__calc_possible_position()
        self.space.move_agent(self, new_pos)

    def __calc_possible_position(self) -> ndarray:
        direction = np.array((self.random.random() * self.random.choice([-1, 1]),
                              self.random.random() * random.choice([-1, 1])))
        new_pos = self.pos + direction * self.move_speed
        return new_pos


class FemaleCattle(Cattle):
    def __init__(self, unique_id: int, model, pos: ndarray, age_days: int, move_speed: int):
        """
       Create a new female cattle. The FemaleCattle is a very simple agent, all it does is move around.
        :param unique_id: the unique id of the cattle
        :param model: the model the cattle lives in
        :param pos: the initial position of the cattle
        :param age_days: the age of the cattle
        """
        super().__init__(unique_id, model, pos, age_days, move_speed)
        self.days_pregnant = -1

    def step(self):
        super().step()
        if self.days_pregnant != -1:
            if self.days_pregnant >= constants['gestation_length_days']:
                if self.random.random() < constants['female_fetus_chance']:
                    # add baby cattle at position of mother
                    new_agent = FemaleCattle(self.model.cattle_id_sequence, self.model, self.pos, 0, self.move_speed)
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
    def __init__(self, unique_id: int, model, pos: ndarray, move_speed, mating_vision):
        super().__init__(unique_id, model, pos, constants['min_mating_age'], move_speed)
        self.vision = mating_vision

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
