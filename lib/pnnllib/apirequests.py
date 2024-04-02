# encoding = utf-8
import requests, urllib3

###################################################################################################################
#
#                                               Microsoft API Functions
#
###################################################################################################################

# Submit API GET request
def apiGET(url, proxies=None, headers=None, cookies=None, json=None):
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)      
        return requests.get(url=url, headers=headers, proxies=proxies, verify=False, cookies=cookies, json=json)
    
    except Exception as e:
        raise ValueError("apiGET: {0}".format(e))


# Submit API POST request
def apiPOST(url, proxies=None, headers=None, cookies=None, json=None):
    #Message body
    # body=body
    #Message headers
    headers=headers
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.post(url=url, headers=headers, proxies=proxies, verify=False, cookies=cookies, json=json)
        return response
    except Exception as e:
        raise ValueError("apiPOST: {0}".format(e))

# OAuth 2.0 Authentication
def oauthV2(oauth_url, username, secret, scope):
    #Message body
    body={'grant_type': 'client_credentials', 'client_id': username, 'client_secret': secret, 'scope': scope}
    #Message headers
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        #OAuth2_v2 HTTP Post to receive token
        response = requests.post(url=oauth_url,headers=headers,data=body)
        return response
    except Exception as e:
        raise ValueError("oauthV2: {0}".format(e))
