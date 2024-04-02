# encoding = utf-8
import datetime

###################################################################################################################
#
#                                               Splunk Functions
#
###################################################################################################################

def getDateVariable(date_format, timezone, modifier):

    #------------------------------------------ Sample Usage -------------------------------------------------
    # currenttest = getDateVariable(content["format"], "utc", content["modifier"])
	# endpoint = endpoint.replace("{"+variable+"}",currenttest)
    #---------------------------------------------------------------------------------------------------------

    if modifier is None:
        modifier = 0

    if timezone.lower() == "utc":
        # Calculate default end date as UTC
        adjusted_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=int(modifier))
    elif timezone.lower() == "local":
        # Calculate default end date as local
        adjusted_date = datetime.datetime.now() + datetime.timedelta(days=int(modifier))
    else:
        #Default to UTC
        adjusted_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=int(modifier))

    return adjusted_date.strftime(date_format)
		




