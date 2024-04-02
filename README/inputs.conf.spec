[apiconnect://<name>]
provider = The vendor who owns the API
api = Enter the name of a pre-configured API provider from the Configuration screen
endpoint = The API URI endpoint
odata_support = true/false
filter = Filter to apply to response
headers = Additional headers in "{key: value, key: value}" format. JSON response is automatically requested.
useproxy = true/false to pass request through configured proxy
limit = Limit the number of results
event_path = Path to the keys used to separate payload into events. Separate keys by forward slashes. Example: value/0/issues
next_type = Location to find results paging key (header, JSON key)
next_key = Key which provides value for paged events
event_time_field = Field to be used for _time extraction
event_time_format = Format of _time field
event_timezone = Timezone to be used for _time extraction
csv_conversion = Events from this TA are written as JSON. If payload is CSV, convert it and set event_key='value'.
checkpoint_support = true/false
checkpoint_type = Field to determine how to filter or drop events
checkpoint_field = Calculated field to be used for limiting results.
checkpoint_tracker = Event field to be used with tracking the latest checkpointer. For keys buried in nested JSON, separate by forward slashes. ie. doc/timestamp
checkpoint_format = Format for checkpoint_field
checkpoint_operator = Comparison operator for filtering events based on prior checkpoint
checkpoint_timezone = Timezone of incoming data
checkpoint_start_date = Date to begin event ingest. Many APIs have a limit. That limit will be enforced over this setting if you set it too far back.
request_window_minutes = If set, will append an event search filter using checkpoint_field's value for start of window and calculating the end of dataset by adding event_window to it
request_delay_throttle_minutes = How close to "now" should a query determine and end date for the search?

[apiconnect]
python.version = python3

