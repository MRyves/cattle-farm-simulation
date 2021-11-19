from django.conf import settings
from django.template import Template, Context, Engine
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


class StatisticsTableElement(TextElement):
    def __init__(self):
        super().__init__()
        settings.configure()
        self.table_template_str = """
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Value</th>
                <tr>
            </thead>
            <tbody>
                {{ body|safe }}
            </tbody>
        </table>
        """
        self.template = Template(self.table_template_str, engine=Engine())

    def render(self, model):
        body = self.__get_table_row("Total cattle: ", model.statistics.cattle_count)
        body += self.__get_table_row("Total infected: ", model.statistics.infected_count)
        body += self.__get_table_row("Removed through random check: ", model.statistics.removed_through_random_check)
        c = Context({'body': body})
        return self.template.render(c)

    def __get_table_row(self, title, number):
        return "<tr><td>" + title + "</td><td>" + str(number) + "</td></tr>"


def agent_portrayal(agent: FemaleCattle):
    portrayal = {'Shape': 'circle',
                 'Color': 'Green',
                 'Filled': True,
                 'r': 1.5}
    if type(agent) is MaleCattle:
        portrayal['Color'] = 'Blue'
    elif agent.is_infected:
        portrayal['Color'] = 'Red'
    elif not agent.is_fertile:
        portrayal['Color'] = 'Black'
        portrayal['Filled'] = False

    return portrayal


canvas = SimpleCanvas(agent_portrayal, 700, 700)
date = DateElement()
cattle_count_chart = ChartModule(
    [{"Label": "Cattle count", "Color": "Black"}, {"Label": "Infected count", "Color": "Red"}])
removed_through_random_check = StatisticsTableElement()

model_params_constant = {
    'size': 1000,
    'init_cattle_count': UserSettableParameter("number", "Initial cattle count", 300, 1, 1000),
    'males_per_female': UserSettableParameter("number", "Males per female", 0.01, 0.001, 0.1),
    'init_infection_count': UserSettableParameter("number", "Initially infected cattle", 1, 1, 10),
    'infection_radius': UserSettableParameter("slider", "Infection radius", 10, 5, 20),
    'infection_check_sample_size': UserSettableParameter("slider", "Infection check sample size", 1, 0, 10),
    'chance_of_virus_transmission': UserSettableParameter("slider", "Chance of virus transmission", 0.02, 0.01, 0.25,
                                                          0.01),
}

server = CattleFarmServer(CattleFarmModel,
                          [canvas, date, cattle_count_chart, removed_through_random_check],
                          'Cattle farm',
                          model_params_constant)
