# OEE-simulators

Collection of simulators available for [Cumulocity IoT OEE block](https://github.com/Cumulocity-IoT/oee-block). The simulators are available as Docker image and need to be deployed to the tenant where OEE block is running. Once deployed, the simulators automatically create preconfigured devices and start sending data. 

[Generic Simulators](simulators) are the simulators can be used for testing and demoing the Cumulocity IoT OEE block. The simulators have been designed and configured to simulate commonly seen machine types. A detailed description of the [supported machine types](simulators/simulators.md) can be found in the [simulators](simulators) folder.

The prebuilt docker images can be downloaded from the [Releases](https://github.com/Cumulocity-IoT/oee-simulators/releases) in this repository.

# Tests 
Collection of test for the [Generic Simulators](simulators)

To run specific a test script:
```
python test/[script-name].py  [-h] [--tenant-id TENANT_ID] [--password PASSWORD] [--baseurl BASEURL] [--username USER]
```
<pre>
Cumulocity platform credentials setup

optional arguments:<br>
  long syntax                |    short syntax       |   Functions
------------------------------------------------------------------------------------------
  --help,                    |    -h                 |   show help message and exit
  --tenant-id TENANT_ID,     |    -t TENANT_ID       |   Tenant ID
  --password PASSWORD,       |    -p PASSWORD        |   C8Y Password
  --baseurl BASEURL,         |    -b BASEURL         |   C8Y Baseurl
  --username USER,           |    -u USER            |   C8Y Username

It is important to note that <strong><ins>all four arguments: Tenant ID, C8Y Password, C8Y Baseurl, and C8Y Username must be filled</ins></strong>. 
Failure to provide any of these fields may cause the script to malfunction or produce unexpected results.
</pre>

If you don't want to input arguments, you can set environment variables. They need to be set in [cumulocityAPI.py](simulators/main/cumulocityAPI.py) in order to run [simulators_test.py](test/simulators_test.py). <br>
For example:
```
C8Y_BASEURL=https://test.development.c8y.io 
C8Y_TENANT=t123
C8Y_USER=yourusername
C8Y_PASSWORD=yourpassword
```

If you run the [export_import_test.py](test/export_import_test.py), besides environment variables in [cumulocityAPI.py](simulators/main/cumulocityAPI.py), you must set environment variables also in [Environment.py](simulators/extras/Environment.py).
Because they use both [extra](simulators/extras) and [main](simulators/main) parts of simulators which are independent to each other.
<br>

------------------------------

These tools are provided as-is and without warranty or support. They do not constitute part of the Cumulocity GmbH product suite. Users are free to use, fork and modify them, subject to the license agreement. While Cumulocity GmbH welcomes contributions, we cannot guarantee to include every contribution in the master project.
