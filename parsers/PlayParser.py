import pandas as pd






def parse_entry(entry):

    column_names = ["currentScore", "currentSetScore", "currentMatchScore"]
    matchData = pd.DataFrame(columns = column_names)

    gameData = entry.split(" ")
    gameData.append("E")
    MatchScoreL = 0
    MatchScoreR = 0
    SetScore = "0-0"
    check = True
    


    def updateMatchScore():  
        nonlocal MatchScoreL
        nonlocal MatchScoreR 
        if (int(SetScore[0]) > int(SetScore[2])): 
            MatchScoreL += 1
        if (int(SetScore[0]) < int(SetScore[2])):      
            MatchScoreR += 1


    for token in gameData:
        if "*" in token:   
            matchData_length = len(matchData)
            matchData.loc[matchData_length] = [token,SetScore, str(MatchScoreL) + "-" + str(MatchScoreR)]
            check = True
        elif token == "End" :
            updateMatchScore()
            matchData_length = len(matchData)
            matchData.loc[matchData_length] = [token,SetScore, str(MatchScoreL) + "-" + str(MatchScoreR)]
            check = True
        else:
            if token == "0-0":
                updateMatchScore()
            elif(check):
                matchData_length = len(matchData)
                matchData.loc[matchData_length] = ["EndGame",SetScore, str(MatchScoreL) + "-" + str(MatchScoreR)]
                check = False
            SetScore = token
    return matchData



