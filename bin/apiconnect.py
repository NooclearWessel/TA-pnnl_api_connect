from __future__ import print_function
import os, sys, json, re, base64
from sys import platform
import datetime, pytz, time
from dateutil.parser import parse
from dateutil.tz import tzlocal

# TA-specific and PNNL custom libraries
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from splunklib.modularinput import *
from pnnllib.logging import *
from pnnllib.apirequests import apiGET, oauthV2
from pnnllib.checkpoint import getCheckpointFile, readCheckpoint, writeCheckpoint
from pnnllib.apivariables import getDateVariable
from pnnllib.datetimeutils import * 
from pnnllib.datautils import convertCSVtoJSON, getCodec, getNestedValue

class APIConnect(Script):

	def get_scheme(self):
		scheme = Scheme("Modular Input for APIs")

		scheme.description = "Issues queries against configured APIs"
		scheme.use_external_validation = True
		scheme.use_single_instance = False

		api_argument = Argument("api")
		api_argument.title = "Configuration"
		api_argument.data_type = Argument.data_type_string
		api_argument.description = "Selected API configuration"
		api_argument.required_on_create = True
		scheme.add_argument(api_argument)

		endpoint_argument = Argument("endpoint")
		endpoint_argument.title = "URI Endpoint"
		endpoint_argument.data_type = Argument.data_type_string
		endpoint_argument.description = "API endpoint to query"
		endpoint_argument.required_on_create = True
		scheme.add_argument(endpoint_argument)

		odata_support_argument = Argument("odata_support")
		odata_support_argument.title = "OData Support"
		odata_support_argument.data_type = Argument.data_type_string
		odata_support_argument.description = "True/False"
		odata_support_argument.required_on_create = True
		scheme.add_argument(odata_support_argument)

		filter_argument = Argument("filter")
		filter_argument.title = "Filter"
		filter_argument.data_type = Argument.data_type_string
		filter_argument.description = "API filter"
		filter_argument.required_on_create = False
		scheme.add_argument(filter_argument)

		headers_argument = Argument("headers")
		headers_argument.title = "Headers"
		headers_argument.data_type = Argument.data_type_string
		headers_argument.description = "Additional headers in \"{key: value, key: value}\" format. JSON response is automatically requested."
		headers_argument.required_on_create = False
		scheme.add_argument(headers_argument)

		next_type_argument = Argument("next_type")
		next_type_argument.title = "Next Link Type"
		next_type_argument.data_type = Argument.data_type_string
		next_type_argument.description = "Location to find results paging key (header, JSON key)"
		next_type_argument.required_on_create = False
		scheme.add_argument(next_type_argument)

		next_key_argument = Argument("next_key")
		next_key_argument.title = "Next Link Key"
		next_key_argument.data_type = Argument.data_type_string
		next_key_argument.description = "JSON key that provides paging link"
		next_key_argument.required_on_create = False
		scheme.add_argument(next_key_argument)

		limit_argument = Argument("limit")
		limit_argument.title = "Limit"
		limit_argument.data_type = Argument.data_type_string
		limit_argument.description = "Limits the number of results returned"
		limit_argument.required_on_create = False
		scheme.add_argument(limit_argument)

		event_time_field_argument = Argument("event_time_field")
		event_time_field_argument.title = "Event Time Field"
		event_time_field_argument.data_type = Argument.data_type_string
		event_time_field_argument.description = "Field to be used for _time extraction"
		event_time_field_argument.required_on_create = False
		scheme.add_argument(event_time_field_argument)

		event_time_format_argument = Argument("event_time_format")
		event_time_format_argument.title = "Event Time Format"
		event_time_format_argument.data_type = Argument.data_type_string
		event_time_format_argument.description = "strftime format of _time field"
		event_time_format_argument.required_on_create = False
		scheme.add_argument(event_time_format_argument)

		event_timezone_argument = Argument("event_timezone")
		event_timezone_argument.title = "Event Timezone"
		event_timezone_argument.data_type = Argument.data_type_string
		event_timezone_argument.description = "Timezone to be used for _time extraction"
		event_timezone_argument.required_on_create = False
		scheme.add_argument(event_timezone_argument)

		checkpoint_support_argument = Argument("checkpoint_support")
		checkpoint_support_argument.title = "Checkpoints Supported"
		checkpoint_support_argument.data_type = Argument.data_type_string
		checkpoint_support_argument.description = "True/False"
		checkpoint_support_argument.required_on_create = True
		scheme.add_argument(checkpoint_support_argument)

		checkpoint_type_argument = Argument("checkpoint_type")
		checkpoint_type_argument.title = "Checkpoint Type"
		checkpoint_type_argument.data_type = Argument.data_type_string
		checkpoint_type_argument.description = "Field to determine how to filter or drop events"
		checkpoint_type_argument.required_on_create = False
		scheme.add_argument(checkpoint_type_argument)

		checkpoint_field_argument = Argument("checkpoint_field")
		checkpoint_field_argument.title = "Checkpoints Field"
		checkpoint_field_argument.data_type = Argument.data_type_string
		checkpoint_field_argument.description = "Calculated field to be used for limiting results"
		checkpoint_field_argument.required_on_create = False
		scheme.add_argument(checkpoint_field_argument)

		checkpoint_tracker_argument = Argument("checkpoint_tracker")
		checkpoint_tracker_argument.title = "Checkpoints Tracker"
		checkpoint_tracker_argument.data_type = Argument.data_type_string
		checkpoint_tracker_argument.description = "Event field to be used with tracking the latest checkpointer. For keys buried in nested JSON, separate by forward slashes. ie. doc/timestamp"
		checkpoint_tracker_argument.required_on_create = False
		scheme.add_argument(checkpoint_tracker_argument)

		checkpoint_operator_argument = Argument("checkpoint_operator")
		checkpoint_operator_argument.title = "Checkpoints Operator"
		checkpoint_operator_argument.data_type = Argument.data_type_string
		checkpoint_operator_argument.description = "Comparison operator for filtering events based on prior checkpoint"
		checkpoint_operator_argument.required_on_create = False
		scheme.add_argument(checkpoint_operator_argument)

		checkpoint_format_argument = Argument("checkpoint_format")
		checkpoint_format_argument.title = "Checkpoint Field Format"
		checkpoint_format_argument.data_type = Argument.data_type_string
		checkpoint_format_argument.description = "Field format to use when working with checkpointer"
		checkpoint_format_argument.required_on_create = False
		scheme.add_argument(checkpoint_format_argument)

		checkpoint_timezone_argument = Argument("checkpoint_timezone")
		checkpoint_timezone_argument.title = "Checkpoints Timezone"
		checkpoint_timezone_argument.data_type = Argument.data_type_string
		checkpoint_timezone_argument.description = "Timezone of incoming data"
		checkpoint_timezone_argument.required_on_create = False
		scheme.add_argument(checkpoint_timezone_argument)

		checkpoint_start_date_argument = Argument("checkpoint_start_date")
		checkpoint_start_date_argument.title = "Checkpoints Timezone"
		checkpoint_start_date_argument.data_type = Argument.data_type_string
		checkpoint_start_date_argument.description = "Date to begin event ingest. Many APIs have a limit. That limit will be enforced over this setting if you set it too far back."
		checkpoint_start_date_argument.required_on_create = True
		scheme.add_argument(checkpoint_start_date_argument)

		request_window_minutes_argument = Argument("request_window_minutes")
		request_window_minutes_argument.title = "Request Window (minutes)"
		request_window_minutes_argument.data_type = Argument.data_type_string
		request_window_minutes_argument.description = "If set, will append an event search filter using checkpoint_field's value for start of window and calculating the end of dataset by adding event_window to it"
		request_window_minutes_argument.required_on_create = False
		scheme.add_argument(request_window_minutes_argument)

		request_delay_throttle_minutes_argument = Argument("request_delay_throttle_minutes")
		request_delay_throttle_minutes_argument.title = "Request Delay Throttle (minutes)"
		request_delay_throttle_minutes_argument.data_type = Argument.data_type_string
		request_delay_throttle_minutes_argument.description = "How close to 'now' should a query determine and end time filter? This will add a delay to the ending timestamp window to prevent pulling back data that has not yet loaded in the API"
		request_delay_throttle_minutes_argument.required_on_create = False
		scheme.add_argument(request_delay_throttle_minutes_argument)

		event_path_argument = Argument("event_path")
		event_path_argument.title = "Event Path"
		event_path_argument.data_type = Argument.data_type_string
		event_path_argument.description = "Path to the keys used to separate payload into events. Separate keys by forward slashes. Example: value/0/issues"
		event_path_argument.required_on_create = False
		scheme.add_argument(event_path_argument)

		csv_conversion_argument = Argument("csv_conversion")
		csv_conversion_argument.title = "CSV Response"
		csv_conversion_argument.data_type = Argument.data_type_string
		csv_conversion_argument.description = "Converts CSV to JSON before ingestion"
		csv_conversion_argument.required_on_create = False
		scheme.add_argument(csv_conversion_argument)

		useproxy_argument = Argument("useproxy")
		useproxy_argument.title = "Use Proxy"
		useproxy_argument.data_type = Argument.data_type_string
		useproxy_argument.description = "True/False"
		useproxy_argument.required_on_create = True
		scheme.add_argument(useproxy_argument)

		return scheme

	def validate_input(self, validation_definition):

		empty_set = ["", "undefined", None]

		# Get the values of the parameters, and construct a URL for the Github API
		api = validation_definition.parameters["api"]
		endpoint = validation_definition.parameters["endpoint"]
		odata_support = validation_definition.parameters["odata_support"]
		filter = validation_definition.parameters["filter"]
		headers = validation_definition.parameters["headers"]
		next_type = validation_definition.parameters["next_type"]
		next_key = validation_definition.parameters["next_key"]
		limit = validation_definition.parameters["limit"]	
		event_time_field = validation_definition.parameters["event_time_field"]
		event_time_format = validation_definition.parameters["event_time_format"]
		event_timezone = validation_definition.parameters["event_timezone"]
		checkpoint_support = validation_definition.parameters["checkpoint_support"]
		checkpoint_type = validation_definition.parameters["checkpoint_type"]
		checkpoint_start_date = validation_definition.parameters["checkpoint_start_date"]
		checkpoint_field = validation_definition.parameters["checkpoint_field"]
		checkpoint_tracker = validation_definition.parameters["checkpoint_tracker"]
		checkpoint_operator = validation_definition.parameters["checkpoint_operator"]
		checkpoint_format = validation_definition.parameters["checkpoint_format"]
		checkpoint_timezone = validation_definition.parameters["checkpoint_timezone"]
		request_window_minutes = validation_definition.parameters["request_window_minutes"]
		request_delay_throttle_minutes =  validation_definition.parameters["request_delay_throttle_minutes"]
		useproxy = validation_definition.parameters["useproxy"]

		if api in empty_set:
			raise ValueError("Select an API")

		# if credential in empty_set:
		# 	raise ValueError("Select a credential")
		if next_type not in empty_set:
			if next_key in empty_set: 
				raise ValueError("Enter a value for finding the paged link")

		if checkpoint_support == True:
			if checkpoint_start_date != datetime.datetime.strptime(checkpoint_start_date, "%Y-%m-%d").strftime('%Y-%m-%d'):
				raise ValueError("Start Date must be in YYYY-MM-DD format. Received {0}".format(checkpoint_start_date))
			
			if checkpoint_type in empty_set: 
				raise ValueError("Enter checkpoint type")
						
			if checkpoint_field in empty_set and checkpoint_type == "ef": 
				raise ValueError("Enter Endpoint Filter field")
			
			if checkpoint_field in empty_set and checkpoint_type == "of":
				raise ValueError("Enter OData Filter field")
			
			if checkpoint_tracker in empty_set:
				raise ValueError("Enter checkpointer field")

			if checkpoint_operator in empty_set:
				raise ValueError("Select checkpoint operator")

			if checkpoint_format in empty_set:
				raise ValueError("Enter checkpointer field formatting in python epoch format")
			
			if checkpoint_timezone in empty_set:
				raise ValueError("Select checkpoint field timezon")
			
			if request_window_minutes not in empty_set:
				if not request_window_minutes.isdigit():
					raise ValueError("Window size should be an integer for number of minutes")
				
			if request_delay_throttle_minutes not in empty_set:
				if not request_delay_throttle_minutes.isdigit():
					raise ValueError("Delay Throttle should be an integer for number of minutes")

		if limit not in empty_set:
			if not limit.isdigit():
				raise ValueError("Limit should be an integer")

		#Need to add external validation script

	def stream_events(self, inputs, ew):
		try:

			global logging, log_props, endpoint_filter, odata_filter, event_drop_filter
			endpoint_filter = "ef"
			odata_filter = "of"
			event_drop_filter = "ed"
			checkpoint_filters = [endpoint_filter, odata_filter]

			ta_name = "TA-pnnl_api_connect"
			api_configs_conf = "api_configs"
			variables_conf = "api_variables"
			props_time_format = "%Y-%m-%dT%H:%M:%S.%f"
			empty_set = ["", "undefined", None]

			# Go through each input for this modular input
			for input_name, input_item in list(inputs.inputs.items()):

				# Build a logger for this sourcetype (TA name + sourcetype)
				# Example: TA-pnnl_api_connect_microsoft_getemailactivitycounts_csv
				log_source = re.sub(r"://|\s+","_",input_name.lower())
				logging = setup_logging("TA-pnnl_api_connect_"+log_source)
				
				# Build properties for modinput logging
				job_time = time.time()
				job_id = (ta_name +"_"+ log_source +"_"+ str(job_time))
				job_id=	re.sub(r"\s+|\.", "", job_id)
				
				log_props="input_name=\"{0}\" job_id=\"{1}\"".format(input_name, job_id)

				log_info(logging, log_props, "Start", "Begin import process")

				### DATE/TIME CONFIGURATION ###
				if "event_timezone" in input_item and input_item["event_timezone"] not in empty_set:
					events_timezone_label = input_item["event_timezone"]
					if input_item["event_timezone"] == "local":
						event_timezone = None
					elif input_item["event_timezone"].upper() == "UTC":
						event_timezone = pytz.timezone("UTC")
					else:
						event_timezone = pytz.timezone(str(input_item["event_timezone"]))
					log_info(logging, log_props, "Running", "Events received will be from the {0} timezone".format(events_timezone_label))
				else:
					event_timezone = None
					log_info(logging, log_props, "Running", "No event timezone defined. Defaulting to local")

				### CHECKPOINT CONFIGURATION ###
				checkpoint_type = None
				checkpoint_filter = None
				checkpoint_field = None
				checkpoint_tracker = None
				checkpoint_operator = None
				search_start_datetime = None
				end_date = None

				#If checkpointing has been enabled, build the filters now
				if input_item["checkpoint_support"].lower() in ["t", "true", "1"]:
					log_info(logging, log_props, "Running", "Begin checkpoint configuration")

					if "checkpoint_type" in input_item and input_item["checkpoint_type"] not in empty_set:
						checkpoint_type = input_item["checkpoint_type"]
					else:
						log_error_quit(logging, log_props, "Checkpoint for modinput has been selected but no checkpoint type has been configured")

					if "checkpoint_field" in input_item and input_item["checkpoint_field"] not in empty_set and checkpoint_type in checkpoint_filters:
						checkpoint_field = input_item["checkpoint_field"]
					else:
						log_error_quit(logging, log_props, "Checkpoint for modinput has been selected but no valid checkpoint filter field entered")

					if "checkpoint_operator" in input_item and input_item["checkpoint_operator"] not in empty_set:
						# Calculate the checkpoint_operator format based on the checkpointer type. Not needed for Event Drop.
						if checkpoint_type in checkpoint_filters:
							if checkpoint_type == endpoint_filter:
								if input_item["checkpoint_operator"] == "eq":
									checkpoint_operator = "="
								elif input_item["checkpoint_operator"] == "gt":
									checkpoint_operator = ">"
								else:
									checkpoint_operator = ">="
							else:
								checkpoint_operator = input_item["checkpoint_operator"]
					else:
						log_error_quit(logging, log_props, "Checkpoint Operator missing")

					if "checkpoint_tracker" in input_item and input_item["checkpoint_tracker"] not in empty_set:
						checkpoint_tracker = input_item["checkpoint_tracker"]
					else:
						log_error_quit(logging, log_props, "Checkpoint for modinput has been selected but no checkpoint tracker field entered")

					if "checkpoint_format" in input_item and input_item["checkpoint_format"] not in empty_set:
						checkpoint_format = input_item["checkpoint_format"] 
					else:
						log_error_quit(logging, log_props, "Checkpoint for modinput has been selected but no checkpoint filter has been provided for field {0}".format(checkpoint_field))

					if "checkpoint_timezone" in input_item and input_item["checkpoint_timezone"] not in empty_set:
						if input_item["checkpoint_timezone"]  == "local":
							# checkpoint_timezone = pytz.timezone(str(getLocalTZ()))
							checkpoint_timezone = None
						elif input_item["checkpoint_timezone"] .upper() == "UTC":
							checkpoint_timezone = pytz.timezone("UTC")
						else:
							checkpoint_timezone = pytz.timezone(str(input_item["checkpoint_timezone"] ))
					else:
						log_info(logging, log_props, "Running", "Checkpoint for modinput has not been selected. Defaulting to UTC.")
						# checkpoint_timezone = "utc"
						checkpoint_timezone = pytz.timezone("UTC")

					log_info(logging, log_props, "Running", "Finding input checkpoint file")
					checkpoint_file = getCheckpointFile(inputs, "checkpoint_"+input_name.replace("://","_"))

					#Checkpoints are stored in epoch time format
					prior_checkpoint_epoch = readCheckpoint(checkpoint_file)
					
					log_info(logging, log_props, "Running", "Calculating beginning checkpoint")
					#Calculate a human readable checkpoint using the provided checkpoint_format
					search_start_datetime = _calculate_start(checkpoint_type, prior_checkpoint_epoch, input_item["checkpoint_start_date"], checkpoint_format, checkpoint_timezone)

					# Construct the checkpoint to append to the URL
					if checkpoint_type == odata_filter:
						# Checkpoint type is OData Filter. Construct the formatting.
						checkpoint_filter = checkpoint_field+"%20"+checkpoint_operator+"%20"+str(search_start_datetime)
					elif checkpoint_type == endpoint_filter:
						# Checkpoint type is Endpoint Filter.
						checkpoint_filter = checkpoint_field+str(checkpoint_operator)+str(search_start_datetime)

					if not prior_checkpoint_epoch in ["", None]:
						if checkpoint_type in checkpoint_filters:
							log_info(logging, log_props, "Running", "Setting API filter based on prior checkpoint: {0}".format(checkpoint_filter))
						else:
							log_info(logging, log_props, "Running", "Setting event drop based on prior checkpoint: {0}".format(search_start_datetime))							
					elif not input_item["checkpoint_start_date"] in ["", None]:
						if checkpoint_type == odata_filter or checkpoint_type == endpoint_filter:
							log_info(logging, log_props, "Running", "No starting checkpoint set. Calculating filter start date from modinput value: {0}".format(checkpoint_filter))
						else:
							log_info(logging, log_props, "Running", "No starting checkpoint set. Calculating start date from modinput value: {0}".format(search_start_datetime))
					else:
						log_info(logging, log_props, "Running", "No prior checkpoint set. Indexing all events.")

					# Build end date filter if request_window_minutes is provided
					if "request_window_minutes" in input_item and input_item["request_window_minutes"] not in empty_set:
						end_date = str(addMinutesToDateTime(search_start_datetime, checkpoint_format, input_item["request_window_minutes"]))
						log_info(logging, log_props, "Running", "Calculated end date using request window of {0} minutes as {1}".format(input_item["request_window_minutes"], end_date))
					else:
						log_info(logging, log_props, "Running", "Request window not defined. Skipping...")
					
					#  Apply end date filter modifiers using delay throttle
					if "request_delay_throttle_minutes" in input_item and input_item["request_delay_throttle_minutes"] not in empty_set:
						if end_date not in empty_set:
							# If an end_date has already been calculated, push it back by the number request_window_minutes				
							end_date = str(subtractMinutesFromDateTime(end_date, checkpoint_format, input_item["request_delay_throttle_minutes"]))
							log_info(logging, log_props, "Running", "Modified request window end date using delay throttle of {0} minutes as {1}".format(input_item["request_delay_throttle_minutes"], end_date))
						else:
							# If an end_date has not already been calculated because request_window_minutes was not specified, assume this is the end date and calculate based on start date
							end_date = str(addMinutesToDateTime(search_start_datetime, checkpoint_format, input_item["request_delay_throttle_minutes"]))
							log_info(logging, log_props, "Running", "Calculated end date using delay throttle of {0} minutes as {1}".format(input_item["request_delay_throttle_minutes"], end_date))
						
						if checkpoint_type == odata_filter:
							checkpoint_filter += "%20and%20" + checkpoint_field + "%20lt%20" + end_date
						# else ---> Need to add an ending field entry for Endpoint Filtering
					else:
						if checkpoint_type == odata_filter:
							log_info(logging, log_props, "Running", "Delay Throttle not defined. Searching with filter {0}".format(checkpoint_filter))
						else:
							log_info(logging, log_props, "Running", "Delay Throttle not defined. Running with calculated checkpointer {0}".format(search_start_datetime))
				
					if checkpoint_type == odata_filter or checkpoint_type == endpoint_filter :
						log_info(logging, log_props, "Running", "Calculated final API checkpoint filter {0}".format(checkpoint_filter))
					else:
						log_info(logging, log_props, "Running", "Calculated event drop filter beginning with events older than {0}".format(checkpoint_filter))
						if end_date not in empty_set:
							log_info(logging, log_props, "Running", "Calculated ending event drop filter for events newer than {0}".format(end_date))

					update_checkpoint = True

				else:
					log_info(logging, log_props, "Running", "Input not configured to use checkpointer")
					update_checkpoint = False

				### ENDPOINT CONFIGURATION ###
				endpoint = ""
				if "endpoint" in input_item and input_item["endpoint"] not in empty_set:
					endpoint=input_item["endpoint"]
					endpointVariables = re.findall(r'{{(.*?)}}', endpoint)
					count=0

					for endpointVariable in endpointVariables:
						found = False
						count+=1
						splitVariable = endpointVariable.split(",")
						variable = splitVariable[0]

						for stanza in self.service.confs[variables_conf]:
							if stanza.name == variable:
								found = True
								content=json.loads(json.dumps(stanza.content))

								if content["type"] == "date":
									if splitVariable[1] not in empty_set:
										modifier = re.search(r'\[(.*?)\]', splitVariable[1]).group(1)
									else:
										modifier = 0
			
									formatted_date = getDateVariable(content["format"], "utc", modifier)
									endpoint = endpoint.replace("{{"+endpointVariable+"}}", formatted_date)

							log_info(logging, log_props, "Running", "Endpoint after variable substitutions: {0}".format(endpoint))

						if found == False:
							log_error_quit(logging, log_props, "Variable {0} has not been configured in {1}}".format(variable, variables_conf))

				### URL FILTER CONFIGURATION ###
				# Begin the filter string build by defining the prefix and suffix of the final result
				if checkpoint_type is not None:
					if checkpoint_type == odata_filter:
						filter_text = "$filter="
					else:
						filter_text = ""

					if checkpoint_type == odata_filter and "$expand=" in endpoint:
						filter_prefix = "(" + filter_text
						filter_suffix = ")"
					else:
						if "?" in endpoint:
							filter_prefix = "&" + filter_text
						else:
							filter_prefix = "?" + filter_text
					filter_suffix = ""
				else:
					filter_prefix = ""
					filter_suffix = ""

				# Construct the final API filter string
				if input_item["odata_support"].lower() in ["t", "true", "1"]:
					log_info(logging, log_props, "Running", "Starting OData-based filter configuration")
					if "filter" in input_item and input_item["filter"] not in empty_set:
						filter = filter_prefix + input_item["filter"]
					else:
						filter = filter_prefix

					if checkpoint_type == odata_filter and checkpoint_filter is not None:
						filter += "%20" + checkpoint_filter + filter_suffix
					else:
						filter = filter + filter_suffix
					log_info(logging, log_props, "Running", "Finished OData-based filter configuration: {0}".format(filter))
				elif checkpoint_type == endpoint_filter:
					log_info(logging, log_props, "Running", "Starting endpoint-based filter configuration")
					if checkpoint_filter is not None:
						filter = filter_prefix + checkpoint_filter + filter_suffix					
						log_info(logging, log_props, "Running", "Applying checkpoint filter to URL {0}".format(filter))
				else:
					filter = None
					log_info(logging, log_props, "Running", "No API-based filtering will be applied to URL.")

				if "limit" in input_item and input_item["limit"] not in empty_set:
					limit = input_item["limit"]
				else:
					limit = None

				### PROXY CONFIGURATION ###
				proxies = {}
				if input_item["useproxy"] is not None and input_item["useproxy"].lower() in ['t', 'true']:
					for stanza in self.service.confs["api_proxy"]:
						content=json.loads(json.dumps(stanza.content))
						if "proxyurl" in content and content["proxyurl"] is not None:
							proxies[stanza.name] = content["proxyurl"]
						else:
							log_error_quit(logging, log_props, "useproxy was requested but proxy has not been configured properly")

					log_info(logging, log_props, "Running", "Using proxy configuration {0}".format(proxies))

				### API AND AUTHENTICATION CONFIGURATION ###
				secret = None
				cookies = None

				#Loop through defined providers until the one used by the modinput is found. Use that information to build connection information
				log_info(logging, log_props, "Running", "Begin looping providers")

				for stanza in self.service.confs[api_configs_conf]:
					if stanza.name == input_item["api"]:
						content=json.loads(json.dumps(stanza.content))

						authtype=content["authtype"]
						log_info(logging, log_props, "Running", "Authentication type {0} specified".format(authtype))

						# Configure Basic Auth package. Will build the basic authentication header to send with the request.
						if authtype == "Basic Auth":
							secret = _getSecret(self, str(input_item["api"] +":"+ content["username"] +":"))
							if secret is not None:
								log_info(logging, log_props, "Running", "Basic Auth secret found")
							else:
								log_error_quit(logging, log_props, "Requested api secret has not been configured for basic auth {0}".format(self.api))

							# Create a base64 encoded string to pass in the Authorization header
							cred = content["username"] + ":" + secret
							cred64 = base64.b64encode(cred.encode()).decode()
							headers = {"Authorization": "Basic %s" % cred64}

						# Configure Basic Auth package. Will build headers. If auth URL provided, will get a session cookie to pass to requests.
						if authtype == "Header Auth":
							if "usernamekey" in content and content["usernamekey"] not in empty_set:
								usernamekey=content["usernamekey"]
							else:
								usernamekey="username"
							if "secretkey" in content and content["secretkey"] not in empty_set:
								secretkey=content["secretkey"]
							else:
								secretkey="password"
							secret = _getSecret(self, str(input_item["api"] +":"+ content["username"] +":"))
							if secret is not None:
								log_info(logging, log_props, "Running", "Header Auth secret found")

							if "authdomain" in content and content["authdomain"] not in empty_set:
								headers = {usernamekey: content["authdomain"]+ "\\" + content["username"], secretkey: secret}
							else:
								headers = {usernamekey: content["username"], secretkey: secret}

							if "authurl" in content and content["authurl"] not in empty_set:
								log_info(logging, log_props, "Running", "Performing cookie-based authentication")
								# Get a session cookie and use that for logins
								response = apiGET(url=content["authurl"], proxies=proxies, headers=headers)
								if response.status_code != 200:
									log_error_quit(logging, log_props, "Cookie authentication request to {0} failed with status code {1}".format(content["authurl"], response.status_code))
								else:
									log_info(logging, log_props, "Running", "Basic Auth succeeded with cookies for {0}".format(content["authurl"]))
									# Use cookies instead of auth headers
									cookies = response.cookies
									headers = None
									proxies = None
							else:
								log_info(logging, log_props, "Running", "Passing Basic Auth credentials to request without cookies")

						if authtype == "OAuth 2.0":
							log_info(logging, log_props, "Running", "Retrieve OAuth 2.0 token")
							secret = _getSecret(self, str(input_item["api"] +":"+ content["username"] +":"))
							if secret is None:
								log_error_quit(logging, log_props, "Requested api secret has not been configured {0}".format(self.api))

							auth_response = oauthV2(content["authurl"], content["username"], secret, content["scope"])
							if auth_response.status_code != 200:
								log_error_quit(logging, log_props, "API authentication failed with status code {0}".format(auth_response.status_code))
							else:
								log_info(logging, log_props, "Running", "OAuth 2.0 token recieved")
							auth_json = json.loads(auth_response.content)
							headers = {"Authorization": "Bearer " + auth_json['access_token']} 

						log_info(logging, log_props, "Running", "{0} authentication configuration succeeded".format(authtype))

						if authtype == "No Auth":
							log_info(logging, log_props, "Running", "Requesting No Auth")
							headers=""

						### API URL CONFIGURATION ###
						if endpoint not in empty_set:
							payloadurl=content["baseurl"]+"/"+endpoint.strip("/")
						else:
							payloadurl=content["baseurl"]

						if filter != None:
							payloadurl = payloadurl + filter

						log_info(logging, log_props, "Running", "Calculated API URL: {0}".format(payloadurl))
						break

				### HEADERS CONFIGURATION ###
				log_info(logging, log_props, "Running", "Begin formatting headers")

				# Format headers by applying any custom values to the array
				if "headers" in input_item and input_item["headers"] not in empty_set:
					formattedHeaders = []
					appendedHeaders = input_item["headers"].strip()
					for sub in appendedHeaders.split(','):
						if ':' in sub:
							formattedHeaders.append(map(str.strip, sub.split(':', 1)))
					formattedHeaders = dict(formattedHeaders)
					headers.update(formattedHeaders)

				### INITIAL API REQUEST ###
				log_info(logging, log_props, "Running", "Before calling API")

				# This format handles any case where a cookie is provided or headers are used. Do not change.
				response = apiGET(url=payloadurl, proxies=proxies, headers=headers, cookies=cookies)
				if response.status_code != 200:
					log_error_quit(logging, log_props, "API request to {0} failed with status code {1}".format(payloadurl, response.status_code))
				else:
					log_info(logging, log_props, "Running", "API request to {0} status code {1}".format(payloadurl, response.status_code))

				#Convert CSV data to JSON format
				jsonFile = True
				eventPath = None
				if input_item["csv_conversion"] is not None and input_item["csv_conversion"].lower() in ['t', 'true']:
					log_info(logging, log_props, "Running", "Converting results from CSV to JSON format")
					jsonFile = False
					codec = getCodec(response.content)

					log_info(logging, log_props, "Running", "Detected {0} codec of response".format(codec))
					eventResponse = None					
					eventData = convertCSVtoJSON(response.content, codec)
				else:
					try:
						eventResponse = json.loads(response.content)
						if "event_path" in input_item and input_item["event_path"] not in empty_set:
							eventPath = input_item["event_path"].split("/")
							eventData = getNestedValue(eventResponse, eventPath)
						else:
							eventData = eventResponse
					except:
						log_error_quit(logging, log_props, "Results do not appear to be in JSON format. Verify csv=true is not needed or change to an endpoint that supports JSON before trying to index.")

				#Set the initial checkpointer to compare against all other things
				if update_checkpoint == True:			
					new_checkpoint = search_start_datetime
				else:
					new_checkpoint = None

				nextLink = None

				# Configure next_key lookups
				if "next_type" in input_item:
					if input_item["next_type"] == "linkHeader":
						nextKey = input_item["next_key"]
						page = 1
					elif input_item["next_type"] == "eventKey":
						nextKey = input_item["next_key"].split("/")
						page = 1
					else:
						nextKey = None
				else:
					nextKey = None

				log_info(logging, log_props, "Running", "Before writing events")
				count = 0

				if eventPath not in empty_set or jsonFile == False:
					if limit is None:
						log_info(logging, log_props, "Running", "Running without limits")						
						for item in eventData:
							new_checkpoint = _process_event(ew, 
															input_name, 
															input_item, 
															item, 
															event_timezone,
															props_time_format,
															update_checkpoint, 
															checkpoint_tracker, 
															new_checkpoint,
															search_start_datetime,
															end_date)
							if update_checkpoint == True and new_checkpoint > search_start_datetime:							
								count += 1
							elif update_checkpoint == False:
								count += 1

						# Search payload for value provided by self.next_key. getNestedValue returns None if key not found.
						if nextKey is not None:
							if input_item["next_type"] == "linkHeader":
								if nextKey in response.links:
									nextLink = response.links[nextKey]['url']
								else:
									nextLink = None
							elif input_item["next_type"] == "eventKey":
								nextLink = getNestedValue(eventResponse, nextKey)
							else:
								nextLink = None

						# If the next_key key is found response, we are officially paging the calls.
						if jsonFile == True and nextLink is not None:
							log_info(logging, log_props, "Running", "Paging events received")
							paging = True
						else:
							# If the next_key is provided by the caller but is not found in the json response. Throw and quit.
							if nextLink is None and nextKey is not None:
								log_warn(logging, log_props, "next_key {0} not found in response. Will not page results.".format(str(input_item["next_key"])))
							else:
								log_info(logging, log_props, "Running", "Paging of events is not configured")
							paging = False

						while paging == True:
							log_info(logging, log_props, "Running", "Paging through results with endpoint {0}".format(nextLink))
							page+=1             
							response = apiGET(url=nextLink, proxies=proxies, headers=headers, cookies=cookies)
							if response.status_code != 200:
								if update_checkpoint == True:
									log_info(logging, log_props, "Running", "Writing last good checkpointer to {0} before exit".format(checkpoint_file))
									writeCheckpoint(checkpoint_file, str(convertDateTimeToEpochTZ(new_checkpoint, checkpoint_timezone)))									
									log_error_quit(logging, log_props, "API request to {0} failed with status code {1}".format(payloadurl, response.status_code))

							eventResponse = json.loads(response.content)
							eventData = getNestedValue(eventResponse, eventPath)

							for item in eventData:
								new_checkpoint = _process_event(ew, 
																input_name, 
																input_item, 
																item, 
																event_timezone,
																props_time_format, 
																update_checkpoint, 
																checkpoint_tracker, 
																new_checkpoint,
																search_start_datetime,
																end_date)
								if update_checkpoint == True and new_checkpoint > search_start_datetime:							
									count += 1
								elif update_checkpoint == False:
									count += 1

							# Search payload for the next paging value provided by next_key
							if nextKey is not None:
								if input_item["next_type"] == "linkHeader":
									if nextKey in response.links:
										nextLink = response.links[nextKey]['url']
									else:
										nextLink = None
								elif input_item["next_type"] == "eventKey":
									nextLink = getNestedValue(eventResponse, nextKey)
								else:
									nextLink = None


							if nextLink is None:
								log_info(logging, log_props, "Running", "No more pages found")
								paging = False

					else:
						log_info(logging, log_props, "Running", "Limiting write event count to {0}".format(limit))
						for item in eventData:				
							# log_info(logging, log_props, "Running", "item: {0}".format(str(item)))
							new_checkpoint = _process_event(ew, 
															input_name, 
															input_item, 
															item,
															event_timezone,
															props_time_format, 
															update_checkpoint, 
															checkpoint_tracker, 
															new_checkpoint,
															search_start_datetime,
															end_date)
							if update_checkpoint == True and new_checkpoint > search_start_datetime:	
								count += 1
							elif update_checkpoint == False:
								count += 1

							if count == int(limit):
								break

						# Search payload for paging indicator.
						if nextKey is not None:
							if input_item["next_type"] == "linkHeader":
								if nextKey in response.links:
									nextLink = response.links[nextKey]['url']
								else:
									nextLink = None
							elif input_item["next_type"] == "eventKey":
								nextLink = getNestedValue(eventResponse, nextKey)
							else:
								nextLink = None

						log_info(logging, log_props, "Running", "HERE4: {0}".format(nextLink))
						# If the next_key key is found in json response, we are officially paging the calls.
						if jsonFile == True and nextLink is not None:
							log_info(logging, log_props, "Running", "Paging events received")
							paging = True
						else:
							# If the next_key is provided by the caller but is not found in the json response. Throw and quit.
							if nextLink is None and nextKey is not None:
								log_warn(logging, log_props, "next_key {0} not found in response. Will not page results.".format(str(input_item["next_key"])))
							else:
								log_info(logging, log_props, "Running", "Paging of events is not configured")
							paging = False
						
						while paging == True and count!=int(limit):
							log_info(logging, log_props, "Running", "Paging through results with endpoint {0}".format(nextLink))					
							page+=1
							response = apiGET(url=nextLink, proxies=proxies, headers=headers, cookies=cookies)
							if response.status_code != 200:
								if update_checkpoint == True:
									log_info(logging, log_props, "Running", "Writing last good checkpointer to {0} before exit.".format(checkpoint_file))
									writeCheckpoint(checkpoint_file, str(convertDateTimeToEpochTZ(new_checkpoint, checkpoint_timezone)))
									log_error_quit(logging, log_props, " API request to {0} failed with status code {1}".format(payloadurl, response.status_code))
							eventResponse = json.loads(response.content)
							eventData = getNestedValue(eventResponse, eventPath)
							for item in eventData:
								new_checkpoint = _process_event(ew, 
																input_name, 
																input_item, 
																item,
																event_timezone,
																props_time_format, 
																update_checkpoint, 
																checkpoint_tracker, 
																new_checkpoint,
																search_start_datetime,
																end_date)
								if update_checkpoint == True and new_checkpoint > search_start_datetime:							
									count += 1
								elif update_checkpoint == False:
									count += 1

								if count == int(limit):
									break

							# Search payload for the next paging value provided by next_key
							if nextKey is not None:
								if input_item["next_type"] == "linkHeader":
									if nextKey in response.links:
										nextLink = response.links[nextKey]['url']
									else:
										nextLink = None
								elif input_item["next_type"] == "eventKey":
									nextLink = getNestedValue(eventResponse, nextKey)
								else:
									nextLink = None

							if nextLink is None:
								log_info(logging, log_props, "Running", "No more pages found")
								paging = False

				else:
					log_info(logging, log_props, "Running", "No event_path provided. Indexing payload as a single event.")
					new_checkpoint = _process_event(ew, 
													input_name, 
													input_item, 
													eventData,
													event_timezone,
													props_time_format, 
													update_checkpoint, 
													checkpoint_field, 
													new_checkpoint,
													search_start_datetime,
													end_date)
					if new_checkpoint > search_start_datetime:
						count += 1
				
				log_info(logging, log_props, "Running", "Wrote {0} new event(s) to index".format(count))

				if update_checkpoint == True:
					#If events found, use last event's timestamp
					#If we calculated an end_date, use that
					#If no events found, use time.time()
					#If new_checkpoint == search_start_datetime, that means no events were found
					if (new_checkpoint == search_start_datetime):
						new_checkpoint = end_date

					if (new_checkpoint is not None):
						log_info(logging, log_props, "Running", "Performing write operation of new checkpointer to {0}. Next Checkpoint: {1}".format(checkpoint_file, new_checkpoint))
						writeCheckpoint(checkpoint_file, str(convertDateTimeToEpochTZ(new_checkpoint, checkpoint_timezone)))
					else:
						# If nothing was found, assume there is no data and update the checkpointer to time.time() calculated at the start of the input job
						log_info(logging, log_props, "Running", "Performing write operation of new checkpointer to {0}. Next Checkpoint: {1}".format(checkpoint_file, str(job_time)))
						writeCheckpoint(checkpoint_file, str(job_time))					

			log_info(logging, log_props, "Done", "Finished event collection for modinput")

		except Exception as e:
			log_error_quit(logging, log_props, "stream_events: {0}".format(e))

def _getSecret(self, username):
	try:
		log_info(logging, log_props, "Running", "Retrieve password")
		for storage_password in self.service.storage_passwords.list():
			if storage_password.name == username:
				log_info(logging, log_props, "Running", "Password found")
				return storage_password.clear_password
		log_error_quit(logging, log_props, "No password found for username {0}".format(username))
	except Exception as e:
		log_error_quit(logging, log_props, "_getSecret: {0}".format(e))	

def _process_event(ew, input_name, input_item, event, event_timezone, props_time_format, update_checkpoint, checkpoint_tracker, new_checkpoint, search_start_datetime, end_date):
	try:
		if update_checkpoint == True:
			latest_event_checkpoint = _get_new_checkpoint(event, checkpoint_tracker)

			if latest_event_checkpoint > search_start_datetime and (end_date is None or latest_event_checkpoint <= end_date):
				_event_writer(ew, input_name, input_item, event, event_timezone, props_time_format)

			if latest_event_checkpoint > new_checkpoint and (end_date is None or latest_event_checkpoint <= end_date):
				log_info(logging, log_props, "Running", "Setting new checkpoint highwater mark to {0}".format(latest_event_checkpoint))
				return latest_event_checkpoint
			else:
				log_info(logging, log_props, "Running", "Highwater mark for checkpoint stayed the same")
				return new_checkpoint
		else:
			_event_writer(ew, input_name, input_item, event, event_timezone, props_time_format)
			return
	except Exception as e:
		log_error_quit(logging, log_props, "_process_event: {0}".format(e))

def	_event_writer(ew, input_name, input_item, data, event_timezone, props_time_format):
	try:
		# Create an Event object, and set its fields
		output = data
		empty_set = ["", "undefined", None]

		# Create api_time based on configured event_time_field. If field doesn't exist in payload, default it.
		if "event_time_field" in input_item and input_item["event_time_field"] not in empty_set:

			if input_item["event_time_field"] in data:
				event_time_value = data[input_item["event_time_field"]]
				event_time_format = input_item["event_time_format"]
			else:
				log_error_quit(logging, log_props, "Field {0} not found in event. Check the data and the configured Event Key and Event Breaker options.".format(input_item["event_time_field"]))
		else:
			event_time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
			event_time_value = datetime.datetime.now(datetime.timezone.utc)
			event_time_value = event_time_value.strftime(event_time_format)

		output['api_time'] = createTimestamp(convertStringToDateTime(event_time_value), None, props_time_format)

		event = Event()
		event.sourceType = input_item["sourcetype"]
		event.source = input_name
		event.data = json.dumps(output, sort_keys=True)
		ew.write_event(event)
	except Exception as e:
		log_error_quit(logging, log_props, "_event_writer: {0}".format(e))

def _get_new_checkpoint(event, checkpoint_tracker):
	try:
		checkpointValue = None
		checkpointPath = checkpoint_tracker.split("/")
		checkpointValue = getNestedValue(event, checkpointPath)

		if checkpointValue is not None:
			log_info(logging, log_props, "Running", "Found possible new checkpoint in event {0}".format(checkpointValue))
			return checkpointValue
		else:
			log_error_quit(logging, log_props, "Checkpoint tracking was chosen but selected checkpoint path not found in event: {0}".format(checkpoint_tracker))
	except Exception as e:
		log_error_quit(logging, log_props, "_get_new_checkpoint: {0}".format(e))

# If epoch time provided, convert to human readble. Or return current date/time.
def _calculate_start(checkpoint_type, checkpoint_start_epoch, checkpoint_start_date, checkpoint_format, checkpoint_timezone):
	try:
		# First time through, calculate the number of days to search based on the provided checkpoint_start_date. If one is somehow missing, default to 10 days ago.
		if not checkpoint_start_date in ["", None]:
			daysAgo = calculateDaysFromToday(checkpoint_start_date)
		else:
			if checkpoint_type == odata_filter:
				daysAgo = 10
			else:
				daysAgo = 900

		if not checkpoint_start_epoch in ["", None]:
			return convertEpochToDateTimeTZ(convertStringToFloat(checkpoint_start_epoch), checkpoint_timezone, checkpoint_format)
		else:
			return (getNowAsTZ(checkpoint_timezone) - calculateDayDelta(daysAgo)).strftime(checkpoint_format)
		
	except Exception as e:
		log_error_quit(logging, log_props, "_calculate_start: {0}".format(e))

#------------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------------  

if __name__ == "__main__":
    sys.exit(APIConnect().run(sys.argv))
    


