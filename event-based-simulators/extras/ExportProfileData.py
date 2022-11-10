import base64
import json
import logging
import os
import sys

import requests

import ArgumentsAndCredentialsHandler
import Environment

from datetime import datetime, timedelta, timezone
from os.path import isfile, join

####################################################
if not os.path.exists('logs'):
    os.makedirs('logs')
logger = logging.getLogger('ExportImportProfileData')
relativeFilePath = f"logs\log{datetime.strftime(datetime.now(), '%Y%m%d%H%M%S_%f')}.log"
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


#####################################################


def exportAllProfileData(c8y, DATA_TYPE, createFrom, createTo):
    # Loop through the list of device in Device management
    try:
        for device in c8y.device_inventory.select(type="c8y_EventBasedSimulator"):
            logger.info(f"Found device '{device.name}', id: #{device.id}, "
                        f"owned by {device.owner}, number of children: {len(device.child_devices)}, type: {device.type}")
            logger.info(f"List of {device.name}'s child devices: ")
            for childDevice in device.child_devices:
                logger.info(f"Child device {childDevice.name}, id #{childDevice.id}")
                filePath = createFilePathFromExternalId(childDevice.id)
                if DATA_TYPE == "alarms":
                    jsonAlarmsList = listAlarms(c8y, childDevice, createFrom, createTo, DATA_TYPE, filePath)
                    appendDataToJsonFile(jsonAlarmsList, filePath, DATA_TYPE)
                elif DATA_TYPE == "measurements":
                    # listing measurements of child device
                    jsonMeasurementsList = listMeasurements(c8y, childDevice, createFrom, createTo, DATA_TYPE, filePath)
                    appendDataToJsonFile(jsonMeasurementsList, filePath, DATA_TYPE)
                else:
                    jsonAlarmsList = listAlarms(c8y, device, createFrom, createTo, DATA_TYPE, filePath)
                    appendDataToJsonFile(jsonAlarmsList, filePath, DATA_TYPE)
                    jsonMeasurementsList = listMeasurements(c8y, childDevice, createFrom, createTo, DATA_TYPE, filePath)
                    appendDataToJsonFile(jsonMeasurementsList, filePath, DATA_TYPE)
    except:
        logger.error(
            "Connection to Cumulocity platform failed. Check your required parameter in environment file again")
        sys.exit()


def ExportSpecificProfileDataWithDeviceId(c8y, DATA_TYPE, createFrom, createTo, DEVICE_ID):
    try:
        response = requests.get(f'{Environment.C8Y_BASE}/inventory/managedObjects/{DEVICE_ID}',
                                headers=C8Y_HEADERS)
        deviceName = response.json()['name']
    except:
        logger.error(
            "Connection to Cumulocity platform failed. Check your required parameter in environment file again")
        sys.exit()

    deviceCount = 0
    filePath = createFilePathFromExternalId(DEVICE_ID)
    logger.info(f"Search for {DATA_TYPE} data from device {DEVICE_ID} ")
    for device in c8y.device_inventory.select(name=deviceName):
        deviceCount += 1
        logger.info(f"Child device {device.name}, id #{device.id}")
        if DATA_TYPE == "alarms":
            jsonAlarmsList = listAlarms(c8y, device, createFrom, createTo, DATA_TYPE, filePath)
            appendDataToJsonFile(jsonAlarmsList, filePath, DATA_TYPE)
            appendEmptyDataToJsonFile(filePath, 'measurements')
        elif DATA_TYPE == "measurements":
            # listing measurements of child device
            jsonMeasurementsList = listMeasurements(c8y, device, createFrom, createTo, DATA_TYPE, filePath)
            appendDataToJsonFile(jsonMeasurementsList, filePath, DATA_TYPE)
            appendEmptyDataToJsonFile(filePath, 'alarms')
        else:
            jsonAlarmsList = listAlarms(c8y, device, createFrom, createTo, 'alarms', filePath)
            appendDataToJsonFile(jsonAlarmsList, filePath, 'alarms')
            jsonMeasurementsList = listMeasurements(c8y, device, createFrom, createTo, 'measurements', filePath)
            appendDataToJsonFile(jsonMeasurementsList, filePath, 'measurements')

    if deviceCount == 0:
        logger.deug(f"No device with id {DEVICE_ID} found")


def listAlarms(c8y, device, createFrom, createTo, DATA_TYPE, filePath, jsonAlarmsList=[]):
    # Create a count variable as a json/dict key to save json data
    count = 0
    for alarm in c8y.alarms.select(source=device.id, created_after=createFrom, created_before=createTo):
        logger.info(
            f"Found alarm id #{alarm.id}, severity: {alarm.severity}, time: {alarm.time}, creation time: {alarm.creation_time}, update time : {alarm.updated_time}\n")
        count += 1
        jsonAlarmsList.append(alarm.to_json())
    return jsonAlarmsList


def listMeasurements(c8y, device, createFrom, createTo, DATA_TYPE, filePath, jsonMeasurementsList=[]):
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


def appendEmptyDataToJsonFile(filePath, data_type, json_data={}):
    with open(filePath, 'w') as f:
        json_data[f"{data_type.capitalize()}"] = []
        json.dump(json_data, f, indent=2)


def createFilePathFromExternalId(deviceId):
    externalIdResponse = requests.get(f'{Environment.C8Y_BASE}/identity/globalIds/{deviceId}/externalIds',
                                      headers=C8Y_HEADERS)
    deviceExternalId = externalIdResponse.json()['externalIds'][0]['externalId']
    # Check if folder containing data files exists and make one if not
    if not os.path.exists('export_data'):
        os.makedirs('export_data')
    relativeFilePath = f'export_data\{deviceExternalId}.json'
    filePath = os.path.join(os.path.dirname(__file__), relativeFilePath)
    logger.info(filePath)
    return filePath


def checkFileList():
    if not os.path.exists('export_data'):
        logger.debug("No folder with name export_data")
    else:
        onlyfiles = [f for f in os.listdir('export_data') if isfile(join('export_data', f))]
        return onlyfiles


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
    DATA_TYPE, DEVICE_ID, CREATE_FROM, CREATE_TO = ArgumentsAndCredentialsHandler.argumentsParser()

    createFrom, createTo = SetTimePeriodToExportData(CREATE_FROM, CREATE_TO)
    logger.debug(f"Export data which is created after/from: {createFrom}")
    logger.debug(f"and created before/to: {createTo}")

    if not DEVICE_ID:
        exportAllProfileData(c8y, DATA_TYPE, createFrom, createTo)
    else:
        ExportSpecificProfileDataWithDeviceId(c8y, DATA_TYPE, createFrom, createTo, DEVICE_ID)