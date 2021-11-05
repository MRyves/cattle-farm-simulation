from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import TextElement, ChartModule

from .cattle_agent import FemaleCattle, MaleCattle
from .model import CattleFarmModel
from visualization.SimpleContinuousModule import SimpleCanvas


class CattleFarmServer(ModularServer):
    verbose = False

    def __init__(self, model_cls, visualization_elements, name="Mesa Model", model_params=None):
        if model_params is None:
            model_params = {}
        super().__init__(model_cls, visualization_elements, name, model_params)


class DateElement(TextElement):

    def __init__(self):
        super().__init__()

    def render(self, model):
        return "Current date: " + model.current_date.strftime("%b %d %Y")


def agent_portrayal(agent: FemaleCattle):
    portrayal = {'Shape': 'circle',
                 'Color': 'Yellow',
                 'Filled': 'true',
                 'r': 1}
    if type(agent) is MaleCattle:
        portrayal['Color'] = 'Blue'
    elif agent.is_infected:
        portrayal['Color'] = 'Red'
    elif not agent.is_fertile:
        portrayal['Color'] = 'Green'

    return portrayal


canvas = SimpleCanvas(agent_portrayal, 700, 700)
date = DateElement()
cattle_count_chart = ChartModule([{"Label": "Cattle count", "Color": "Black"}])

model_params_constant = {
    'size': 1000,
    'init_cattle_count': UserSettableParameter("number", "Initial cattle count", 300, 1, 1000),
    'males_per_female': UserSettableParameter("number", "Males per female", 0.01, 0.001, 0.1),
    'init_infection_count': UserSettableParameter("number", "Initially infected cattle", 1, 1, 10),
    'infection_radius': UserSettableParameter("slider", "Infection radius", 10, 5, 20),
    'chance_of_virus_transmission': UserSettableParameter("slider", "Chance of virus transmission", 0.5, 0.1, 0.8, 0.1),
    'cattle_move_speed': UserSettableParameter("slider", "Move speed", 50, 10, 100),
    'cattle_vision': UserSettableParameter("slider", "Mating vision", 50, 30, 150),
    'cattle_separation': UserSettableParameter("slider", "Min separation", 10, 5, 20)
}

server = CattleFarmServer(CattleFarmModel,
                          [canvas, date, cattle_count_chart],
                          'Cattle farm',
                          model_params_constant)
