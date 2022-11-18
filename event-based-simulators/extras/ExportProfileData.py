import json, logging, os, sys, requests

import ArgumentsAndCredentialsHandler, Environment

from datetime import datetime, timedelta, timezone

# Global variables and constants
logTimeFormat = "%Y%m%d%H%M%S_%f"
C8Y_PROFILE_GROUP = 'c8y_EventBasedSimulatorProfile'
C8Y_OEE_SIMULATOR_DEVICES_GROUP = "c8y_EventBasedSimulator"
DATA_TYPE, DEVICE_ID_LIST, CREATE_FROM, CREATE_TO, LOG_LEVEL, c8y, PASSWORD = ArgumentsAndCredentialsHandler.HandleExportArguments()
C8Y_HEADERS, MEASUREMENTS_HEADERS = ArgumentsAndCredentialsHandler.SetupHeadersForAPIRequest(tenant_id=c8y.tenant_id, username= c8y.username, password=PASSWORD)
####################################################
# Setup Log
file_log_level = logging.DEBUG
console_log_level = LOG_LEVEL
relativeFilePath = f"logs\export_{datetime.strftime(datetime.now(), logTimeFormat)}.log"
filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
fileLogger, consoleLogger = ArgumentsAndCredentialsHandler.SetupLogger(file_logger_name='ExportProfileData', console_logger_name='ConsoleExportProfileData', filepath=filePath, file_log_level=file_log_level, console_log_level=console_log_level)
def LogDebug(content):
  fileLogger.debug(content)
  consoleLogger.debug(content)
def LogInfo(content):
  fileLogger.info(content)
  consoleLogger.info(content)
def LogError(content):
  fileLogger.error(content)
  consoleLogger.error(content)
#####################################################
# Check if connection to tenant can be created
tenantConnectionResponse = ArgumentsAndCredentialsHandler.CheckTenantConnection(baseUrl=c8y.base_url, C8Y_HEADERS=C8Y_HEADERS)
if tenantConnectionResponse:
    LogInfo(f"Connect to tenant {c8y.tenant_id} successfully")
else:
    if tenantConnectionResponse is None:
        LogError(f"Wrong base url setup. Check again the URL: {c8y.base_url}")
    else:
        LogError(tenantConnectionResponse.json())
    LogError(f"Connect to tenant {c8y.tenant_id} failed")
    sys.exit()
######################################################


def ExportAllProfileDataFromChildDevices(createFrom, createTo):
    deviceInTenantCount = 0
    deviceManagedObject = c8y.device_inventory.select(type=C8Y_OEE_SIMULATOR_DEVICES_GROUP)
    for device in deviceManagedObject:
        deviceInTenantCount += 1
        LogDebug(f"Found device '{device.name}', id: #{device.id}, owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
        LogDebug(f"List of {device.name}'s child devices: ")
        for childDevice in device.child_devices:
            ExportSpecificProfileDataWithDeviceId(createFrom=createFrom,createTo=createTo, deviceId=childDevice.id)

    if deviceInTenantCount == 0:
        LogInfo(f"No device in tenant {c8y.tenant_id} found")


def ExportSpecificProfileDataWithDeviceId(createFrom, createTo, deviceId):
    deviceName = FindDeviceNameById(deviceId, c8y.base_url)
    deviceWithIdCount = 0
    deviceExternalId, deviceExternalIdType = CheckDeviceExternalIdById(deviceId, c8y.base_url)
    if not deviceExternalId:
        return
    if IsExternalIdTypeEventBasedSimulatorProfile(deviceExternalIdType):
        filePath = CreateFilePath(Id=deviceExternalId)
    else:
        return
    LogDebug(f"Search for {DATA_TYPE} data from device {deviceName}, id #{deviceId}")
    for device in c8y.device_inventory.select(name=deviceName):
        deviceWithIdCount += 1
        fileLogger.debug(f"Child device {device.name}, id #{device.id}")
        if DATA_TYPE == "alarms":
            ExportAlarms(device, createFrom, createTo, filePath)
            AppendDataToJsonFile([], filePath, 'measurements')
            fileLogger.debug(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
        elif DATA_TYPE == "measurements":
            # listing measurements of child device
            ExportMeasurements(device, createFrom, createTo, filePath)
            AppendDataToJsonFile([], filePath, 'alarms')
            fileLogger.debug(f"{DATA_TYPE.capitalize()} data is added to data file at {filePath}")
        else:
            ExportAlarms(device, createFrom, createTo, filePath)
            ExportMeasurements(device, createFrom, createTo, filePath)
            fileLogger.debug(f"Alarms and Measurements data is added to data file at {filePath}")

    if deviceWithIdCount == 0:
        fileLogger.info(f"No data for device with id #{deviceId} is exported")
    else:
        LogInfo(f"Exported successfully data for device with id #{deviceId}, external id: {deviceExternalId}")
    return


def FindDeviceNameById(deviceId, baseUrl):
    response = requests.get(f'{baseUrl}/inventory/managedObjects/{deviceId}',
                            headers=C8Y_HEADERS)
    if not response.ok:
        LogError(response.json())
        sys.exit()
    else:
        try:
            deviceName = response.json()['name']
        except:
            LogError(f"Device #{deviceId} does not have name")
            sys.exit()

    return deviceName


def ExportAlarms(device, createFrom, createTo, filePath):
    jsonAlarmsList = ListAlarms(device, createFrom, createTo)
    AppendDataToJsonFile(jsonAlarmsList, filePath, 'alarms')


def ListAlarms(device, createFrom, createTo):
    jsonAlarmsList = []
    for alarm in c8y.alarms.select(source=device.id, created_after=createFrom, created_before=createTo):
        fileLogger.debug(f"Found alarm id #{alarm.id}, severity: {alarm.severity}, time: {alarm.time}, creation time: {alarm.creation_time}, update time : {alarm.updated_time}\n")
        jsonAlarmsList.append(alarm.to_json())
    return jsonAlarmsList


def ExportMeasurements(device, createFrom, createTo, filePath):
    jsonMeasurementsList = ListMeasurements(device, createFrom, createTo)
    AppendDataToJsonFile(jsonMeasurementsList, filePath, 'measurements')


def ListMeasurements(device, createFrom, createTo):
    jsonMeasurementsList = []
    for measurement in c8y.measurements.select(source=device.id, after=createFrom, before=createTo):
        fileLogger.debug(f"Found measurement id #{measurement.id}\n")
        jsonMeasurementsList.append(measurement.to_json())
    return jsonMeasurementsList


def AppendDataToJsonFile(jsonDataList, filePath, data_type, json_data={}):
    # Create new json file or add data to an existing json file
    with open(filePath, 'w') as f:
        json_data[f"{data_type}"] = jsonDataList
        json.dump(json_data, f, indent=2)


def GetExternalIdReponse(deviceId, baseUrl):
    externalIdResponse = requests.get(f'{baseUrl}/identity/globalIds/{deviceId}/externalIds',
                                      headers=C8Y_HEADERS)
    if not externalIdResponse.ok:
        LogError(externalIdResponse.json())
        sys.exit()
    else:
        return externalIdResponse


def CheckDeviceExternalIdById(deviceId, baseUrl):
    externalIdResponse = GetExternalIdReponse(deviceId, baseUrl)

    try:
        deviceExternalId = externalIdResponse.json()['externalIds'][0]['externalId']
        deviceExternalIdType = externalIdResponse.json()['externalIds'][0]['type']
        LogInfo(f"Found external id: {deviceExternalId} with type: {deviceExternalIdType} for the device with id {deviceId}")
    except:
        LogInfo(f"Could not find external id for the device with id {deviceId}")
        return None, None

    return deviceExternalId, deviceExternalIdType


def IsExternalIdTypeEventBasedSimulatorProfile(deviceExternalIdType):
    if deviceExternalIdType == C8Y_PROFILE_GROUP:
        return True
    else:
        LogInfo(f"The type {deviceExternalIdType} of external ID must match with type {C8Y_PROFILE_GROUP}")
        return False


def CreateFilePath(Id):
    # Check if folder containing data files exists and make one if not
    if not os.path.exists('export_data'):
        os.makedirs('export_data')
    relativeFilePath = f'export_data\{Id}.json'
    filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
    fileLogger.debug(f"Created successfully file path: {filePath}")
    return filePath


def SetTimePeriodToExportData():
    if not CREATE_FROM or CREATE_TO:
        LogDebug(f'CREATE_FROM and/or CREATE_TO were not set. Using default setup to export {Environment.PERIOD_TO_EXPORT}{Environment.TIME_UNIT} ago from now')

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
    createFrom, createTo = SetTimePeriodToExportData()
    fileLogger.info(f"Export data which is created after/from: {createFrom}")
    fileLogger.info(f"and created before/to: {createTo}")

    if not DEVICE_ID_LIST:
        ExportAllProfileDataFromChildDevices(createFrom=createFrom, createTo=createTo)
    else:
        for deviceId in DEVICE_ID_LIST:
            ExportSpecificProfileDataWithDeviceId(createFrom=createFrom, createTo=createTo, deviceId=deviceId)
