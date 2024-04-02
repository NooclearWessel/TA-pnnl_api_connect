## API Command Help

## About
   apiconnect is an SPL-based API tool useful for sending GET/POST requests to API endpoints and displaying the results in Splunk.

## Input fields for custom command
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |  Option          | Required  | Description                                                                                                   |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   api            |    Yes    | Configuration defined in app to use for building API connection                                               |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   method         |    No     | GET/POST. Defaults to POST                                                                                    |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   endpoint       |    No     | API endpoint to attach to the API configuration. Defaults to the base URL                                     |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   json           |    No     | Payload submitted with the request                                                                            |
   |                  |           |   Example: json="{'my_filter':{'filter':[{'field':'group_type','includes':['MyGroup']}]},'limit':5}"          |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   headers        |    No     | Additional headers to apply besides JSON formatting. Structure like this: "{key: value, key: value}"          |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   csv            |    No     | If the response is in CSV format, convert it to JSON. When set to 'true', event_key is automatically set to   |
   |                  |           |    'value' and cannot be overridden.                                                                          |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   event_path     |    No     | Path to the keys used to separate payload into events. Separate keys by forward slashes.                      |
   |                  |           |    Example: value/0/issues                                                                                    |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   next_location  |    No     | Location of next_key for paged events (HEADER/BODY)                                                           |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   next_key       |    No     | JSON key in response with instructions to pull additional results from large resultsets                       |
   |                  |           |    Example #1: @odata.nextLink                                                                                |
   |                  |           |    Example #2: links/next                                                                                     |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   useproxy       |    No     | Tells Splunk to use the configured proxy if needed. Should mostly be false. The search heads pass requests    |
   |                  |           |    through proxy01 (true/false)                                                                               |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   limit          |    No     | Limits the number of results returned by the API. Due to paging, using just $top will still result in every   |
   |                  |           |    event being returned but the paging will be smaller. Use limit to actually limit the results. Can be used  |
   |                  |           |    in conjunction with $top for faster searches and lower search costs.                                       |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   debug          |    No     | Prints debug logging                                                                                          |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |

## Usage Exmaples
   | apiconnect api="Microsoft Graph OAuthV2" method=GET endpoint="v1.0/admin/serviceAnnouncement/healthOverviews?$expand=issues" limit=1 event_path="value/0/issue"
   | apiconnect api="Microsoft Graph OAuthV2" endpoint="v1.0/users/my.email@myco.com" event_path="value" next_location=BODY next_key="@odata.nextLink"
   | apiconnect api="Microsoft Graph OAuthV2" endpoint="beta/reports/getSharePointActivityUserCounts(period='D7')" query="$format=application/json" event_path="value" next_key="@odata.nextLink"

   | apiconnect api="apiconfig" method=POST endpoint=api/someendpoint json="{'myfilter':{'filter':[{'field':'type','includes':['sometext']}]},'limit':5}" event_path=data next_location=BODY next_key=next_page_token limit=15

## api_configs.conf
   The apiconnect command requires a configuration and credentials to make the connection. These are keyed through the input page in the app.

   [Microsoft Graph OAuthV2]
   disabled = false
   provider = Microsoft
   baseurl = https://graph.microsoft.com
   authurl = https://login.microsoftonline.com/mytenantid.../oauth2/v2.0/token
   scope = https://graph.microsoft.com/.default
   authtype = OAuth 2.0
   username = myclientid...

## Validation
   Feedback to users can be done with self.write_error or self.write_
   self.write_error("Graph stanza missing in api_configs.conf")

## Logging
   Any logging should be done using the Splunk logging function
      self.logger.warning('apiconnect: Begin API search')
