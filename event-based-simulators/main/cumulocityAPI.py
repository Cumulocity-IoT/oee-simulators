import time, json, os, logging, requests, base64
from datetime import datetime
from random import randint, uniform

C8Y_BASE = os.environ.get('C8Y_BASEURL') or 'http://localhost:8080'
C8Y_TENANT = os.environ.get('C8Y_TENANT') or 't100'
C8Y_USER = os.environ.get('C8Y_USER') or 'test'
C8Y_PASSWORD = os.environ.get('C8Y_PASSWORD') or 'test'

MOCK_RUEQUESTS = os.environ.get('MOCK_C8Y_REQUESTS') or 'false'

user_and_pass_bytes = base64.b64encode((C8Y_TENANT + "/" + C8Y_USER + ':' + C8Y_PASSWORD).encode('ascii')) # bytes
user_and_pass = user_and_pass_bytes.decode('ascii') # decode to str 

C8Y_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + user_and_pass
}

'''
End configuration
'''


# JSON-PYTHON mapping, to get json.load() working
null = None
false = False
true = True
######################


C8Y_SIMULATORS_GROUP = "c8y_EventBasedSimulators"

OEE_DATA_MODEL_FIELD_NAME = "@com_adamos_oee_datamodel_MachineOEEConfiguration"

__counter = 0
def global_counter():
    __counter = __counter + 1
    return __counter

class CumulocityAPI:
    def __init__(self) -> None:
        self.mocking = MOCK_RUEQUESTS.lower() == 'true'
        print(f'mocking: {self.mocking}' )

    def send_event(self, event):
        if self.mocking:
            print("mock: send event ", json.dumps(event), ' to ', C8Y_BASE + '/event/events')
            return json.dumps({'response': 200})
        else:
            response = requests.post(C8Y_BASE + '/event/events', headers=C8Y_HEADERS, data=json.dumps(event))
            self.log_warning_on_bad_repsonse(response)
            return response.json()

    def log_warning_on_bad_repsonse(self, response):
        if not response.ok:
            logging.warning(f'response status code is not ok: {response}, content: {response.text}')

    def get_or_create_device(self, sim_id, label):
        if self.mocking:
            print("mock: get or create device with external id", sim_id)
            return sim_id
        
        # Check if device already created
        return self.__get_device(sim_id) or self.__create_device(sim_id, label)

    def count_profiles(self, device_id):
        ''' count all profiles for the given device id.
        '''
        if self.mocking:
            print(f'mock: count_profiles(${device_id})')
            return 10
        request_query = f'{C8Y_BASE}/inventory/managedObjects/count?type=OEECalculationProfile&text={device_id}'
        response = requests.get(request_query, headers=C8Y_HEADERS)
        if response.ok:
            try:
                return int(response.text)
            except Exception as e:
                logging.warn(f'cannot convert "${response.text}" to number. exception: {e}')
                return 0
        else:
            self.log_warning_on_bad_repsonse(response)
            return 0
    
    def create_managed_object(self, fragment: str):
        if self.mocking:
            print(f'mock: create_managed_object()')
            return {'id': '0'}
        response = requests.post(C8Y_BASE + '/inventory/managedObjects', headers=C8Y_HEADERS, data=fragment)
        if response.ok:
            return response.json()
        self.log_warning_on_bad_repsonse(response)
        #TODO: check for errors
        return {}

    def update_managed_object(self, device_id, fragment):
        if self.mocking:
            print(f'mock: update_managed_object()')
            return {'id': '0'}

        response = requests.put(f'{C8Y_BASE}/inventory/managedObjects/{device_id}', headers=C8Y_HEADERS, data=fragment)
        if response.ok:
            return response.json()
        self.log_warning_on_bad_repsonse(response)
        return {}

    def add_child_object(self, device_id: str, child_id: str):
        if self.mocking:
            print(f'mock: add_child_device()')
            return {'id': '0'}

        data = {"managedObject": {"id": child_id}}
        response = requests.post(f'{C8Y_BASE}/inventory/managedObjects/{device_id}/childDevices', headers=C8Y_HEADERS, data=json.dumps(data))
        if response.ok:
            return response.json()

        self.log_warning_on_bad_repsonse(response)
        return {}


    def find_device_by_external_id(self, external_id):
        if self.mocking:
            print(f'mock: find_device_by_external_id()')
            return []
        response = requests.get(f'{C8Y_BASE}/inventory/managedObjects?text={external_id}&fragmentType=c8y_IsDevice', headers=C8Y_HEADERS)
        if response.ok:
            mangaged_objects = response.json()['managedObjects']
            return [mo['id'] for mo in mangaged_objects]
        return []

    def __get_device(self, sim_id):
        response = requests.get(f'{C8Y_BASE}/identity/externalIds/{C8Y_SIMULATORS_GROUP}/{sim_id}', headers=C8Y_HEADERS)
        if response.ok:
            device_id = response.json()['managedObject']['id']
            logging.info(f' Device({device_id}) has been found by its external id "{C8Y_SIMULATORS_GROUP}/{sim_id}".')
            return device_id
        return None
    
    def __create_device(self, sim_id, label):
        logging.info(f'Creating a new device with following external id "{C8Y_SIMULATORS_GROUP}/{sim_id}"')
        device = {
            'name': label,
            'c8y_IsDevice': {}
        }
        device = self.create_managed_object(json.dumps(device))
        device_id = device['id']
        if device_id:
            logging.info(f'new device created({device_id})')
            return self.__add_external_id(device_id, sim_id)
        return device_id

    def __add_external_id(self, device_id, ext_id, type = C8Y_SIMULATORS_GROUP):
        external_id = {
            'type': type,
            'externalId': ext_id
        }
        response = requests.post(C8Y_BASE + '/identity/globalIds/' + device_id + '/externalIds', headers=C8Y_HEADERS, data=json.dumps(external_id))
        self.log_warning_on_bad_repsonse(response)
        return device_id

