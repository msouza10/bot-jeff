# Liquipedia API v3
Documentation API v3
The v3 API is OpenAPI compliant, you can find the OpenAPI documentation here!
All LiquipediaDB API calls have a base url of https://api.liquipedia.net/api.
All requests have to be made as GET requests.
Each API call needs the parameter wiki and the API key in the Authorization header like Apikey ThisIsALongStringThatIsOurExampleApiKey. Multi-wiki calls can be done by pipe-separating (|) wiki names, API keys can be obtained on the API keys page (ask your manager if you don't have access).
On failed requests the API will return a non-200 http status code.
There is a chance duplicates will be in the API, filter the results yourself or use a relevant groupby clause.
Other parameters have to be submitted as query parameters in the url.
Your client must accept gzip encoding.
When doing multi-wiki requests, mind that all of limit, offset, order and groupby are done on a per wiki basis.
The return value of a proper API call is a json object with up to 3 keys:

result: The result of the query as an array of objects. This key will be an empty array on invalid requests.
error (optional): Invalid API calls will have this key to tell you what went wrong. This key is an array of strings.
warning (optional): We will use this to notify you of non-fatal issues with your request. Examples for this are deprecations, or if the API struggled to return data from some page. If this unexpectedly happens repeatedly, feel free to notify us about it. This key is an array of strings.
Example result:

{
    "result": [
        {
            "id": "TaeJa",
            "localizedname": "윤영서",
            "name": "Yun Young Seo",
            "nationality": "South Korea"
        },
        {
            "id": "TLO",
            "localizedname": "",
            "name": "Dario Wünsch",
            "nationality": "Germany"
        }
    ]
}
Filtering results
Most API endpoints give you a multitude of filters. A lot of the syntax is heavily based on SQL, so developers will feel at home rather quickly. These parameters need to also be supplied as GET parameters. The following parameters can be used for filtering:

limit: A simple integer to define the amount of results wanted. If less than limit results exist, all results are returned. The default for this is 20, the maximum is 1000.
offset: A simple integer to define the offset. If specified, the first offset results will be omitted. The default is 0.
conditions: Conditions for the query can be supplied by using this key. The format uses [[]] as delimiters and works as [[columnname::columnvalue]]. Comparisions can be done like :: (equals), ::! (not equals), ::< (lower than) or ::> (greater than).
Subkeys in the json fields can be used by appending the subkey to the column name with an underscore. Do not depend on subkeys existing, as they will not always be guaranteed to be available. Conditions can be used with AND or OR and can be grouped with parentheses. An example condition could look like this: [[date::>2017-11-14]] AND [[date::<2017-12-14]] AND ([[liquipediatier::1]] OR [[type::!online]]) AND [[extradata_key::test]]. You can also use date functions but only on date type columns like [[birthdate_year::1995]] AND [[birthdate_month::2]]. Available date functions are: YEAR(), MONTH(), DAY(), HOUR(), MINUTE(), SECOND()
query: A comma-separated list of datapoints you want returned. If omitted all datapoints of an object will be returned. The functions COUNT(), SUM(), AVG(), MAX() and MIN() can be used with numerical columns like so: sum::prizemoney. The value would then be available as sum_prizemoney. You can also use YEAR(), MONTH(), DAY(), HOUR(), MINUTE(), SECOND() on date columns like so: month::birthdate. The value would then be available as month_birthdate
order: The way you want your query ordered similar to how ordering in SQL works. Both the name of the datapoint and the sorting direction need to be supplied, eg id ASC, name ASC.
groupby: The way you want your query grouped similar to how grouping in SQL works. Both the name of the datapoint and the grouping direction need to be supplied, eg id ASC, name ASC.
Data types
The Liquipedia DB API currently supports querying of the following data types:

Broadcasters via /v3/broadcasters
Companies via /v3/company
Datapoints via /v3/datapoint
External Media Links via /v3/externalmedialink
Matches via /v3/match
Placements via /v3/placement
Players via /v3/player
Series via /v3/series
Squad Players via /v3/squadplayer
Standings Entry via /v3/standingsentry
Standings Table via /v3/standingstable
Teams via /v3/team
Tournaments via /v3/tournament
Transfers via /v3/transfer
Team Templates via /v3/teamtemplate
List of Team Templates via /v3/teamtemplatelist
Available wikis
The following wikis are currently available in the API, depending on your organisations limits:

Age of Empires as ageofempires
Apex Legends as apexlegends
Arena FPS as arenafps
Artifact as artifact
Auto Chess as autochess
Battalion 1944 as battalion
Battlerite as battlerite
Brawlhalla as brawlhalla
Brawl Stars as brawlstars
Call of Duty as callofduty
Chess as chess
Clash of Clans as clashofclans
Clash Royale as clashroyale
Counter-Strike as counterstrike
Critical Ops as criticalops
CrossFire as crossfire
Deadlock as deadlock
Dota 2 as dota2
EA Sports FC as easportsfc
Fighting Games as fighters
Formula 1 as formula1
Fortnite as fortnite
Free Fire as freefire
GeoGuessr as geoguessr
GOALS as goals
Halo as halo
Hearthstone as hearthstone
Heroes of the Storm as heroes
Honor of Kings as honorofkings
Hub as hub
Identity V as identityv
Illuvium as illuvium
Lab as lab
League of Legends as leagueoflegends
Magic: The Gathering as magic
Marvel Rivals as marvelrivals
Mobile Legends: Bang Bang as mobilelegends
Naraka as naraka
Omega Strikers as omegastrikers
osu as osu
Overwatch as overwatch
Paladins as paladins
Pokémon as pokemon
PUBG as pubg
PUBG Mobile as pubgmobile
Rainbow Six as rainbowsix
Rematch as rematch
Rocket League as rocketleague
Legends of Runeterra as runeterra
Rocket League Sideswipe as sideswipe
Sim Racing as simracing
Smash as smash
SMITE as smite
Splatoon as splatoon
Splitgate as splitgate
Star Wars: Squadrons as squadrons
StarCraft Brood War as starcraft
StarCraft 2 as starcraft2
Stormgate as stormgate
Escape from Tarkov: Arena as tarkovarena
Team Fortress as teamfortress
Tetris as tetris
Teamfight Tactics as tft
The Finals as thefinals
TrackMania as trackmania
Dota Underlords as underlords
VALORANT as valorant
Warcraft as warcraft
War Thunder as warthunder
Wildcard as wildcard
Wild Rift as wildrift
World of Tanks as worldoftanks
World of Warcraft as worldofwarcraft
Zula as zula