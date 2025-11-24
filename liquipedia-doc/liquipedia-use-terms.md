Liquipedia API Terms of Use
General
The following terms of use apply additionally to both the MediaWiki API as well as the LiquipediaDB API:

Re-use / cache your API results for as long as possible - do not issue repeated requests which return the same data.
Liquipedia content is licensed under CC-BY-SA 3.0, which requires that you attribute Liquipedia as the source of your data. See Liquipedia:Copyrights for more information.
Automated access to non-API endpoints (ie, generated HTML pages) is not permitted.
Liquipedia reserves the right to do any of the following, at any time, without notice: (1) to modify, suspend or terminate operation of or access to the Liquipedia API, or any portion of the API, for any reason; and (2) to interrupt the operation of the API, or any portion of the API, as necessary to perform routine or non-routine maintenance, error correction, or other changes.
LiquipediaDB API
Upon approved request Liquipedia grants access to the information in our wikis through the LiquipediaDB API for use in your own projects. In order to keep the wiki API available for all users, we ask that you follow these terms of use.

Rate limit all requests to no more than 60 requests per 1 hour.
Follow the documentation available after logging in to the LiquipediaDB Dashboard.
Do not share your API Keys with third parties.
MediaWiki API
Liquipedia is pleased to provide free access to the information in our wikis through the MediaWiki API for use in your own projects. In order to keep the wiki API available for all users, we ask that you follow these terms of use.

Rate limit all HTTP requests to no more than 1 request per 2 seconds. API "action=parse" requests should not exceed 1 request per 30 seconds as these are more resource intensive.
Use a custom HTTP "User-Agent" header in your requests that identifies your project / use of the API, and includes contact information. Example: "LiveScoresBot/1.0 (http://www.example.com/; email@example.com)". Generic user agents such as "Python-requests", "Go-http-client", etc are more likely to be blocked.
Your client must accept gzip encoding (supply an "Accept-Encoding: gzip" HTTP header with every request).
Only use authenticated (logged in) API calls when necessary - this allows improved caching of commonly requested endpoints.
If you have any questions about the API or these terms of use, please contact us on Discord. Violations of these terms can result in automated temporary IP bans (you can unblock yourself by completing a CAPTCHA); repeated triggering of temporary bans may result in them becoming permanent.