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


class LegendListElement(TextElement):
    def __init__(self):
        super().__init__()
        self.list = """
        <h3>Legend:</h3>
        <ol>
            <li>Normal: White (green border)</li>
            <li>Fertile: White (black border)</li>
            <li>Male: Blue</li>
            <li>Infected and not vaccinated: Red</li>
            <li>Infected and vaccinated: White (red border)</li>
            <li>Not infected and vaccinated: Green</li>
        </ol>
        """

    def render(self, model):
        return self.list


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
        cattle_cost = sum([agent.production_cost for agent in model.schedule.agents])
        body = self.__get_table_row("Total cattle: ", str(model.statistics.cattle_count))
        body += self.__get_table_row("Total infected: ", str(model.statistics.infected_count))
        body += self.__get_table_row("Total deaths of age: ", str(model.statistics.died_of_age))
        body += self.__get_table_row("Total deaths of disease: ", str(model.statistics.died_of_disease))
        body += self.__get_table_row("Removed by random check: ", str(model.statistics.removed_by_random_check))
        body += self.__get_table_row("Total vaccination shots: ", str(model.statistics.vaccinated_count))
        body += self.__get_table_row("Virus located: ", str(model.statistics.virus_located))
        body += self.__get_table_row("Total cattle cost: ", "${:,.2f}".format(cattle_cost))
        body += self.__get_table_row("Total cost (including vaccinations): ",
                                     "${:,.2f}".format(cattle_cost + (9 * model.statistics.vaccinated_count)))
        body += self.__get_table_row("Total sale value: ",
                                     "${:,.2f}".format(sum([agent.sale_value for agent in model.schedule.agents])))
        c = Context({'body': body})
        return self.template.render(c)

    def __get_table_row(self, title: str, content: str):
        return "<tr><td>" + title + "</td><td>" + content + "</td></tr>"


def agent_portrayal(agent: FemaleCattle):
    portrayal = {'Shape': 'circle',
                 'Color': 'Green',
                 'Filled': False,
                 'r': 1.5}
    if type(agent) is MaleCattle:
        portrayal['Color'] = 'Blue'
    elif agent.is_infected and not agent.is_vaccinated:
        portrayal['Color'] = 'Red'
        portrayal['Filled'] = True
    elif agent.is_infected and agent.is_vaccinated:
        portrayal['Color'] = 'Red'
        portrayal['Filled'] = False
    elif agent.is_vaccinated:
        portrayal['Filled'] = True
    elif not agent.is_fertile:
        portrayal['Color'] = 'Black'
        portrayal['Filled'] = False

    return portrayal


canvas = SimpleCanvas(agent_portrayal, 700, 700)
date = DateElement()
cattle_count_chart = ChartModule(
    [{"Label": "Cattle count", "Color": "Black"}, {"Label": "Infected count", "Color": "Red"}])
money_chart = ChartModule([
    {"Label": "Monetary value", "Color": "Blue"}
])
statistics = StatisticsTableElement()
legend = LegendListElement()

model_params_constant = {
    'size': 1000,
    'init_cattle_count': UserSettableParameter("number", "Initial cattle count", 300, 1, 1000),
    'males_per_female': UserSettableParameter("number", "Males per female", 0.01, 0.001, 0.1),
    'init_infection_count': UserSettableParameter("number", "Initially infected cattle", 1, 1, 10),
    'infection_check_sample_size': UserSettableParameter("slider", "Infection check sample size", 1, 0, 10),
    'infection_check_accuracy': UserSettableParameter("slider", "Infection check accuracy", 0.8, 0.1, 1, 0.1),
    'infection_check_interval': UserSettableParameter("slider", "Infection check interval", 1, 1, 7),
    'infection_radius': UserSettableParameter("slider", "Infection radius", 10, 5, 40),
    'chance_of_virus_transmission': UserSettableParameter("slider", "Chance of virus transmission", 0.02, 0.01, 0.25,
                                                          0.01),
    'infection_radius_vaccinated': UserSettableParameter("slider", "Infection radius (vaccinated)", 5, 1, 20),
    'chance_of_virus_transmission_vaccinated': UserSettableParameter("slider",
                                                                     "Chance of virus transmission (vaccinated)", 0.01,
                                                                     0.002, 0.2, 0.002),
    'vaccinations_per_day': UserSettableParameter("number", "Vaccinations per day", 1, 0, 100000),
}

server = CattleFarmServer(CattleFarmModel,
                          [canvas, date, cattle_count_chart, money_chart, statistics, legend],
                          'Cattle farm',
                          model_params_constant)
