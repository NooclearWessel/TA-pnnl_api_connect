## API Command Help

## About
   joinapi is an SPL-based API tool useful for appending API results to a set of data events

## Input fields for custom command
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |  Option          | Required  | Description                                                                                                   |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   api            |    Yes    | Configuration defined in app to use for building API connection                                               |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   endpoint       |    No     | Endpoint can be provided as a command string or event field. Field name defaults to 'endpoint' in the event   |
   |                  |           |    list.                                                                                                      |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   headers        |    No     | Additional headers to apply besides JSON formatting. Structure like this: "{key: value, key: value}"          |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   csv            |    No     | If the response is in CSV format, convert it to JSON. When set to 'true', event_key is automatically set to   |
   |                  |           |    'value' and cannot be overridden.                                                                          |
   | ---------------- | --------- | ------------------------------------------------------------------------------------------------------------- |
   |   event_path     |    No     | Path to the keys used to separate payload into events. Separate keys by forward slashes.                      |
   |                  |           |    Example: value/0/issues                                                                                    |
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
   | joinapi api="Microsoft Graph OAuthV2" endpoint="v1.0/admin/serviceAnnouncement/healthOverviews?$expand=issues" limit=1 event_path="value/0/issue"
   | joinapi api="Microsoft Graph OAuthV2" endpoint=endpoint event_path="value" next_key="@odata.nextLink"
   | joinapi api="Microsoft Graph OAuthV2" event_path="value" next_key="@odata.nextLink"

## api_configs.conf
   The joinapi command requires a configuration and credentials to make the connection. These are keyed through the input page in the app.

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
      self.logger.warning('joinapi: Begin API search')
