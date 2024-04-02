from __future__ import print_function
import sys, json, time, os, socket, ast, re
from sys import platform
import itertools

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "lib"))
from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option, validators
from pnnllib.apirequests import apiGET, apiPOST
from pnnllib.datautils import convertCSVtoJSON, getCodec, getNestedValue
from pnnllib.apiauth import authBasic, authCookie, authHeader, authNone, authOAuthV2, authToken

@Configuration(distributed=False)
class APIConnect(GeneratingCommand):

	# Example Usage
	# | apiconnect 
	# 	api=Graph 
	#   method=GET
	# 	endpoint=v1.0/admin/serviceAnnouncement/healthOverviews?$expand=issues($filter=lastModifiedDateTime%20gt%202023-06-26T20:30:01.16Z) 
	# 	limit=1 
	#   csv=true
	# 	event_breaker=issues
	#   paging_type=body
	#   next_key=data/nextKey
	# 	headers="header1: header1value, header2: header2value"

	#Input fields for custom command
	api = Option(
		doc='''
		**Syntax:** **api=***<api_name>*
		**Description:** API credential to use''',
		require=True)
	method = Option(
		doc='''
		**Syntax:** **method=***<GET/POST>*
		**Description:** GET or POST''',
		require=False)
	endpoint = Option(
		doc='''
		**Syntax:** **endpoint=***<api_endpoint>*
		**Description:** API endpoint to use''',
		require=False)
	json = Option(
		doc='''
		**Syntax:** **json=***<json>*
		**Description:** JSON formatted query to pass to endpoint in the request body''',
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
	next_location = Option(
		doc='''
		**Syntax:** **next_location=***<next_location>*
		**Description:** Location of next_key for paged events (HEADER/BODY)''',
		require=False)
	next_key = Option(
		doc='''
		**Syntax:** **next_key=***<next_key>*
		**Description:** Identifier for paged events''',
		require=False)
	# Might develop this to direct where to throw the next request
	# next_apply = Option(
	# 	doc='''
	# 	**Syntax:** **next_apply=***<next_apply>*
	# 	**Description:** Determines how to apply the next request using the next_location and next_key values (URL/JSON)''',
	# 	require=False)		
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

	def generate(self):
		self.logger.warning('apiconnect: Begin API GET')

		#Set global variables
		global ta_name	
		ta_name="TA-pnnl_api_connect"
		
		empty_set = ["", "undefined", None]
		api_methods = ["GET", "POST"]
		paging_locations = ["HEADER", "BODY"]
		# next_apply_types = ["URL", "JSON"]

		url_match = r'https?://\S+'

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
			self.logger.warning("apiconnect: Lookup api configuration for {0}".format(self.api))

		self.logger.warning("apiconnect: ***** SELF ***** {0}".format(self))

		# ------------------------------------------------------------------------------------------
		# Next Links: Set up where and how to find paging indicators in response object
		# ------------------------------------------------------------------------------------------
		# nextLocation = None
		# nextApply=None
		nextLink = None
		nextLocation = None
		# nextApply=self.next_apply.upper()

		if self.next_location not in empty_set:
			nextLocation=self.next_location.upper()

			if nextLocation not in paging_locations:
				self.write_error("Invalid next_location provided (HEADER/BODY): {0}".format(nextLocation))
				quit()
			
			# if nextApply not in next_apply_types:
			# 		self.write_error("apiconnect: Invalid next_apply provided (URL/JSON):".format(nextApply))
			# 		quit()							

			if self.next_key in empty_set: 
				self.write_error("apiconnect: next_key must be provided with next_location so paging knows where to find paging in the reesponse")
				quit()
			else:
				if nextLocation == "HEADER":
					nextKey = self.next_key
					page = 1
				else:
					# It's in the body somewhere
					nextKey = self.next_key.split("/")
					page = 1
		else:
			# if nextApply not in empty_set:
			# 		self.write_error("apiconnect: next_location (HEADER/BODY) must be provided (URL/JSON) with paging configuration so it knows where to apply paging to the follow-up response")
			# 		quit()

			if self.next_key not in empty_set:
				self.write_error("apiconnect: next_location (HEADER/BODY) must be provided with next_key so paging knows where in the response to locate the paging key")
				quit()
			else:
				nextKey = None

		# ------------------------------------------------------------------------------------------
		# Body: Validates any body payloads passed to command
		# ------------------------------------------------------------------------------------------
		
		body_json = None

		if self.json is not None:
			try:
				# convert the string literal to a dict object
				body_json = ast.literal_eval(self.json)
				if debug=="True":
					self.logger.warning("apiconnect: body_json {0}".format(self.json))
			except:
				self.write_error("apiconnect: body_json does not appear to be a valid JSON format")
				quit()

		# ------------------------------------------------------------------------------------------
		# Proxies: Build connection to proxy, if needed
		# ------------------------------------------------------------------------------------------

		proxies = {}
		if self.useproxy is not None and str(self.useproxy).lower() in ["t", "true", "1"]:
			if debug=="True":
				self.logger.warning("apiconnect: Configuring proxy")
			for stanza in proxyConf:
				content=json.loads(json.dumps(stanza.content))
				if "proxyurl" in content and content["proxyurl"] is not None:
					proxies[stanza.name] = content["proxyurl"]
				else:
					if debug=="True":
						self.logger.warning("apiconnect: Proxy has not been configured")
					self.write_error("useproxy was requested but proxy has not been configured properly")
					quit()

			if debug=="True":
				self.logger.warning("apiconnect: Using proxy configuration {0}".format(proxies))

		# ------------------------------------------------------------------------------------------
		# Authentication: Build authentication headers or cookies
		# ------------------------------------------------------------------------------------------
		
		cookies = None

		for stanza in apiConfigs:
			# if debug=="True":
			# 	self.logger.warning("apiconnect: ---------------------------------")
			# 	self.logger.warning("apiconnect: stanza.name {0}".format(stanza.name))
			# 	self.logger.warning("apiconnect: self.api {0}".format(self.api))

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
						self.write_error("apiconnect: Valid authentication type not provided")
						quit()
				except Exception as e:
					self.write_error("apiconnect: Exception gathering credentials for {0}. Error {1}".format(self.api, e))
					quit()

				foundConfig = True

				# Found stanza matching API parameter passed to the command
				break

		if foundConfig == False:
			if debug=="True":
				self.logger.warning("apiconnect: Requested api has not been configured {0}".format(self.api))
			self.write_error("apiconnect: Requested API name has not been configured")
			quit()
		else:

			# ------------------------------------------------------------------------------------------
			# Headers: Configure headers for the API call
			# ------------------------------------------------------------------------------------------

			### HEADERS CONFIGURATION ###
			formattedHeaders = []
		
			if self.headers is not None:
				if debug=="True":
					self.logger.warning("apiconnect: Appending custom headers {0}".format(self.headers))
				appendedHeaders=self.headers.strip()
				for sub in appendedHeaders.split(','):
					if ':' in sub:
						formattedHeaders.append(map(str.strip, sub.split(':', 1)))
				formattedHeaders = dict(formattedHeaders)
				if headers is not None:
					headers.update(formattedHeaders)
				else:
					headers = formattedHeaders
			
			if debug=="True":
				self.logger.warning("apiconnect: Using headers for request {0}".format(str(headers)))

			# ------------------------------------------------------------------------------------------
			# apiconnect: Begin calling the API
			# ------------------------------------------------------------------------------------------

			if self.method is not None:
				if self.method in api_methods:
					method=self.method
				else:
					self.write_error("Valid API method missing. Use method=GET/POST")
					quit()
			else:
				if debug=="True":
					self.logger.warning("apiconnect: Defaulting to method GET")
				method="GET"

			if self.endpoint not in empty_set:
				payloadurl=baseurl+"/"+self.endpoint.strip("/")
			else:
				payloadurl=baseurl

			if debug=="True":
				self.logger.warning("apiconnect: Making {0} request to API endpoint {1}".format(method, payloadurl))

			# This format handles any case where a cookie is provided or headers are used. Do not change.
			if method == "GET":
				response = apiGET(url=payloadurl, proxies=proxies, headers=headers, cookies=cookies, json=body_json)
			else:
				response = apiPOST(url=payloadurl, proxies=proxies, headers=headers, cookies=cookies, json=body_json)

			if response.status_code != 200:
				self.write_error("API {0} failed with status code {1}".format(method, response.status_code))
				quit()

			jsonFile = True
			if self.csv is not None and self.csv.lower() in ["t", "true", "1"]:
				jsonFile = False
				self.logger.warning("apiconnect: Converting results from CSV to JSON format")
				codec = getCodec(response.content)
				
				self.logger.warning("apiconnect: Detected {0} codec of response".format(codec))
				eventResponse = None
				eventData = convertCSVtoJSON(response.content, codec)
			else:
				try:
					if response.content and response.content not in empty_set:
						self.logger.warning("content {0}".format(response.content))
						eventResponse=json.loads(response.content.decode('utf-8'))
						self.logger.warning("content {0}".format(eventResponse))
					else: 
						eventResponse = json.loads(response)

					if self.event_path is not None:
						eventPath = self.event_path.split("/")
						eventData = getNestedValue(eventResponse, eventPath)
					else:
						eventData = eventResponse
				except:
					self.logger.warning("apiconnect: Results do not appear to be in JSON format. Writing payload as a single event. Verify csv=true is not needed.")
					yield json.loads(buildNonJSONEvent(baseurl, response.content))
					quit()

			# jsonFile == False: If original was CSV, we want to write each row as an event. These have been converted to JSON format.
			if self.event_path is not None or jsonFile == False:
				if self.limit is None:
					if debug=="True":
						self.logger.warning("apiconnect: Running without limits")

					for item in eventData:
						yield buildEvent(baseurl, item)

					# Search payload for value provided by self.next_key. getNestedValue returns None if key not found.
					if nextKey is not None:
						if nextLocation == "HEADER":
							if nextKey in response.links:
								nextLink = response.links[nextKey]['url']
							else:
								nextLink = None
						elif nextLocation == "BODY":
							data_pointer = getNestedValue(eventResponse, nextKey)
							if data_pointer is not None:
								if re.search(url_match, data_pointer) is not None:
									# If it looks like a URL, use that as the next link
									nextLink=data_pointer
								else:
									# Assume it is a token
									body_json[nextKey[-1]] = data_pointer
									nextLink = payloadurl
							else:
								nextLink = None
						else:
							nextLink = None

					# If the next_key key is found in json response, we are officially paging the calls.
					if jsonFile == True and nextLink is not None:
						if debug=="True":
							self.logger.warning("apiconnect: Paging events found")
						paging = True
					else:
						# If the next_key is provided by the caller but is not found in the json response. Throw and quit.
						if nextLink is None and nextKey is not None:
							self.logger.warning("apiconnect: next_key=\"{0}\" not found in response. Skipping paging.".format(str(self.next_key)))
							self.write_warning("WARNING: Provided next_key=\"{0}\" not found in response. Paging skipped.".format(str(self.next_key)))
							paging = False
						else:
							if debug=="True":
								self.logger.warning("apiconnect: Paging of events is not configured")
							paging = False

					while paging == True:
						if debug=="True":
							self.logger.warning("apiconnect: Begin paging events")
						page+=1
						if debug=="True":
							self.logger.warning("apiconnect: Making page {0} request to api with {1} value {2}".format(page, nextLocation, nextLink))

						if method == "GET":
							response = apiGET(url=nextLink, proxies=proxies, headers=headers, cookies=cookies, json=body_json)
						else:
							response = apiPOST(url=nextLink, proxies=proxies, headers=headers, cookies=cookies, json=body_json)

						if response.status_code != 200:
							self.write_error("API failed with status code {0}".format(response.status_code))
							if debug=="True":
								self.logger.warning("apiconnect: Page {0} request to api endpoint {1} failed {2}".format(page, nextLink, response.status_code))
							quit()

						eventResponse = json.loads(response.content)
						eventData = getNestedValue(eventResponse, eventPath)
						for item in eventData:
							yield buildEvent(baseurl, item)						

						# Cycle through the rest of the pages
						if nextLocation == "HEADER":
							if nextKey in response.links:
								nextLink = response.links[nextKey]['url']
							else:
								nextLink = None
						elif nextLocation == "BODY":
							data_pointer = getNestedValue(eventResponse, nextKey)
							if data_pointer is not None:
								if re.search(url_match, data_pointer) is not None:
									# If it looks like a URL, use that as the next link
									nextLink=data_pointer
								else:
									# Assume it is a token
									body_json[nextKey[-1]] = data_pointer
									nextLink = payloadurl
							else:
								nextLink = None
						else:
							nextLink = None

						# All done
						if nextLink is None:
							if debug=="True":
								self.logger.warning("apiconnect: No more pages found")
							paging = False

				else:
					if debug=="True":
						self.logger.warning("apiconnect: Limiting write event count to {0}".format(self.limit))
					count = 0
					for item in eventData:
						yield buildEvent(baseurl, item)
						count+=1

						if count == int(self.limit):
							if debug=="True":
								self.logger.warning("apiconnect: Defined limit of {0} events hit. Count={1}".format(self.limit, count))							
							break

					if debug=="True":
						self.logger.warning("apiconnect: Wrote {0} events on first pass".format(count))

					# Search payload for value provided by self.next_key. getNestedValue returns None if key not found.
					if nextKey is not None:
						if nextLocation == "HEADER":
							if nextKey in response.links:
								nextLink = response.links[nextKey]['url']
							else:
								nextLink = None
						elif nextLocation == "BODY":
							data_pointer = getNestedValue(eventResponse, nextKey)
							if data_pointer is not None:
								if re.search(url_match, data_pointer) is not None:
									# If it looks like a URL, use that as the next link
									nextLink=data_pointer
								else:
									# Assume it is a token
									body_json[nextKey[-1]] = data_pointer
									nextLink = payloadurl
							else:
								nextLink = None
						else:
							nextLink = None

					# If the next_key key is found in json response, we are officially paging the calls.
					if jsonFile == True and nextLink is not None:
						if debug=="True":
							self.logger.warning("apiconnect: Paging events found")
						paging = True
					else:
						# If the next_key is provided by the caller but is not found in the json response. Throw and quit.
						if nextLink is None and nextKey is not None:
							self.logger.warning("joinapi: next_key=\"{0}\" not found in response. Skipping paging.".format(str(self.next_key)))
							self.write_warning("WARNING: next_key=\"{0}\" not found in response".format(str(self.next_key)))
							paging = False
						else:
							if debug=="True":
								self.logger.warning("apiconnect: Paging of events is not configured")
							paging = False

					while paging == True and count!=int(self.limit):
						if debug=="True":
							self.logger.warning("apiconnect: Begin paging events")
						page+=1
						if debug=="True":
							self.logger.warning("apiconnect: Making page {0} request to api endpoint {1}".format(page, nextLink))
						if method == "GET":				
							response = apiGET(url=nextLink, proxies=proxies, headers=headers, cookies=cookies, json=body_json)
						else:						
							response = apiPOST(url=nextLink, proxies=proxies, headers=headers, cookies=cookies, json=body_json)

						if response.status_code != 200:
							self.write_error("API failed with status code {0}".format(response.status_code))
							if debug=="True":
								self.logger.warning("apiconnect: Page {0} request to api endpoint {1} failed {2}".format(page, nextLink, response.status_code))							
							quit()

						eventResponse = json.loads(response.content)
						eventData = getNestedValue(eventResponse, eventPath)

						if debug=="True":
							self.logger.warning("apiconnect: Writing page {0} events to Splunk".format(page))
						for item in eventData:
							yield buildEvent(baseurl, item)
							count+=1

							if count == int(self.limit):
								if debug=="True":
									self.logger.warning("apiconnect: Defined limit of {0} events hit. Count={1}".format(self.limit, count))
								break

						# Cycle through the rest of the pages
						if nextLocation == "HEADER":
							if nextKey in response.links:
								nextLink = response.links[nextKey]['url']
							else:
								nextLink = None
						elif nextLocation == "BODY":
							data_pointer = getNestedValue(eventResponse, nextKey)
							if data_pointer is not None:
								if re.search(url_match, data_pointer) is not None:
									# If it looks like a URL, use that as the next link
									nextLink=data_pointer
								else:
									# Assume it is a token
									body_json[nextKey[-1]] = data_pointer
									nextLink = payloadurl
							else:
								nextLink = None
						else:
							nextLink = None

						# All done
						if nextLink is None:
							if debug=="True":
								self.logger.warning("apiconnect: No more pages found")
							paging = False
			else:
				if debug=="True":
					self.logger.warning("apiconnect: Attempting to break response into events")

				try:
					if isinstance(eventData, list):
						if debug=="True":
							self.logger.warning("apiconnect: Response appears to be a list. Separating into events.")
						
						# -- ChatGPT FTW ---
						# Create a generator expression that yields events one by one.
						events_generator = (buildEvent(baseurl, item) for item in eventData)
						# itertools.islice is used to limit the number of items yielded by the generator
						# enumerate to count the number of yielded events
						for count, event in enumerate(itertools.islice(events_generator, None if self.limit is None else int(self.limit)), start=1):
							yield event
							if self.limit is not None and count == int(self.limit):
								if debug=="True":
									self.logger.warning("apiconnect: Defined limit of {0} events hit. Count={1}".format(self.limit, count))		
								break
					else:
						if debug=="True":
							self.logger.warning("apiconnect: Response does not appear to be a list. Writing as a single event to Splunk. Consider using event_path to return a payload as single events.")
						# for item in eventData:
						yield buildEvent(baseurl, eventData)
				except ValueError:
					if debug=="True":
						self.logger.warning("apiconnect: Writing single event to Splunk")
					# for item in eventData:
					yield buildEvent(baseurl, eventData)

			self.logger.info("{0}: Before updating checkpointer".format(self.api))

def buildEvent(baseurl, item):

	item['_time'] = time.time()
	item['_raw'] = json.dumps(item, sort_keys=True)
	item['host'] = socket.gethostname()
	item['source'] = baseurl
	item['sourcetype'] = "_json"
	return item

def buildNonJSONEvent(baseurl, event):
	item = {}
	item['_time'] = time.time()
	item['_raw'] = event.decode()
	item['host'] = socket.gethostname()
	item['source'] = baseurl
	item['sourcetype'] = "_json"
	return json.dumps(item)

#------------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------------  

if __name__=="__main__":
	dispatch(APIConnect, sys.argv, sys.stdin, sys.stdout, __name__)
