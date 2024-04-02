# encoding = utf-8
import csv, json
import chardet

###################################################################################################################
#
#                                               Data Utilities Functions
#
###################################################################################################################

# Converts CSV to JSON format
def convertCSVtoJSON(csv_input, codec):

	try:
		csv_decoded= csv_input.decode(codec)
		csv_data = csv.reader(csv_decoded.splitlines(), delimiter=',')
		data_list = list(csv_data)
		# return json.loads(json.dumps({"value":[dict(zip(data_list[0], row)) for row in data_list[1:]]}))
		return json.loads(json.dumps([dict(zip(data_list[0], row)) for row in data_list[1:]]))
	except Exception as e:
		raise ValueError("convertCSVtoJSON: {0}".format(e))

# Gets the encoding of the text
def getCodec(text):
	try:
		result = chardet.detect(text)
		return result['encoding']
	except Exception as e:
		raise ValueError("getCodec: {0}".format(e))

# Searches dictionary for a path of keys. Returns the final result.
def getNestedValue(data, path):
	try:
		current = data
		for key in path:
			# Try converting string to an integer to designate location in object
			try:
				key = int(key)
			except ValueError:
				key = key
			# Search dict array for key
			if isinstance(current, dict) and key in current:
				current = current[key]
			# If integer, search for object location in array
			elif isinstance(current, list) and isinstance(key, int) and key < len(current):
				current = current[key]
			else:
				return None
		return current
	except Exception as e:
		raise ValueError("getNestedValue: {0}".format(e))