import logging
import interface

from datetime import datetime
from random import uniform, randint, gauss
from cumulocityAPI import CumulocityAPI


cumulocityAPI = CumulocityAPI()
log = logging.getLogger("measurements generation")


class Measurement(interface.MachineType):
    def __init__(self, model) -> None:
        self.model = model
        self.definitions = self.model.get('measurements', [])
        self.simulated_data = {}
        self.first_time = True

    def callback(self, definition, min_interval_in_seconds, max_interval_in_seconds):
        measurement_callback = lambda task: {self.measurement_functions(definition, task)}
        if definition:
            log.debug(f'Machine {self.model.get("label")}, id {self.model.get("id")}: create periodic task for measurement {definition}, interval ({min_interval_in_seconds}, {max_interval_in_seconds}) seconds')
        else:
            log.debug(f'No definition of measurement in machine {self.model.get("label")}, id {self.model.get("id")}')
        return measurement_callback

    def measurement_functions(self, measurement_definition, task):
        self.generate_measurement(measurement_definition=measurement_definition)
        self.send_measurements(measurement_definition=measurement_definition)

    def generate_measurement(self, measurement_definition):
        log.info(f"Generating value of measurement {measurement_definition.get('series')} of device {self.id}")
        distribution = measurement_definition.get("valueDistribution", "uniform")
        value = 0.0
        if distribution == "uniform":
            min_value = measurement_definition.get("minimumValue", measurement_definition.get("value"))
            max_value = measurement_definition.get("maximumValue", measurement_definition.get("value"))
            value = round(uniform(min_value, max_value), 2)
        elif distribution == "uniformint":
            min_value = measurement_definition.get("minimumValue", measurement_definition.get("value"))
            max_value = measurement_definition.get("maximumValue", measurement_definition.get("value"))
            value = randint(min_value, max_value)
        elif distribution == "normal":
            mu = measurement_definition.get("mu")
            sigma = measurement_definition.get("sigma")
            value = round(gauss(mu, sigma), 2)

        if (measurement_definition.get("type") is not None and measurement_definition.get("type") != ""): 
            type = measurement_definition.get("type")
            log.info(f"using defined type value: {type}")
        elif (measurement_definition.get("fragment") is not None and measurement_definition.get("fragment") != ""):
            type = measurement_definition.get("fragment")
            log.info(f"using fragment value fallback for type property: {type}")
        else:
            log.error(f"No definition about type and fragment found for measurement: {measurement_definition} for device {self.device_id} !")
            return

        self.simulated_data = {
            'type': type,
            'fragment': measurement_definition.get("fragment"),
            'series': measurement_definition.get("series"),
            'value': value,
            'unit': measurement_definition.get("unit"),
            'time': datetime.utcnow()
        }

    def send_measurements(self, measurement_definition):
        if not self.simulated_data:
            log.info(f"No measurement definition to create measurements for device #{self.device_id}, external id {self.id}")
            return
        base_dict = self.create_extra_info_dict(self.simulated_data)
        measurement_dict = self.create_individual_measurement_dict(self.simulated_data)
        base_dict.update(measurement_dict)
        log.info('Send create measurements requests')
        response = cumulocityAPI.create_measurements(measurement=base_dict)
        if response:
            log.info(f"Created new measurement for device {self.id} ({self.model.get('label')}): {base_dict}")

    def create_extra_info_dict(self, data):
        extraInfoDict = {
            "type": f"{data.get('type')}",
            "time": f"{interface.datetime_to_string(data.get('time'))}",
            "source": {
                "id": f"{self.device_id}"
            }
        }
        return extraInfoDict

    def create_individual_measurement_dict(self, data):
        measurementDict = {
            f"{data.get('fragment')}":
                {
                    f"{data.get('series')}":
                        {
                            "unit": f"{data.get('unit')}",
                            "value": data.get('value')
                        }
                }
        }
        return measurementDict

