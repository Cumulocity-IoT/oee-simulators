# Description OEE-Simulators

The OEE-simulators project offers these main features in the [main](main) folder: 
- the **oee-simulators microservice** which creates devices and sends data into Cumulocity IoT.

There are extra features in [extras](extras):
- the **export data** script to export Measurements or/and Alarms from OEE devices into json data files.
- the **import data** script to upload Measurements or/and Alarms from data json file to OEE devices.

## Simulator Microservice
Detailed feature list:
- configuration in JSON, no need to write code.
- automatically creates devices and sends data.
- identifies devices using a configurable `externalId`.
- devices can be disabled to not send any events and measurements.
- Written in python which can be modified easily for further development.

### Simulator definition
The simulators are created in Cumulocity IoT based on the definitions in [simulators.json](main/simulator.json). Those simulators can be used for calculation in the OEE block. The currently supported simulators described [here](simulators.md).

Example for a simulator definition:
```
  [
    {
        "type": "Simulator",
        "id": "sim_001",
        "label": "Normal #1",
        "enabled": true,
        "events": [
            {
                "type": "Availability",
                "minimumPerHour": 5,
                "maximumPerHour": 10,
                "status": ["up", "down"],
                "probabilities": [0.9, 0.1],
                "durations": [0, 0],
                "forceStatusDown": true
            }
        ],
        "measurements": [
            {
                "type": "PumpPressure",
                "fragment": "Pressure",
                "series": "P",
                "unit": "hPa",
                "valueDistribution": "uniform",
                "minimumValue": 1000.0,
                "maximumValue": 1500.0,
                "minimumPerHour": 4.0,
                "maximumPerHour": 4.0
            }
        ]
    }
  ]
```

- the number of **events** and **measurements** **per hour** can be configured as a random number in a range
    ```
    "minimumPerHour": 5,
    "maximumPerHour": 10
    ```
  or using a constant number: 
    ```
    "frequency": 20
    ```
  
- the availability of machine is expressed as probability value `probabilities` with range from 0.0 to 1.0. The `probabilities` is an array which has correspondence with the `status` array.
  ```
    "status": ["up", "down"],
    "probabilities": [0.9, 0.1]
  ```
  In this case, the up status has 90% to happen and the down status has the remaining 10%.

- the timestamp of the following `Piece_ok` event is the same as the corresponding `Piece_Produced` event
  - the expected quality of production is configurable
  ```
    "events": [
      "type": "Piece_Produced",
      "frequency": 25,
      "followedBy": {
          "type": "Piece_Ok",
          "frequency": 20
      }
    ]
  ```
    the expected quality would be 80% (*followedBy.frequency/frequency * 100%*)

- For the `Pieces_Produced`, the simulator produces multiple pieces at a time so the minimum (`piecesMinimumPerProduction`) and maximum pieces per production (`piecesMaximumPerProduction`) must be set
  ```
    "type": "Pieces_Produced",
    "frequency": 6,
    "piecesMinimumPerProduction": 1,
    "piecesMaximumPerProduction": 10,
    "followedBy": {
        "type": "Pieces_Ok",
        "piecesMinimumPerProduction": 0,
        "piecesMaximumPerProduction": 10,
        "frequency": 6
    }
  ```
  - the kind of measurement that should be sent, can be defined by
      ```
      "measurements": [
          "type": "PumpPressure",
          "fragment": "Pressure",
          "series": "P"
      ]
      ```
    where "type" is optional and its default value is the value from the "fragment" property.
  
  - In measurements, `valueDistribution` is defined to let the simulator know which distribution formula to use to generate measurements. There are three choices that can be defined here: `uniform`, `uniformint`, `normal`.

- Simulates shutdowns (no events or measurements are sent if simulator is DOWN)

- the main entry point is the [simulator.py](main/simulator.py) script
  - the script reads the configuration from [simulator.json](main/simulator.json) and creates a new device for every entry (if it does not exist)
  - the `id` property is used as `external_id` for the ManagedObjects to avoid creating multiple devices when redeploying/updating the microservice

### Build the docker image locally

To build the docker image for this microservice, execute:
```
git clone git@github.softwareag.com:IOTA/oee-simulators.git
cd oee-simulators/simulators
docker build -t oee-simulators .
docker save -o image.tar oee-simulators
```
In [cumulocity.json](cumulocity.json), change "version" from "@project.version@" to version number you want in format xx.xx.xx (example: "version": "12.20.11"). If you want to use the same version for multiple uploads, "latest" or "SNAPSHOT" can be used in the last position (example: "version": "12.20.latest").
Then compress both the [cumulocity.json](cumulocity.json) and the newly created [image.tar] files into a ZIP file or execute the command below to create [oee-simulators.zip] file:
```
zip oee-simulators.zip image.tar cumulocity.json 
```
This zip file can then be uploaded as a Microservice to Cumulocity IoT.

### Deployment

To deploy this project, upload the zip file to the Cumulocity as Microservice. The zip file can be created locally as described above or downloaded from the [Releases](https://github.com/SoftwareAG/oee-simulators/releases) section.

### Environment

Install python 3.8.3+ on your system. Probably you'll need install some packages using *pip* command, e.g.
```
pip install requests
```

To run the scripts locally the following variables need to be set as environment variables or in [cumulocityAPI.py](main/cumulocityAPI.py):
```
C8Y_BASEURL=https://test.development.c8y.io 
C8Y_TENANT=t123
C8Y_USER=yourusername
C8Y_PASSWORD=yourpassword
```

Additionally, the following optional/debug variables can be set:
```
MOCK_C8Y_REQUESTS=false
```

- if MOCK_C8Y_REQUESTS is set to true, no requests to the C8Y tenant are executed, but you can see what would have been executed in the log
