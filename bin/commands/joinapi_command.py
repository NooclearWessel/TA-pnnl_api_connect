from __future__ import print_function
import sys, json, os, base64, re
from sys import platform

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "lib"))
from splunklib.searchcommands import dispatch, StreamingCommand, Configuration, Option, validators
from pnnllib.apirequests import apiGET, oauthV2
from pnnllib.datautils import convertCSVtoJSON, getCodec, getNestedValue
from pnnllib.apiauth import authBasic, authCookie, authHeader, authNone, authOAuthV2, authToken

@Configuration(distributed=False)
class JoinAPI(StreamingCommand):

	# Example Usage
	# | joinapi 
	# 	api=Graph 
	# 	credential=SplunkLog 
	# 	endpoint=v1.0/admin/serviceAnnouncement/healthOverviews?$expand=issues($filter=lastModifiedDateTime%20gt%202023-06-26T20:30:01.16Z) 
	# 	limit=1 
	#   csv=true
	# 	event_path="value/0/issues"
	# 	headers="header1: header1value, header2: header2value"

	#Input fields for custom command
	api = Option(
		doc='''
		**Syntax:** **api=***<api_name>*
		**Description:** API credential to use''',
		require=True)
	endpoint = Option(
		doc='''
		**Syntax:** **endpoint=***<api_endpoint>*
		**Description:** API endpoint to use for all events. If none provided, looks for endpoint field in event.''',
		require=False)
	headers = Option(
		doc='''
		**Syntax:** **headers=***<headers>*
		**Description:** Additional headers to append to API call in JSON format''',
		require=False)
	csv = Option(
		doc='''
		**Syntax:** **csv=***<boolean>*
		**Description:** Converts events from CSV to JSON before ingest''',
		require=False)			
	event_path = Option(
		doc='''
		**Syntax:** **event_path=***<event_path>*
		**Description:** Path to the keys used to separate payload into events. Separate keys by forward slashes. Example: value/0/issues''',
		require=False)
	next_key = Option(
		doc='''
		**Syntax:** **next_key=***<next_key>*
		**Description:** Identifier for paged events''',
		require=False)
	limit = Option(
		doc='''
		**Syntax:** **limit=***<number>*
		**Description:** limits the number of results to return''',
		require=False)
	useproxy = Option(
		doc='''
		**Syntax:** **proxy=***<boolean>*
		**Description:** If True (t/true), pass request through proxy. Defaults to false (f/false)''',
		require=False, validate=validators.Boolean())
	debug = Option(
        doc='''
        **Syntax:** **debug=***<boolean>*
        **Description:** Sets debug logging level''',
        require=False, validate=validators.Boolean())	

	#------------------------------------------------------------------------------------------------------------------
	# Procedural definitions
	#------------------------------------------------------------------------------------------------------------------  

	def stream(self,events):
		self.logger.warning('joinapi: Begin API GET')

		#Set global variables
		global ta_name	
		ta_name="TA-pnnl_api_connect"
		
		empty_set = ["", "undefined", None]
		if (str(self.debug).lower()) in ["t", "true", "1"]:
			debug="True"
		else:
			debug="False"

		apiConfigs = self.service.confs["api_configs"]
		try:
			proxyConf = self.service.confs["api_proxy"]
		except:
			# Move on if proxy is unconfigured
			pass

		foundConfig = False
		page = 1
		count = 1

		if debug=="True":
			self.logger.warning("joinapi: Lookup api configuration for {0}".format(self.api))

		# ------------------------------------------------------------------------------------------
		# Proxies: Build connection to proxy, if needed
		# ------------------------------------------------------------------------------------------

		proxies = {}
		if self.useproxy is not None and str(self.useproxy).lower() in ["t", "true", "1"]:
			if debug=="True":
				self.logger.warning("joinapi: Configuring proxy")
			for stanza in proxyConf:
				content=json.loads(json.dumps(stanza.content))
				if "proxyurl" in content and content["proxyurl"] is not None:
					proxies[stanza.name] = content["proxyurl"]
				else:
					if debug=="True":
						self.logger.warning("joinapi: Proxy has not been configured")
					self.write_error("useproxy was requested but proxy has not been configured properly")
					quit()

			if debug=="True":
				self.logger.warning("joinapi: Using proxy configuration {0}".format(proxies))

		# ------------------------------------------------------------------------------------------
		# Authentication: Build authentication headers or cookies
		# ------------------------------------------------------------------------------------------

		cookies = None

		for stanza in apiConfigs:
			# if debug=="True":
			# 	self.logger.warning("joinapi: ---------------------------------")
			# 	self.logger.warning("joinapi: stanza.name {0}".format(stanza.name))
			# 	self.logger.warning("joinapi: self.api {0}".format(self.api))

			if stanza.name == self.api:
				content=json.loads(json.dumps(stanza.content))
				baseurl=content["baseurl"]

				try:
					# AUTHENTICATION CONFIGURATION
					if content["authtype"] == "Basic Auth":
						headers=authBasic(self, content)
					elif content["authtype"] == "Header Auth" and "authurl" in content and content["authurl"] not in empty_set:
						# Cookie auth					
						cookies=authCookie(self, content, proxies)
						headers = None
						# proxies = None
					elif content["authtype"] == "Header Auth":
						headers=authHeader(self, content)
					elif content["authtype"] == "No Auth":
						headers={}
					elif content["authtype"] == "OAuth 2.0":
						headers=authOAuthV2(self, content)
					elif content["authtype"] == "Auth Token":					
						headers=authToken(self, content)
					else:
						self.write_error("joinapi: Valid authentication type not provided")
						quit()
				except Exception as e:
					self.write_error("joinapi: Exception gathering credentials for {0}. Error {1}".format(self.api, e))
					quit()

				foundConfig = True

				# Found stanza matching API parameter passed to the command
				break

		if foundConfig == False:
			if debug=="True":
				self.logger.warning("joinapi: Requested api has not been configured {0}".format(self.api))
			self.write_error("joinapi: Requested API name has not been configured")
			quit()
		else:

			# ------------------------------------------------------------------------------------------
			# Headers: Configure headers for the API call
			# ------------------------------------------------------------------------------------------

			### HEADERS CONFIGURATION ###
			formattedHeaders = []
		
			if self.headers is not None:
				if debug=="True":
					self.logger.warning("joinapi: Appending custom headers {0}".format(self.headers))
				appendedHeaders=self.headers.strip()
				for sub in appendedHeaders.split(','):
					if ':' in sub:
						formattedHeaders.append(map(str.strip, sub.split(':', 1)))
				formattedHeaders = dict(formattedHeaders)
				headers.update(formattedHeaders)
			
			if debug=="True":
				self.logger.warning("joinapi: Using headers for request {0}".format(str(headers)))

			# ------------------------------------------------------------------------------------------
			# joinapi: Begin calling the API
			# ------------------------------------------------------------------------------------------

			#Loop through each event and search specified nameservers for provided events
			for eventResult in events:
				endpoint = None
				single_endpoint = False
				if self.endpoint is not None:
					if self.endpoint in eventResult and eventResult[self.endpoint] not in empty_set:
						# The joinapi command has instructions to use an endpoint field from each event for individual API calls
						endpoint=eventResult[self.endpoint].strip("/")
						self.logger.warning("joinapi: Using event endpoint {0} for request".format(endpoint))
					elif self.endpoint in eventResult and eventResult[self.endpoint] in empty_set:
						# An empty endpoint value was found in this event
						eventResult["apistatus"] = "Missing"
						eventResult["apiresult"] = "No suitable endpoint value found in command options or events"
						yield eventResult
						continue
					else:
						# An endpoint is provided by the command to be used globally across all events
						single_endpoint = True
						endpoint = self.endpoint.strip("/")
						self.logger.warning("joinapi: Using command endpoint option '{0}' for API requests".format(endpoint))
				elif endpoint is None and ("endpoint" in eventResult and eventResult["endpoint"] not in empty_set):
					# Endpoint option was not provided to the joinapi command, but an endpoint field was found in the event
					endpoint=eventResult["endpoint"].strip("/")
					self.logger.warning("joinapi: Using event endpoint {0} for request".format(endpoint))
				else:
					# An endpoint field was found in the event but is empty
					eventResult["apistatus"] = "Missing"
					eventResult["apiresult"] = "No suitable endpoint value found in command options or events"
					yield eventResult
					continue

				payloadurl=baseurl+"/"+endpoint

				if debug=="True":
					self.logger.warning("joinapi: Making request to API endpoint {0}".format(payloadurl))

				# This format handles any case where a cookie is provided or headers are used. Do not change.
				response = apiGET(url=payloadurl, proxies=proxies, headers=headers, cookies=cookies)
				
				if response.status_code != 200:
					if single_endpoint == True:
						self.write_error("API failed with status code {0} for url {1}".format(response.status_code, payloadurl))
						quit()
					else:
						# An endpoint field was found in the event but is empty
						eventResult["apistatus"] = "Error"
						eventResult["apiresult"] = "API request failed with status code {0}".format(response.status_code)
						yield eventResult
						continue

				jsonFile = True
				if self.csv is not None and self.csv.lower() in ["t", "true", "1"]:
					jsonFile = False
					self.logger.warning("joinapi: Converting results from CSV to JSON format")
					codec = getCodec(response.content)
					self.logger.warning("joinapi: Detected {0} codec of response".format(codec))
					eventResponse = None
					eventData = convertCSVtoJSON(response.content, codec)
				else:
					try:
						# eventResponse = json.loads(response.content)
						# event_path = self.event_path
						eventResponse = json.loads(response.content)
						
						if self.event_path is not None:
							eventPath = self.event_path.split("/")
							eventData = getNestedValue(eventResponse, eventPath)
						else:
							eventData = eventResponse						
					except:
						eventResult["apistatus"] = "Success"
						eventResult["apiresult"] = response.content.decode()
						self.logger.warning("joinapi: Results do not appear to be in JSON format. Writing payload as a single event. Verify csv=true is not needed.")
						yield eventResult
						continue

				if self.next_key is not None:
					nextKey = self.next_key.split("/")
					page = 1
				else:
					nextKey = None
				nextLink = None

				if self.event_path is not None or jsonFile == False:
					if self.limit is None:
						if debug=="True":
							self.logger.warning("joinapi: Running without limits")		
						for item in eventData:
							if debug=="True":
								self.logger.warning("joinapi: Writing events without event_breaker")
							eventResult["apistatus"] = "Success"
							eventResult["apiresult"] = json.dumps(item, sort_keys=True)
							yield eventResult

						# Search payload for value provided by self.next_key. getNestedValue returns None if key not found.
						if nextKey is not None:
							nextLink = getNestedValue(eventResponse, nextKey)

						# If the next_key key is found in json response, we are officially paging the calls.
						if jsonFile == True and nextLink is not None:
							if debug=="True":
								self.logger.warning("joinapi: Paging events found")
							paging = True
						else:
							# If the next_key is provided by the caller but is not found in the json response. Throw and quit.
							if nextLink is None and nextKey is not None:
								self.logger.warning("joinapi: next_key=\"{0}\" not found in response. Skipping paging.".format(str(self.next_key)))
								self.write_warning("WARNING: next_key=\"{0}\" not found in response. Skipping paging.".format(str(self.next_key)))
								paging = False
							else:
								if debug=="True":
									self.logger.warning("joinapi: Paging of events is not configured")
								paging = False

						while paging == True:
							if debug=="True":
								self.logger.warning("joinapi: Begin paging events")
							page+=1             

							if debug=="True":
								self.logger.warning("joinapi: Making page {0} request to api endpoint {1}".format(page, nextLink))
							response = apiGET(url=nextLink, proxies=proxies, headers=headers, cookies=cookies)
							if response.status_code != 200:
								self.write_error("API failed with status code {0}".format(response.status_code))
								if debug=="True":
									self.logger.warning("joinapi: Page {0} request to api endpoint {1} failed {2}".format(page, nextLink, response.status_code))
								quit()

							eventResponse = json.loads(response.content)
							eventData = getNestedValue(eventResponse, eventPath)

							for item in eventData:
								eventResult["apistatus"] = "Success"
								eventResult["apiresult"] = json.dumps(item, sort_keys=True)
								yield eventResult

							# Search payload for the next paging value provided by self.next_key
							nextLink = getNestedValue(eventResponse, nextKey)
							if nextLink is None:
								if debug=="True":
									self.logger.warning("joinapi: No more pages found")
								paging = False
					else:
						if debug=="True":
							self.logger.warning("joinapi: Limiting write event count to {0}".format(self.limit))
						count = 0
						for item in eventData:
							eventResult["apistatus"] = "Success"
							eventResult["apiresult"] = json.dumps(item, sort_keys=True)
							yield eventResult
							count+=1

							if count == int(self.limit):
								if debug=="True":
									self.logger.warning("joinapi: Defined limit of {0} events hit. Count={1}".format(self.limit, count))							
								break

						if debug=="True":
							self.logger.warning("joinapi: Wrote {0} events on first pass".format(count))

						# Search payload for value provided by self.next_key. getNestedValue returns None if key not found.
						if nextKey is not None:
							nextLink = getNestedValue(eventResponse, nextKey)

						# If the next_key key is found in json response, we are officially paging the calls.
						if jsonFile == True and nextLink is not None:
							if debug=="True":
								self.logger.warning("joinapi: Paging events found")
							paging = True
						else:
							# If the next_key is provided by the caller but is not found in the json response. Throw and quit.
							if nextLink is None and nextKey is not None:
								# self.write_error("Stopping. next_key=\"{0}\" not found in response".format(str(self.next_key)))
								self.logger.warning("joinapi: next_key=\"{0}\" not found in response. Skipping paging.".format(str(self.next_key)))
								self.write_warning("WARNING: next_key=\"{0}\" not found in response. Skipping paging.".format(str(self.next_key)))
								paging = False
								# quit()
							else:
								if debug=="True":
									self.logger.warning("joinapi: Paging of events is not configured")
								paging = False

						while paging == True and count!=int(self.limit):
							if debug=="True":
								self.logger.warning("joinapi: Begin paging events")
							page+=1

							if debug=="True":
								self.logger.warning("joinapi: Making page {0} request to api endpoint {1}".format(page, nextLink))					
							response = apiGET(url=nextLink, proxies=proxies, headers=headers, cookies=cookies)
							if response.status_code != 200:
								self.write_error("API failed with status code {0}".format(response.status_code))
								if debug=="True":
									self.logger.warning("joinapi: Page {0} request to api endpoint {1} failed {2}".format(page, nextLink, response.status_code))							
								quit()
		
							eventResponse = json.loads(response.content)
							eventData = getNestedValue(eventResponse, eventPath)
							if debug=="True":
								self.logger.warning("joinapi: Writing page {0} events to Splunk".format(page))
							for item in eventData:
								eventResult["apistatus"] = "Success"
								eventResult["apiresult"] = json.dumps(item, sort_keys=True)
								yield eventResult
								count+=1

								if count == int(self.limit):
									if debug=="True":
										self.logger.warning("joinapi: Defined limit of {0} events hit. Count={1}".format(self.limit, count))
									break

							# Search payload for the next paging value provided by self.next_key
							nextLink = getNestedValue(eventResponse, nextKey)
							if nextLink is None:
								if debug=="True":
									self.logger.warning("joinapi: No more pages found")
								paging = False
				else:
					if debug=="True":
						self.logger.warning("joinapi: Writing single event to Splunk")
					eventResult["apistatus"] = "Success"
					eventResult["apiresult"] = eventResponse
					yield eventResult

#------------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------------  

if __name__=="__main__":
	dispatch(JoinAPI, sys.argv, sys.stdin, sys.stdout, __name__)
