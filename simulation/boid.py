import numpy as np
from numpy import ndarray
from mesa import Agent


class Boid(Agent):
    """
    A Boid-style flocker agent.

    The agent follows three behaviors to flock:
        - Cohesion: steering towards neighboring agents.
        - Separation: avoiding getting too close to any other agent.
        - Alignment: try to fly in the same direction as the neighbors.

    Boids have a vision that defines the radius in which they look for their
    neighbors to flock with. Their speed (a scalar) and heading (a vector)
    define their movement. Separation is their desired minimum distance from
    any other Boid.
    """

    def __init__(
            self,
            unique_id,
            model,
            pos,
            speed,
            heading,
            vision,
            separation,
            cohere=0.8,
            separate=0.05,
            match=0.8,
    ):
        """
        Create a new Boid flocker agent.

        Args:
            unique_id: Unique agent identifyer.
            pos: Starting position
            speed: Distance to move per step.
            heading: numpy vector for the Boid's direction of movement.
            vision: Radius to look around for nearby Boids.
            separation: Minimum distance to maintain from other Boids.
            cohere: the relative importance of matching neighbors' positions
            separate: the relative importance of avoiding close neighbors
            match: the relative importance of matching neighbors' headings

        """
        super().__init__(unique_id, model)
        self.pos = np.array(pos)
        self.speed = speed
        self.heading = heading
        self.vision = vision
        self.separation = separation
        self.cohere_factor = cohere
        self.separate_factor = separate
        self.match_factor = match

    def cohere(self, neighbors):
        """
        Return the vector toward the center of mass of the local neighbors.
        """
        cohere = np.zeros(2)
        if neighbors:
            for neighbor in neighbors:
                cohere += self.model.space.get_heading(self.pos, neighbor.pos)
            cohere /= len(neighbors)
        return cohere

    def separate(self, neighbors):
        """
        Return a vector away from any neighbors closer than separation dist.
        """
        me = self.pos
        them = (n.pos for n in neighbors)
        separation_vector = np.zeros(2)
        for other in them:
            if self.model.space.get_distance(me, other) < self.separation:
                separation_vector -= self.model.space.get_heading(me, other)
        return separation_vector

    def match_heading(self, neighbors):
        """
        Return a vector of the neighbors' average heading.
        """
        match_vector = np.zeros(2)
        if neighbors:
            for neighbor in neighbors:
                match_vector += neighbor.heading
            match_vector /= len(neighbors)
        return match_vector

    def step(self):
        """
        Get the Boid's neighbors, compute the new vector, and move accordingly.
        """

        neighbors = self.model.space.get_neighbors(self.pos, self.vision, False)
        heading = self.heading
        heading += (
                           self.cohere(neighbors) * self.cohere_factor
                           + self.separate(neighbors) * self.separate_factor
                           + self.match_heading(neighbors) * self.match_factor
                   ) / 2
        heading /= np.linalg.norm(self.heading)
        self.heading = self.__assure_boid_stays_in_space(heading)

        new_pos = self.pos + self.heading * self.speed
        self.model.space.move_agent(self, new_pos)

    def __assure_boid_stays_in_space(self, heading: ndarray):
        """
        This method makes sure that an agent never leaves the boundaries of the space by changing the heading. If the
        agents next move would lead to it leaving the space the heading is inverted in the other direction.
        :param heading: the new heading of the agent
        :return: the fixed heading
        """
        if (self.pos[0] + (heading[0] * self.speed) <= self.model.space.x_min) or \
                (self.pos[0] + (heading[0] * self.speed) >= self.model.space.x_max):
            heading[0] *= -1

        if (self.pos[1] + (heading[1] * self.speed) >= self.model.space.y_max) or \
                (self.pos[1] + (heading[1] * self.speed) <= self.model.space.y_min):
            heading[1] *= -1

        return heading
