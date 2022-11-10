### Required
C8Y_BASE = 'http://localhost:8080'
C8Y_TENANT = 't100'
C8Y_USER = 'test'
C8Y_PASSWORD = 'test'

### Optional
# Input None if not set
ACTION = 'export'  # 'import': upload json file in export_data to c8y, 'export': export data from c8y to json file
DATA_TYPE = 'measurements'  # 'alarms': export alarms data, 'measurements': export measurements data, 'all' export both
DEVICE_ID = '975560'

# Set one of these two sections and None to all of the others
############################
# Extract data with periods#
############################
TIME_UNIT = 'days'  # weeks, days, hours, minutes, seconds
PERIOD_TO_EXPORT = 4
####################################
# Extract data with exact milestone#
####################################
CREATE_FROM = None
CREATE_TO = None