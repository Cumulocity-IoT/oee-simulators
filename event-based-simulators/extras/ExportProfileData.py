import json, logging, os, sys, requests, base64

import ArgumentsAndCredentialsHandler, Environment

from datetime import datetime, timedelta, timezone

####################################################
if not os.path.exists('logs'):
    os.makedirs('logs')
logger = logging.getLogger('ExportImportProfileData')
relativeFilePath = f"logs\{datetime.strftime(datetime.now(), '%Y%m%d%H%M%S_%f')}.log"
filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
hdlr = logging.FileHandler(filePath)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)
####################################################
# Setup for additional API request message
user_and_pass_bytes = base64.b64encode(
    (Environment.C8Y_TENANT + "/" + Environment.C8Y_USER + ':' + Environment.C8Y_PASSWORD).encode('ascii'))  # bytes
user_and_pass = user_and_pass_bytes.decode('ascii')  # decode to str

C8Y_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'Basic ' + user_and_pass
}
####################################################


def exportAllProfileDataFromChildDevices(c8y, DATA_TYPE, createFrom, createTo):
    deviceCount = 0
    deviceManagedObject = c8y.device_inventory.select(type="c8y_EventBasedSimulator")
    for device in deviceManagedObject:
        deviceCount += 1
        logger.info(f"Found device '{device.name}', id: #{device.id}, "
                    f"owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        print(f"Found device '{device.name}', id: #{device.id} ")
        logger.info(f"List of {device.name}'s child devices: ")

        childDeviceCount = 0
        for childDevice in device.child_devices:
            childDeviceCount += 1
            logger.info(f"Child device {childDevice.name}, id #{childDevice.id}")
            print(f"Child device {childDevice.name}, id #{childDevice.id}")
            deviceExternalId, deviceExternalIdType = checkDeviceExternalIdById(childDevice.id)
            if not deviceExternalId:
                continue
            if isExternalIdHasEventBasedSimulatorProfileType(deviceExternalIdType):
                filePath = createFilePath(fileName=deviceExternalId)
            else:
                continue
            if DATA_TYPE == "alarms":
                jsonAlarmsList = listAlarms(c8y, childDevice, createFrom, createTo)
                appendDataToJsonFile(jsonAlarmsList, filePath, DATA_TYPE)
                appendDataToJsonFile([], filePath, 'measurements')
                logger.info(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
            elif DATA_TYPE == "measurements":
                jsonMeasurementsList = listMeasurements(c8y, childDevice, createFrom, createTo)
                appendDataToJsonFile(jsonMeasurementsList, filePath, DATA_TYPE)
                appendDataToJsonFile([], filePath, 'alarms')
                logger.info(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
            else:
                jsonAlarmsList = listAlarms(c8y, childDevice, createFrom, createTo)
                appendDataToJsonFile(jsonAlarmsList, filePath, 'alarms')
                jsonMeasurementsList = listMeasurements(c8y, childDevice, createFrom, createTo)
                appendDataToJsonFile(jsonMeasurementsList, filePath, 'measurements')
                logger.info(f"Alarms and Measurements data is added to data file at {filePath}")
        if childDeviceCount == 0:
            logger.debug(f"No child device of device {device.name}, id #{device.id} found")

    if deviceCount == 0:
        logger.debug(f"No device in tenant {Environment.C8Y_TENANT} found")


def ExportSpecificProfileDataWithDeviceId(c8y, DATA_TYPE, createFrom, createTo, DEVICE_ID):
    deviceName = findDeviceNameById(DEVICE_ID)
    deviceCount = 0
    deviceExternalId, deviceExternalIdType = checkDeviceExternalIdById(DEVICE_ID)
    if not deviceExternalId:
        sys.exit()
    if isExternalIdHasEventBasedSimulatorProfileType(deviceExternalIdType):
        filePath = createFilePath(fileName=deviceExternalId)
    else:
        sys.exit()
    logger.info(f"Search for {DATA_TYPE} data from device {DEVICE_ID} ")
    for device in c8y.device_inventory.select(name=deviceName):
        deviceCount += 1
        logger.info(f"Child device {device.name}, id #{device.id}")
        if DATA_TYPE == "alarms":
            jsonAlarmsList = listAlarms(c8y, device, createFrom, createTo)
            appendDataToJsonFile(jsonAlarmsList, filePath, DATA_TYPE)
            appendDataToJsonFile([], filePath, 'measurements')
            logger.info(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
        elif DATA_TYPE == "measurements":
            # listing measurements of child device
            jsonMeasurementsList = listMeasurements(c8y, device, createFrom, createTo)
            appendDataToJsonFile(jsonMeasurementsList, filePath, DATA_TYPE)
            appendDataToJsonFile([], filePath, 'alarms')
            logger.info(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
        else:
            jsonAlarmsList = listAlarms(c8y, device, createFrom, createTo)
            appendDataToJsonFile(jsonAlarmsList, filePath, 'alarms')
            jsonMeasurementsList = listMeasurements(c8y, device, createFrom, createTo)
            appendDataToJsonFile(jsonMeasurementsList, filePath, 'measurements')
            logger.info(f"Alarms and Measurements data is added to data file at {filePath}")

    if deviceCount == 0:
        logger.debug(f"No device with id {DEVICE_ID} found")


def findDeviceNameById(DEVICE_ID):
    response = requests.get(f'{Environment.C8Y_BASE}/inventory/managedObjects/{DEVICE_ID}',
                            headers=C8Y_HEADERS)
    if not response.ok:
        logger.error(
            f"Connection to url '{Environment.C8Y_BASE}/inventory/managedObjects/{DEVICE_ID}' failed. Check your parameters in environment file again")
        sys.exit()
    else:
        try:
            deviceName = response.json()['name']
        except:
            logger.error(f"Device #{DEVICE_ID} does not have name")
            sys.exit()

    return deviceName


def listAlarms(c8y, device, createFrom, createTo):
    jsonAlarmsList = []
    # Create a count variable as a json/dict key to save json data
    print(jsonAlarmsList)
    count = 0
    for alarm in c8y.alarms.select(source=device.id, created_after=createFrom, created_before=createTo):
        logger.info(
            f"Found alarm id #{alarm.id}, severity: {alarm.severity}, time: {alarm.time}, creation time: {alarm.creation_time}, update time : {alarm.updated_time}\n")
        count += 1
        jsonAlarmsList.append(alarm.to_json())
    return jsonAlarmsList


def listMeasurements(c8y, device, createFrom, createTo):
    jsonMeasurementsList = []
    # Create a count variable as a json/dict key to save json data
    count = 0
    for measurement in c8y.measurements.select(source=device.id, after=createFrom, before=createTo):
        logger.info(f"Found measurement id #{measurement.id}\n")
        count += 1
        jsonMeasurementsList.append(measurement.to_json())
    return jsonMeasurementsList


def appendDataToJsonFile(jsonDataList, filePath, data_type, json_data={}):
    # Create new json file or add data to an existing json file
    with open(filePath, 'w') as f:
        json_data[f"{data_type.capitalize()}"] = jsonDataList
        json.dump(json_data, f, indent=2)


def getExternalIdReponse(deviceId):
    externalIdResponse = requests.get(f'{Environment.C8Y_BASE}/identity/globalIds/{deviceId}/externalIds',
                                      headers=C8Y_HEADERS)
    if not externalIdResponse.ok:
        logger.error(
            f"Connection to url '{Environment.C8Y_BASE}/identity/globalIds/{deviceId}/externalIds' failed. Check your parameters in environment file again")
        sys.exit()
    else:
        return externalIdResponse


def checkDeviceExternalIdById(deviceId):
    externalIdResponse = getExternalIdReponse(deviceId)

    try:
        deviceExternalId = externalIdResponse.json()['externalIds'][0]['externalId']
        deviceExternalIdType = externalIdResponse.json()['externalIds'][0]['type']
    except:
        logger.error(f"Could not find external id for the device with id {deviceId}")
        return None, None

    return deviceExternalId, deviceExternalIdType


def isExternalIdHasEventBasedSimulatorProfileType(deviceExternalIdType):

    if deviceExternalIdType == "c8y_EventBasedSimulatorProfile":
        return True
    else:
        logger.debug(f"The type {deviceExternalIdType} of external ID must be c8y_EventBasedSimulatorProfile")
        print(f"The type {deviceExternalIdType} of external ID must be c8y_EventBasedSimulatorProfile")
        return False


def createFilePath(fileName):
    # Check if folder containing data files exists and make one if not
    if not os.path.exists('export_data'):
        os.makedirs('export_data')
    relativeFilePath = f'export_data\{fileName}.json'
    filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
    logger.info(f"Created successfully file path: {filePath}")
    return filePath


def SetTimePeriodToExportData(CREATE_FROM, CREATE_TO):
    if not CREATE_FROM or CREATE_TO:
        createTo = datetime.now().replace(tzinfo=timezone.utc)
        TimeUnit = Environment.TIME_UNIT

        if TimeUnit == 'seconds' or not TimeUnit:
            createFrom = createTo - timedelta(seconds=Environment.PERIOD_TO_EXPORT)
            return createFrom, createTo

        if TimeUnit == 'days':
            createFrom = createTo - timedelta(days=Environment.PERIOD_TO_EXPORT)
        elif TimeUnit == 'weeks':
            createFrom = createTo - timedelta(weeks=Environment.PERIOD_TO_EXPORT)
        elif TimeUnit == 'hours':
            createFrom = createTo - timedelta(hours=Environment.PERIOD_TO_EXPORT)
        elif TimeUnit == 'minutes':
            createFrom = createTo - timedelta(minutes=Environment.PERIOD_TO_EXPORT)
        return createFrom, createTo

    return CREATE_FROM, CREATE_TO


# Main function to run the script
if __name__ == '__main__':
    c8y = ArgumentsAndCredentialsHandler.c8yPlatformConnection()
    # Check if connection to tenant can be created
    try:
        requests.get(f'{Environment.C8Y_BASE}/tenant/currentTenant', headers=C8Y_HEADERS)
        logger.debug(f"Connect to tenant {Environment.C8Y_TENANT} successfully")
    except:
        logger.debug(f"Connect to tenant {Environment.C8Y_TENANT} failed")
        sys.exit()

    DATA_TYPE, DEVICE_ID, CREATE_FROM, CREATE_TO = ArgumentsAndCredentialsHandler.argumentsParser()

    createFrom, createTo = SetTimePeriodToExportData(CREATE_FROM, CREATE_TO)
    logger.debug(f"Export data which is created after/from: {createFrom}")
    logger.debug(f"and created before/to: {createTo}")

    if not DEVICE_ID:
        exportAllProfileDataFromChildDevices(c8y, DATA_TYPE, createFrom, createTo)
    else:
        ExportSpecificProfileDataWithDeviceId(c8y, DATA_TYPE, createFrom, createTo, DEVICE_ID)