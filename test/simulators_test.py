import json, subprocess, sys, time, unittest, logging, os
import config.root # Configure root directories

from datetime import datetime
from simulators.main.simulator import get_or_create_device_id, load
from simulators.main.cumulocityAPI import CumulocityAPI, C8Y_USER, C8Y_PASSWORD, C8Y_TENANT, C8Y_BASEURL
from simulators.main.interface import datetime_to_string
from unittest.mock import patch

log = logging.getLogger("Test")
logging.basicConfig(format='%(asctime)s %(name)s:%(message)s', level=logging.DEBUG)


class Test(unittest.TestCase):
    def setUp(self):
        self.cumulocity_api = CumulocityAPI()
        # Get Tenant Options and configure Simulator
        self.MICROSERVICE_OPTIONS = self.cumulocity_api.get_tenant_option_by_category("simulators")
        Utils.setup_model(self)
        log.info('-' * 100)


    def test_get_or_create_device_id_with_full_model_and_delete(self):
        log.info('-' * 100)
        log.info("Start testing create device and adding external id")
        log.info('-' * 100)

        device_id = Utils.create_device(self.device_model_with_events)
        # null device_id will fail the test
        self.assertIsNotNone(device_id)
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the test device with id {device_id}")
        log.info('-' * 100)

    def test_get_or_create_device_id_with_missing_id(self):
        log.info('-' * 100)
        log.info("Start testing create device with no id")
        log.info('-' * 100)

        device_id = Utils.create_device(self.device_model_no_id)
        # null device_id will fail the test
        self.assertIsNone(device_id)
        log.info('-' * 100)

    def test_get_or_create_device_id_with_missing_label(self):
        log.info('-' * 100)
        log.info("Start testing create device with no label")
        log.info('-' * 100)

        device_id = Utils.create_device(self.device_model_no_label)
        # null device_id will fail the test
        self.assertIsNone(device_id)
        log.info('-' * 100)

    @patch('logging.Logger.error')  # patch to hide the log.error method
    def test_load_json_file(self, mock_error):
        log.info('-' * 100)
        log.info("Start testing load json file")
        log.info('-' * 100)

        model = load("simulators/main/simulator.json") # Load model for unittest CLI
        if not model:
            model = load("../simulators/main/simulator.json") # Load model for unittest on IDE
        self.assertIsNotNone(model)
        log.info('-' * 100)

    def test_create_and_activate_oee_profile(self):
        log.info('-' * 100)
        log.info("Start testing create and activate oee profile")
        log.info('-' * 100)

        device_id = Utils.create_device(device_model=self.device_model_with_events)

        # Get current directory path
        current_dir = os.getcwd()

        # Extracts the base name of the current directory
        base_dir = os.path.basename(current_dir)
        # If the working directory is not test then change to test
        if base_dir != "test":
            # Change to the 'test' directory
            os.chdir("test")

        try:
            device_profile_info = self.oee_api.create_and_activate_profile(external_id=self.device_model_with_events.get('id'))
            # null device_profile_info will fail the test
            self.assertIsNotNone(device_profile_info)
        finally:
            # Change back to the original working directory
            os.chdir(current_dir)
            Utils.delete_oee_profile_and_device(self, profile_id= device_profile_info.get('id'), device_id=device_id)

        log.info('-' * 100)

    def test_create_update_organization_structure(self):
        log.info('-' * 100)
        log.info("Start testing create hierarchy asset (organization structure)")
        log.info('-' * 100)

        device_id = Utils.create_device(self.device_model_with_events)
        line_managed_object, site_managed_object = self.oee_api.create_or_update_asset_hierarchy(deviceIDs=device_id, line_description = "Simulator LINE", line_type = "LINE", site_description = "Simulator SITE", site_type = "SITE", oee_target = 80)
        self.assertIsNotNone(line_managed_object.get('hierarchy'))
        self.assertIsNotNone(site_managed_object.get('hierarchy'))
        line_id = line_managed_object.get('id')
        site_id = site_managed_object.get('id')
        self.cumulocity_api.delete_managed_object(site_id)
        log.info(f"Removed the test SITE with id {site_id}")
        self.cumulocity_api.delete_managed_object(line_id)
        log.info(f"Removed the test LINE structure with id {line_id}")
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the test device with id {device_id}")
        log.info('-' * 100)

    def test_send_event(self):
        log.info('-' * 100)
        log.info("Start testing sending event")
        log.info('-' * 100)

        device_id = Utils.create_device(self.device_model_with_events)
        log.info(f"Created the {self.device_model_with_events.get('label')} with id {device_id}")
        event = Utils.setup_events(device_id)
        response = self.cumulocity_api.send_event(event)
        self.assertIsNotNone(response)
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the {self.device_model_with_events.get('label')} with id {device_id}")
        log.info('-' * 100)


    def test_send_measurement(self):
        log.info('-' * 100)
        log.info("Start testing create measurement")
        log.info('-' * 100)

        device_id = Utils.create_device(self.device_model_with_events)
        log.info(f"Created the {self.device_model_with_events.get('label')} with id {device_id}")
        measurement = Utils.setup_measurements(device_id)
        response = self.cumulocity_api.create_measurements(measurement)
        self.assertIsNotNone(response)
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the {self.device_model_with_events.get('label')} with id {device_id}")
        log.info('-' * 100)

    def test_run_simulators_script(self):
        log.info('-' * 100)
        log.info("Start testing simulators script functions")
        log.info('-' * 100)

        # Get current directory path
        current_dir = os.getcwd()
        # Extracts the base name of the current directory
        base_dir = os.path.basename(current_dir)
        # If the working directory is not main then change to main
        if base_dir != "main" and base_dir != "test":
            # Change to the 'test' directory
            os.chdir("test")

        # Create simulator.json
        Utils.setup_model(self)
        device_model = [
            self.device_model_with_events,
            self.device_model_with_measurements
        ]
        with open("simulator.json", "w") as f:
            json.dump(device_model, f)
        self.assertTrue(os.path.exists('simulator.json'), msg=f"simulator.json is not created")

        try:
            # Change to the 'main' directory to access simulator script
            os.chdir("../simulators/main")
            # Start the script with arguments
            process = subprocess.Popen(["python", "simulator.py", "-b", C8Y_BASEURL, "-u", C8Y_USER, "-p", C8Y_PASSWORD, "-t", C8Y_TENANT, "-test"])
            # Wait for 60 seconds
            time.sleep(60)
            # Terminate the script
            process.terminate()

            # Get event device id and profile id from device external id
            event_device_id, event_profile_id = Utils.get_profile_and_device_ids_from_external_id(self, self.device_model_with_events.get('id'))
            # Get measurement device id and profile id from device external id
            measurement_device_id, measurement_profile_id = Utils.get_profile_and_device_ids_from_external_id(self, self.device_model_with_measurements.get('id'))

# TODO! get some dates!
#        { "id": "OneShiftLocation-DayShift", "seriesPostfix": "DayShift", "slotType": "PRODUCTION", "slotStart": "2022-07-13T08:00:00Z", "slotEnd": "2022-07-13T16:00:00Z", "description": "Day Shift", "active": true, "slotRecurrence": { "weekdays": [1, 2, 3, 4, 5] } },
#        { "id": "OneShiftLocation-Break", "slotType": "BREAK", "slotStart": "2022-07-13T12:00:00Z", "slotEnd": "2022-07-13T12:30:00Z", "description": "Day Shift Break", "active": true, "slotRecurrence": { "weekdays": [1, 2, 3, 4, 5] } }

            # Configure time milestone to extract data
#            for shiftplan in self.shiftplans[0].get('recurringTimeslots'):
#                if shiftplan.get('slotType') == 'PRODUCTION':
#                    date_from = shiftplan.get('slotStart')
#                if shiftplan.get('slotType') == 'BREAK':
#                    date_to = shiftplan.get('slotEnd')

            date_from="2022-07-13T08:00:00Z"
            date_to="2022-07-13T12:30:00Z"

            # Get events from event simulator
            events = self.cumulocity_api.get_events(date_from=date_from, date_to=date_to, device_id=event_device_id)
            self.assertTrue(len(events.get('events')) > 0 , msg=f'No events found for simulator {self.device_model_with_events.get("label")}')

            # Get measurements from measurement simulator
            measurements = self.cumulocity_api.get_measurements(date_from=date_from, date_to=date_to, device_id=measurement_device_id)
            self.assertTrue(len(measurements.get('measurements')) > 0, msg=f'No measurements found for simulator #{self.device_model_with_measurements.get("label")}')

        finally:
            Utils.delete_oee_profile_and_device(self, profile_id=event_profile_id, device_id=event_device_id)
            Utils.delete_oee_profile_and_device(self, profile_id=measurement_profile_id, device_id=measurement_device_id)

        log.info('-' * 100)

class Utils:
    def __init__(self):
        self.device_model_no_label = None
        self.device_model_no_id = None
        self.device_model_with_events = None
        self.device_model_with_measurements = None

    @staticmethod
    def create_device(device_model):
        log.info(f"Created device model: {device_model}")
        device_id = get_or_create_device_id(device_model=device_model)
        return device_id

    def setup_model(self):
        self.device_model_with_events = {
            "type": "Simulator",
            "id": "sim_001_test",
            "label": "Test Simulator with events",
            "enabled": "true",
            "locationId": "TestLocation",
            "events": [
                {
                    "type": "Availability",
                    "minimumPerHour": 1800,
                    "maximumPerHour": 3600,
                    "status": ["up", "down"],
                    "probabilities": [0.9, 0.1],
                    "durations": [0, 0],
                    "forceStatusDown": True
                },
                {
                    "type": "Piece_Produced",
                    "frequency": 25,
                    "followedBy": {
                        "type": "Piece_Ok",
                        "frequency": 20
                    }
                }
            ]
        }
        self.device_model_with_measurements = {
            "type": "Simulator",
            "id": "sim_002_test",
            "label": "Test Simulator with measurements",
            "locationId": "TestLocation",
            "enabled": "true",
            "measurements": [
                {
                    "fragment": "ProductionTime",
                    "series": "T",
                    "unit": "s",
                    "valueDistribution": "uniform",
                    "minimumValue": 450.0,
                    "maximumValue": 900.0,
                    "minimumPerHour": 1800.0,
                    "maximumPerHour": 3600.0
                }
            ]
        }
        self.device_model_no_id = {
            "type": "Simulator",
            "label": "Test Simulator #1",
            "enabled": "true"
        }
        self.device_model_no_label = {
            "type": "Simulator",
            "id": "sim_001_test",
            "enabled": "true"
        }

    @staticmethod
    def setup_events(device_id):
        event = {
            'source': {
                'id': f'{device_id}'
            },
            'time': f'{datetime_to_string(datetime.utcnow())}',
            'type': 'Availability',
            'text': 'Availability',
            'status': 'up',
            'production_time_s': 0.0,
            'production_speed_h': 25.0,
            'pieces_produced': 0.0
        }
        return event

    @staticmethod
    def setup_measurements(device_id):
        measurement = {
            'type': 'PumpPressure',
            'time': f'{datetime_to_string(datetime.utcnow())}',
            'source': {
                'id': f'{device_id}'
            },
            'Pressure': {
                'P':
                    {
                        'unit': 'hPa',
                        'value': 1179.26
                    }
            }

        }
        return measurement
    def get_profile_and_device_ids_from_external_id(self, external_id):
        device_id = self.cumulocity_api.get_device_by_external_id(external_id=f"{external_id}")
        profile_id = self.cumulocity_api.get_profile_id(deviceID=device_id)
        return device_id, profile_id

    def delete_oee_profile_and_device(self, profile_id, device_id):
        self.cumulocity_api.delete_managed_object(profile_id)
        log.info(f"Removed the test oee profile with id {profile_id}")
        self.cumulocity_api.delete_managed_object(device_id)
        log.info(f"Removed the test device with id {device_id}")


if __name__ == '__main__':
    # create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)

    # create a test runner
    runner = unittest.TextTestRunner()

    # run the test suite using the test runner
    result = runner.run(suite)

    # print the test result summary
    log.info(f"Executed: {result.testsRun}")
    log.info(f"Failed: {len(result.failures)}")
    log.info(f"Errors: {len(result.errors)}")

    # return True if no failures or errors, False otherwise
    if len(result.failures) == 0 and len(result.errors) == 0:
        sys.exit(0)
    else:
        sys.exit(1)