# encoding = utf-8
import sys, os, base64, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../..", "lib"))
from pnnllib.apirequests import apiGET, oauthV2

###################################################################################################################
#
#                                         Supported API Authentication Types
#
###################################################################################################################

def authBasic(self, content):
    try:
        # Configure Basic Auth package. Will build the basic authentication header to send with the request.
        secret = getSecret(self, content)

        # Create a base64 encoded string to pass in the Authorization header
        cred = content["username"] + ":" + secret
        cred64 = base64.b64encode(cred.encode()).decode()

        headers = {"Authorization": "Basic %s" % cred64}

        return headers
    except Exception as e:
        raise ValueError("authBasic: {0}".format(e))

def authCookie(self, content, proxies=None):
    try:

        empty_set = ["", "undefined", None]

        # If auth URL provided, will get a session cookie to pass to requests.
        # This type is used for APIs that require username/passwords to be passed as header parameters.
        if "usernamekey" in content and content["usernamekey"] not in empty_set:
            usernamekey=content["usernamekey"]
        else:
            usernamekey="username"
        if "secretkey" in content and content["secretkey"] not in empty_set:
            secretkey=content["secretkey"]
        else:
            secretkey="password"
        secret = getSecret(self, content)

        if "authdomain" in content and content["authdomain"] not in empty_set:
            username=content["authdomain"]+ "\\" + content["username"]

        headers = {usernamekey: username, secretkey: secret}

        if "authurl" in content and content["authurl"] not in empty_set:
            # Get a session cookie and use that for logins				
            response = apiGET(url=content["authurl"], proxies=proxies, headers=headers)
            if response.status_code != 200:
                raise ValueError("authCookie: Request failed with status code {0}".format(response.status_code))   
            else:
                # Return auth cookie
                return response.cookies

    except Exception as e:
        raise ValueError("authCookie: {0}".format(e))

def authHeader(self, content):
    try:
        empty_set = ["", "undefined", None]

        # Configure Header Auth package
        if "usernamekey" in content and content["usernamekey"] not in empty_set:
            usernamekey=content["usernamekey"]
        else:
            usernamekey="username"
        if "secretkey" in content and content["secretkey"] not in empty_set:
            secretkey=content["secretkey"]
        else:
            secretkey="password"
        secret = getSecret(self, content)

        if "authdomain" in content and content["authdomain"] not in empty_set:
            username=content["authdomain"]+ "\\" + content["username"]

        headers = {usernamekey: username, secretkey: secret}
        
        return headers
    except Exception as e:
        raise ValueError("authHeader: {0}".format(e))

def authNone():
    try:
        return ""
    except Exception as e:
        raise ValueError("authNone: {0}".format(e))
    
def authOAuthV2(self, content):
    try:
        # OAuth 2.0 based requests that request a token from an endpoint based on a client/secret
        response = oauthV2(content["authurl"], content["username"], getSecret(self, content), content["scope"])
        auth_json = json.loads(response.content)
        headers = {"Authorization": "Bearer " + auth_json['access_token']} 
        return headers
    except Exception as e:
        raise ValueError("authOAuthV2: {0}".format(e))


def authToken(self, content):
    try:
        authToken = getSecret(self, content)
        headers = {"Authorization": authToken} 

        return headers
    
    except Exception as e:
        raise ValueError("authToken: {0}".format(e))


def getSecret(self, content):
    try:
        for storage_password in self.service.storage_passwords.list():
            if storage_password.name == str(self.api + ":" + content["username"] + ":"):
                return storage_password.clear_password            
    except Exception as e:
        raise ValueError("getSecret: {0}".format(e))
