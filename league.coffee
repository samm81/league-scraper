prevIDFile = process.argv[2]
outFile = process.argv[3]

if prevIDFile is undefined or outFile is undefined
    console.log "Usage: node league.js [id file] [data file]\n" +
    "output file headers:\n" +
    "summoner id, rank, points, cs per game, kills per game, assists per game, turrets per game, win ratio, number of games\n"
    throw "Invalid parameters error"

fs = require 'fs'
statsOut = fs.createWriteStream outFile, {
    flags: 'a',
    encoding: 'ascii'
}
prevIDOut = fs.createWriteStream prevIDFile, {
    flags: 'a',
    encoding: 'ascii'
}

LolApi = require 'leagueapi'
LolApi.init 'd3551528-1503-4e23-91ab-b070c96df4a5'
#LolApi.setRateLimit 10, 500

maxID = 10000000

tierToPoints = { "BRONZE":0, "SILVER":500, "GOLD":1000, "PLATINUM":1500, "DIAMOND":2000, "CHALLENGER":2500, "MASTER":3000 }
divisionToPoints = { "V":0, "IV":100, "III":200, "II":300, "I":400 }

writeStat = (stat) ->
    statsOut.write stat, ((err) -> throw err if err)

getRank = (summonerID) -> LolApi.getLeagueEntryData summonerID, ((error, data) ->
    if not error
        ranked = data[summonerID][0]
        if ranked isnt null and ranked.queue is "RANKED_SOLO_5x5"
            console.log "...had data"
            tier = ranked.tier
            division = ranked.entries[0].division
            leaguePoints = ranked.entries[0].leaguePoints
            rank = tier + " " + division
            if tier is "CHALLENGER"
                division = "V"
            points = tierToPoints[tier] + divisionToPoints[division] + leaguePoints
            writeStat "" + summonerID + ", " + rank + ", " + points + ", "
            getCSRatioAndNumGames summonerID)

getRanked = (data) ->
    ranked = null
    for datum in data
        if datum.playerStatSummaryType is "RankedSolo5x5"
            ranked = datum
    ranked

getCSRatioAndNumGames = (summonerID) -> LolApi.Stats.getPlayerSummary summonerID, 4, ((error, data) ->
    ranked = getRanked data
    if ranked isnt null
        wins = ranked.wins
        losses = ranked.losses
        games = wins + losses
        winRatio = wins / games
        winRatio = winRatio.toFixed 3
        cs = ranked.aggregatedStats.totalMinionKills
        csPerGame = cs / games
        csPerGame = csPerGame.toFixed 3
        kills = ranked.aggregatedStats.totalChampionKills
        killsPerGame = kills / games
        killsPerGame = killsPerGame.toFixed 3
        assists = ranked.aggregatedStats.totalAssists
        assistsPerGame = assists / games
        assistsPerGame = assistsPerGame.toFixed 3
        turrets = ranked.aggregatedStats.totalTurretsKilled
        turretsPerGame = turrets / games
        turretsPerGame = turretsPerGame.toFixed 3
        writeStat csPerGame + ", " + killsPerGame + ", " + assistsPerGame + ", " + turretsPerGame + ", " + winRatio + ", " + games + "\n"
    else
        writeStat "NoRanked\n")

writeID = (id) ->
    prevIDOut.write "\n" + id, ((err) -> throw err if err)

processNextID = (prevIDs) ->
    id = Math.floor(Math.random() * maxID + 1)
    console.log id
    if id not in prevIDs
        console.log "...was not previously processed"
        getRank id
        prevIDs.push id
        writeID id
    else
        console.log "...was previously processed"
    setTimeout (() -> processNextID(prevIDs)), 1400

readPrevIDs = () ->
    console.log "loading previous ids..."
    fs.readFile prevIDFile, 'ascii', ((err, data) ->
        throw err if err
        prevIDStrings = data.split "\n"
        prevIDs = []
        for prevIDString in prevIDStrings
            prevIDs.push (parseInt prevIDString)
        console.log "...loaded " + prevIDs.length + " ids"
        processNextID prevIDs)

importedIDs = []
importOldFile = (importFile) ->
    console.log "importing previous file..."
    fs.readFile importFile, 'ascii', ((err, data) ->
        throw err if err
        oldDataStrings = data.split "\n"
        i = 0
        for oldDataString in oldDataStrings
            id = (oldDataString.split ",")[0]
            importedIDs.push id )

processNextImportedID = (index) ->
    id = importedIDs[index]
    console.log "importing #{id}"
    getRank id
    writeID id
    setTimeout (() -> processNextImportedID(index + 1)), 3000

if process.argv[4] is "-import"
    importOldFile(process.argv[5])
    setTimeout (() -> processNextImportedID(0)), 5000
else
    readPrevIDs()
