# encoding = utf-8
import datetime
from dateutil.parser import parse
from tzlocal import get_localzone

###################################################################################################################
#
#                                               Splunk Date/Time Functions
#
###################################################################################################################

__all__ = [
           "addMinutesToDateTime",
           "calculateDayDelta", 
           "calculateDaysFromToday", 
           "calculateMinutesDelta", 
           "convertDateTimeToEpochTZ",
           "convertEpochToDateTimeTZ", 
           "convertEpochToLocal", 
           "convertEpochToUTC",
           "convertStringToDateTime", 
           "convertStringToFloat", 
           "createTimestamp",            
           "getLocalTZ", 
           "getNowAsTZ", 
           "subtractDaysFromDatetime", 
           "subtractMinutesFromDateTime", 
           ]


# Push datetime forward by the number of minutes
def addMinutesToDateTime(dt, format, minutes):
    try:
        return (convertStringToDateTime(dt) + calculateMinutesDelta(int(minutes))).strftime(format)
    except Exception as e:
        raise ValueError("addMinutesToDateTime: {0}".format(e))

# Returns number of days since current time
def calculateDayDelta(days):
    try:
        return datetime.timedelta(days=days)
    except Exception as e:
        raise ValueError("calculateDayDelta: {0}".format(e))

# Finds number of days since provided dt field
def calculateDaysFromToday(dt):
    try:
        return (datetime.date.today() - datetime.datetime.strptime(dt, "%Y-%m-%d").date()).days
    except Exception as e:
        raise ValueError("calculateDaysFromToday: {0}".format(e))

# Returns number of minutes since current time
def calculateMinutesDelta(minutes):
    try:
        return datetime.timedelta(minutes=minutes)
    except Exception as e:
        raise ValueError("calculateMinutesDelta: {0}".format(e))

# Convert datetime object to Epoch format
def convertDateTimeToEpochTZ(dt, timezone):
    try:
        #Return epoch time with timezone offset
        return (convertStringToDateTime(dt).astimezone(timezone) - datetime.datetime(1970,1,1).replace(tzinfo=timezone)).total_seconds()
    except Exception as e:
        raise ValueError("convertDateTimeToEpochTZ: {0}".format(e))

# Converts epoch time to the timezone's datetime in the given format
# Timezone=None converts to local
def convertEpochToDateTimeTZ(epochTime, timezone, format):
    try:
        return datetime.datetime.fromtimestamp(epochTime, tz=timezone).strftime(format)
    except Exception as e:
        raise ValueError("convertEpochToDateTimeTZ: {0}".format(e))

# Converts epoch time to local datetime in the given format
def convertEpochToLocal(epochTime, format):
    try:
        return datetime.datetime.fromtimestamp(epochTime).strftime(format)
    except Exception as e:
        raise ValueError("convertEpochToLocal: {0}".format(e))
    
# Converts epoch time to UTC datetime in the given format
def convertEpochToUTC(epochTime, format):
    try:
        return datetime.datetime.utcfromtimestamp(epochTime).strftime(format)
    except Exception as e:
        raise ValueError("convertEpochToUTC: {0}".format(e))

# Format string as datetime object
def convertStringToDateTime(dt):
    try:
        return parse(dt)
    except Exception as e:
        raise ValueError("convertStringToDateTime: {0}".format(e))
   
# Converts decimal-formatted string to float
def convertStringToFloat(string):
    try:
        return float(string)
    except Exception as e:
        raise ValueError("convertStringToFloat: {0}".format(e))

# Convert datetime into timezone/format formatted string. timezone=None returns local time
def createTimestamp(dt, timezone, format):
    try:
        return dt.astimezone(timezone).strftime(format)
    except Exception as e:
        raise ValueError("createTimestamp: {0}".format(e))

# Return the local timezone
# This does not work on our RHEL boxes. Need to figure out why. Could possibly read from the OS's ZONEs config
def getLocalTZ():
    try:
        # log_info("TESTING", "Local Timezone: {0}".format(get_localzone()))
        return get_localzone()
    except Exception as e:
        raise ValueError("getLocalTZ: {0}".format(e))

def getNowAsTZ(timezone):
    try:
        return datetime.datetime.now(timezone)
    except Exception as e:
        raise ValueError("getNowAsTZ: {0}".format(e))

# Finds number of days since provided dt field
def subtractDaysFromDatetime(dt):
    try:
        return (datetime.date.today() - datetime.datetime.strptime(dt, "%Y-%m-%d").date()).days
    except Exception as e:
        raise ValueError("subtractDaysFromDatetime: {0}".format(e))

# Pull back the datetime based on the number of minutes
def subtractMinutesFromDateTime(dt, format, minutes):
    try:
        return (convertStringToDateTime(dt) - calculateMinutesDelta(int(minutes))).strftime(format)
    except Exception as e:
        raise ValueError("subtractMinutesFromDateTime: {0}".format(e))

