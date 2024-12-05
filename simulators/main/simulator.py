import contextlib, json, logging, os, sys
import interface, time

from cumulocityAPI import C8Y_BASEURL, C8Y_TENANT, C8Y_USER, TEST_FLAG, CumulocityAPI
from datetime import datetime
from event import Event
from measurement import Measurement
from task import PeriodicTask


cumulocityAPI = CumulocityAPI()

# Get Tenant Options and configure Simulator
MICROSERVICE_OPTIONS = cumulocityAPI.get_tenant_option_by_category("simulators")
LOG_LEVEL = MICROSERVICE_OPTIONS.get("LOG_LEVEL", "INFO")

if LOG_LEVEL == "DEBUG":
    logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.INFO)

log = logging.getLogger("sims")
log.info(f"started at {interface.current_timestamp()}")
log.debug(f'Tenant options: {MICROSERVICE_OPTIONS}')

##########################################

log.debug(C8Y_BASEURL)
log.debug(C8Y_TENANT)
log.debug(C8Y_USER)


class MachineSimulator:
    def __init__(self, machine: interface.MachineType) -> None:
        self.machine = machine
        self.machine.device_id = self.machine.model.get("device_id")
        self.machine.locationId = self.machine.model.get("locationId", "")
        self.machine.enabled = self.machine.model.get('enabled', True)
        self.machine.out_of_production_time_logged = False
        self.machine.back_in_production_time_logged = False
        self.machine.id = self.machine.model.get('id')
        if self.machine.enabled:
            self.machine.tasks = list(map(self.__create_task, self.machine.definitions))
            log.debug(f'{self.machine.definitions}')

    def __create_task(self, definition):
        min_interval_in_seconds, max_interval_in_seconds = interface.calculate_interval_in_seconds(definition)
        callback = self.machine.callback(definition, min_interval_in_seconds, max_interval_in_seconds)
        task = PeriodicTask(min_interval_in_seconds, max_interval_in_seconds, callback)
        return task

    def tick(self):
        if not self.machine.enabled:
            return
        for task in self.machine.tasks:
            self.is_first_time(task)
            if task:
                task.tick()

    def is_first_time(self, task):
        with contextlib.suppress(Exception):
            if self.machine.first_time:
                # set the next_run time to always let the measurement generation to run in the first time
                task.next_run = datetime.timestamp(datetime.utcnow()) + 1
                self.machine.first_time = False


def get_or_create_device_id(device_model):
    sim_id = device_model.get("id")
    label = device_model.get("label")
    if not sim_id or not label:
        if not sim_id:
            log.debug("No definition info of device id")
        if not label:
            log.debug(f"No definition info of device name")
        log.info(f"Simulator device won't be created")
        return None

    device_id = cumulocityAPI.get_or_create_device(sim_id, label)
    return device_id


def load(filename):
    try:
        with open(filename) as f_obj:
            return json.load(f_obj)
    except Exception as e:
        log.error(e, type(e))
        return None


###################################################################################
if __name__ == '__main__':
    current_dir = os.getcwd()
    log.info(f'cwd:{current_dir}')

    if TEST_FLAG:
        # Change to the 'test' directory
        os.chdir("../../test")

    DEVICE_MODELS = load("simulator.json")
    if not DEVICE_MODELS:
        sys.exit()
    DEVICE_EVENT_MODELS = []
    DEVICE_MEASUREMENT_MODELS = []
    CREATED_DEVICE_IDS = []

    # Add device id to the model of devices
    for device_model in DEVICE_MODELS:
        device_model["device_id"] = get_or_create_device_id(device_model)
        if not device_model["device_id"]:
            continue
        else:
            CREATED_DEVICE_IDS.append(device_model["device_id"])
        if device_model.get("events"):
            DEVICE_EVENT_MODELS.append(device_model)
        if device_model.get("measurements"):
            DEVICE_MEASUREMENT_MODELS.append(device_model)

    # Get a list of simulator external IDs
    external_ids = cumulocityAPI.get_external_ids(CREATED_DEVICE_IDS)

    # create list of objects for events and measurements
    event_device_list = list(map(lambda model: MachineSimulator(Event(model)), DEVICE_EVENT_MODELS))
    measurement_device_list = list(map(lambda model: MachineSimulator(Measurement(model)), DEVICE_MEASUREMENT_MODELS))
    devices_list = event_device_list + measurement_device_list

    while True:
        for device in devices_list:
            device.tick()

        time.sleep(1)
