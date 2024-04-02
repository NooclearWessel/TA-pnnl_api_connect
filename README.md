## CC0

Released under the Creative Commons 0 Public Domain Dedication:  https://creativecommons.org/publicdomain/zero/1.0/ 
  
This material is free to use, and attribution is always appreciated. Attribution may be as follows: 

Authored by Joshua Stratton at the Pacific Northwest National Laboratory, operated by Battelle for the U.S. Department of Energy.

## DESCRIPTION

This Splunk Technology Add-On was developed as an API integration tool for Splunk. It delivers a modular input for ingesting API-based data into Splunk indexes. It also includes two custom commands for live reading of API events.

#### TA Views

| View            | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| configuration   | Setup page to add/organize API providers and their endpoint connection details. This includes the configuration name, base url, and credentials. Used by both modular input and custom commands |
| inputs          | Modular input configuration for your heavy forwarders        |
| proxy           | HTTPS/HTTP proxy configuration for outbound or firewall-blocked endpoints |
| apiconnect_logs | Useful for troubleshooting apiconnect modular input workflows through extensive logging |

#### Configuration Files

| .conf File         | Splunk Supported | Description                                                  |
| ------------------ | ---------------- | ------------------------------------------------------------ |
| api_configs.conf   | No               | API configurations entered from the configurations view. This file holds the API connectivity details. The stanza name is the mapping used by the modular input and the apiconnect/joinapi commands' api property.<br /><br />Example:<br />[graph_api]<br />authtype = OAuth 2.0<br />authurl = https://login.microsoftonline.com/<your_tenant_id>/oauth2/v2.0/token<br />baseurl = https://graph.microsoft.com<br />provider = Microsoft<br />scope = https://graph.microsoft.com/.default<br />username = <your_azure_app_id><br /> |
| api_providers.conf | No               | A list of stanzas identifying the API providers your environment supports.<br /><br />Example:<br />[Microsoft]<br />[AWS] |
| api_proxy.conf     | No               | Proxy connectivity information<br /><br />Example:<br />[http]<br />proxyurl = http://myproxyhost.myco.com:3128<br /><br />[https]<br />proxyurl = http://myproxyhost.myco.com:3128 |
| api_variables.conf | No               | This file does not have a corresponding UI page. This is helpful for modular input API calls which need a customized date/time format.<br /><br />Example:<br />[utc_YYY-MM-DD]<br />type = date<br />format = %Y-%m-%d<br />timezone = etc |
| app.conf           | Yes              | Describes the application to Splunk. Included a [triggers] stanza to allow reloading of custom .conf files without having to restart Splunk |
| commands.conf      | Yes              | Describes the custom commands to Splunkd                     |
| inputs.conf        | Yes              | For modular input scheduling and consumption                 |
| passwords.conf     | Yes              | Splunk-encrypted secrets file                                |
| props.conf         | Yes              | Structures the modular input json events for ingest into Splunk indexers |
| searchbnf.conf     | Yes              | SPL help for custom commands                                 |
| server.conf        | Yes              | Configured [sshclustering] stanza for replicating custom .conf files across search head cluster deployments |
| splunk_create.conf | Yes              | Generated by @splunk/create when beginning React UI project  |


#### Custom Commands

Documentation on the custom commands can be found in the attached helpdocs folder.

| Command    | Type       | Description                                                  |
| ---------- | ---------- | ------------------------------------------------------------ |
| apiconnect | Generating | Sends adhoc GET/POST requests to API endpoints for generating new Splunk data. |
| joinapi    | Streaming  | Enhances existing Splunk events with adhoc API joins. Only supports GET requests, currently. |

## DEPENDENCIES

| Type       | Name                   | Description                                                  |
| ---------- | ---------------------- | ------------------------------------------------------------ |
| Role       | admin                  | Uses admin role by default for configuring API endpoints for modular inputs and custom API commands |
| Capability | list_storage_passwords | Required capability to use custom commands. Needed to read API passwords from passwords.conf |

## DEVELOPER

​    Authored by Joshua Stratton at the Pacific Northwest National Laboratory, operated by Battelle for the U.S. Department of Energy.

## SUPPORT

​   Important: External suggestions regarding modifications or support for this application, will only be considered when they solve challenges facing the operations and monitoring of Pacific Northwest National Laboratory assets.

​   Contact: joshua.stratton@pnnl.gov
