# Generic scripts information
This scripts folder contains:
- The [Export Script](./ExportData.py) can be used to export a json file for measurements and/or alarms of a device. This json file can then be used later for the import.
- The [Environment File](./Environment.py) is used to set up environment parameters.
- The [Import Script](./ImportData.py) can be used to import alarms and measurements into Cumulocity IoT.

## Setup environment parameters:
Enter necessary configuration in **Environment.py** file\
Credentials:
- base url
- tenant ID 
- username 
- password

Additional parameters:
- data type
- device id
- create from
- create to
- time unit
- period to export

Notice: 
- if **'create from'** and **'create to'** are set, set **'time unit'** and **'period to export'** to **None**, and vice versa.
- if you would like to export all data from every child devices, set **'device id'** to **None**

## Install cumulocity-python-api package
Follow the instructions in: https://github.com/Cumulocity-IoT/cumulocity-python-api

### Installation from PyPI
```shell
pip install c8y_api
```

## Run the export script
If the environment **optional** parameters were not setup, they can be input as arguments when running the script.
```shell
ExportData.py [-h]  [--device-ids DEVICE_ID]
                    [--create-from CREATE_FROM]
                    [--create-to CREATE_TO]
                    [--data-type {measurements,alarms,all}]
                    [--log {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                    [--username USERNAME] [--password PASSWORD]
                    [--baseurl BASEURL] [--tenant-id TENANT-ID]

```
Example:
```shell
python ExportData.py --device-ids 123456 254676 --create-from 2022-11-16T07:39:35.780Z --create-to 2022-11-16T07:49:35.780Z
```

optional arguments:\
  -h, --help : show this help message and exit\
  --device-ids DEVICE_IDS, -i DEVICE_IDS : Input device id / list of device ids\
  --create-from CREATE_FROM, -from CREATE_FROM : Input "create from" milestone\
  --create-to CREATE_TO, -to CREATE_TO : Input "create to" milestone\
  --data-type {measurements,alarms,all}, -d {measurements,alarms,all} : Export "alarms" or "measurements"\
  --log {DEBUG,INFO,WARNING,ERROR,CRITICAL}, -l {DEBUG,INFO,WARNING,ERROR,CRITICAL} : Log-level\
  --username USERNAME, -u USERNAME : C8Y Username\
  --password PASSWORD, -p PASSWORD : C8Y Password\
  --baseurl BASEURL, -b BASEURL : C8Y Baseurl\
  --tenant-id TENANT-ID, -t TENANT-ID : C8Y TenantID\

### Credentials Arguments
Credentials for the C8Y instance can be handed to the script using cli arguments as shown in the example above. The script will try to extract the crendentials from the [Environment File](./Environment.py) if no credentials are presented as arguments.

### Logging
Log-level: five log levels can be set using the --log argument {DEBUG, INFO, WARNING, ERROR, CRITICAL}. From left to right is the decreasing order of log info amount can be seen: DEBUG>INFO>WARNING>ERROR>CRITICAL. For example, if INFO level is set, DEBUG level messages can not be seen.

### Export time period
Input both create-from and create-to to set export time. The time format should be: "%Y-%m-%dT%H:%M:%S.%fZ" (i.e 2022-11-14T13:45:15.893Z)


## Run the import script
 
```shell
ImportData.py [-h]  [--ifiles INPUTFILES] 
                    [--log {DEBUG, INFO, WARNING, ERROR, CRITICAL}] 
                    [--username USERNAME] [--password PASSWORD]
                    [--baseurl BASEURL] [--tenant-id TENANT-ID]
```
Example:
```shell
python ImportData.py --ifiles sim_001 sim_002 --log DEBUG --username admin --password abcxzy123
```
### INPUTFILE 
Filename (without extension "json") of one or multiple input file can be input. For example: ```sim_001 sim_002```.\
If the inputfile is not defined, all the json data files in export_data folder will be imported.

### Credentials Arguments
Credentials for the C8Y instance can be handed to the script using cli arguments as shown in the example above. The script will try to extract the credentials from the [Environment File](./Environment.py) if no credentials are presented as arguments.

### Logging
Log-level: five log levels can be set using the --log argument {DEBUG, INFO, WARNING, ERROR, CRITICAL}. From left to right is the decreasing order of log info amount can be seen: DEBUG>INFO>WARNING>ERROR>CRITICAL. For example, if INFO level is set, DEBUG level messages can not be seen.


The schema of the inputfile is:
```json
{
  "alarms":[],
  "measurements":[]
}
```
Example files can be found [here](./export_data/).