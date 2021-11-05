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
                 'Color': 'Red',
                 'Filled': 'true',
                 'r': 1}
    if type(agent) is MaleCattle:
        portrayal['Color'] = 'Blue'
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
    'cattle_move_speed': UserSettableParameter("slider", "Move speed", 50, 10, 100),
    'cattle_vision': UserSettableParameter("slider", "Mating vision", 50, 30, 150),
    'cattle_separation': UserSettableParameter("slider", "Min separation", 10, 5, 20)
}

# self, size: float, init_cattle_count: int, males_per_female: float, cattle_move_speed: float,
#                  cattle_vision: float, cattle_separation: float

server = CattleFarmServer(CattleFarmModel,
                          [canvas, date, cattle_count_chart],
                          'Cattle farm',
                          model_params_constant)
