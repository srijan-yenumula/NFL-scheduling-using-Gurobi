#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  9 01:22:34 2018

Products Summary
-Dictionary of Home Games: homeGames
-Dictionary of Away Games: awayGames
-Dictionary of dictionaries by division: Div
-Dictionary by conference: Conf
-List of Team Data: Teams
-Tuplelist of Game Data: season
-Testing of Tuplelist: see code at the bottom

"""

import csv, sqlite3
from gurobipy import *


#### creating the connection with the database 
myConn=sqlite3.connect('NFL_DB.db')
myCursor=myConn.cursor()

myData=[]
with open ('GameVariables_2018.csv','r') as myFile:
    myReader=csv.reader(myFile)
    myReader.next()
    for row in myReader:
         myData.append((row[0].strip(),row[1].strip(),int(float( row[2].strip())),row[3].strip(),row[4].strip(),int(float(row[5].strip()))))

#### create table game variables 
SQLString="""CREATE TABLE IF NOT EXISTS tblgamevariables
(Away_Team STRING, Home_Team STRING, Week INTEGER, Slot STRING, Network STRING, Qual_Points INTEGER);"""
myCursor.execute(SQLString)
myConn.commit()

# drop table to clear prvs data 
SQLString="DELETE FROM tblgamevariables;"
myCursor.execute(SQLString)
myConn.commit()

##### insert values into tabelgamevariable
SQLString="""INSERT INTO tblgamevariables VALUES(?,?,?,?,?,?);"""
myCursor.executemany(SQLString,myData)
myConn.commit()

myData=[]
with open ('NETWORK_SLOT_WEEK_2018.csv','r') as myFile:
    myReader=csv.reader(myFile)
    # Don't skip first line since no headers
    for row in myReader:
         myData.append((int(float(row[0].strip())),row[1].strip(),row[2].strip()))


#### create table Network_Slots 
SQLString="""CREATE TABLE IF NOT EXISTS tblNetwork_Slots
(Week INTEGER, Slot STRING, Network STRING);"""
myCursor.execute(SQLString)
myConn.commit()

# drop table to clear prvs data 
SQLString="DELETE FROM tblNetwork_Slots;"
myCursor.execute(SQLString)
myConn.commit()

##### insert values into tabelnetworkslots
SQLString="""INSERT INTO tblNetwork_Slots VALUES(?,?,?);"""
myCursor.executemany(SQLString,myData)
myConn.commit()

# creat the team variable data 
myData=[]
with open ('TEAM_DATA_2018.csv','r') as myFile:
    myReader=csv.reader(myFile)
    myReader.next()
    for row in myReader:
         myData.append((row[0].strip(),row[1].strip(),row[2].strip(),int(float(row[3].strip())),int(float(row[4].strip()))))

#### create table TEAM_DATA variables 
SQLString="""CREATE TABLE IF NOT EXISTS tblTeam_data
(Team STRING, Conf STRING, Div INTEGER, Time_Zone INTEGER, Quality INTEGER);"""
myCursor.execute(SQLString)
myConn.commit()

# drop table to clear tbelTeam_Data 
SQLString="DELETE FROM tblTeam_data;"
myCursor.execute(SQLString)
myConn.commit()

##### insert values into tabelgamevariable
SQLString="""INSERT INTO tblTeam_data VALUES(?,?,?,?,?);"""
myCursor.executemany(SQLString,myData)
myConn.commit()

#### create the dictionqry of away games
sqlString = "SELECT Away_Team, Home_Team FROM tblgamevariables GROUP BY Away_Team, Home_Team;"
myCursor.execute(sqlString)
away_team = myCursor.fetchall()

awayGames={}
for row in away_team:
    awayGames.setdefault(row[0], [])
    awayGames[row[0]].append(row[1])

#### create the dictionary of home games
sqlString = "SELECT Home_Team, Away_Team FROM tblgamevariables GROUP BY Home_Team, Away_Team;"
myCursor.execute(sqlString)
home_team = myCursor.fetchall()

homeGames={}
for row in home_team:
    if row[0] != 'BYE':
          homeGames.setdefault(row[0], [])
          homeGames[row[0]].append(row[1])
        
# Create a dictionary of dictionaries of teams by division
sqlString = "SELECT * FROM tblTeam_data;"
myCursor.execute(sqlString)
teamData = myCursor.fetchall()

Div={}
for row in teamData:
    Div.setdefault(row[1], {})
    Div[row[1]].setdefault(row[2], [])
    Div[row[1]][row[2]].append(row[0])

# Create dictionary of teams by conferance
Conf={}
for row in teamData:
    Conf.setdefault(row[1], [])
    Conf[row[1]].append(row[0])

# Create a list of data by team
Teams=[]
for row in teamData:
    Teams.append(row[0])

# Create tuplelist for game variables without quality  
sqlString = "SELECT Away_Team, Home_Team, Week, Slot, Network FROM tblgameVariables;"
myCursor.execute(sqlString)
gameData = myCursor.fetchall()
season =tuplelist(gameData)

# Create tuplelist for game variables without quality  
sqlString = "SELECT Away_Team, Home_Team, Week, Slot, Network, Qual_Points FROM tblgameVariables;"
myCursor.execute(sqlString)
gameData = myCursor.fetchall()
gameInfo={}
for row in gameData:
    gameInfo[row[0], row[1], row[2], row[3], row[4]] = row[5]

# Creating time zone dictionery
sqlString = "SELECT TEAM, Time_Zone FROM tblTeam_Data;"
myCursor.execute(sqlString)
TimeList = myCursor.fetchall()
timeZone = {}
for row in TimeList:
    timeZone[row[0]] = row[1]

#### relabel dictionary
myCursor.close()
myConn.close()

# Build Model
NFL = Model()
NFL.modelSense = GRB.MAXIMIZE
NFL.update()

NFL.setParam('TIMELimit', 40) # Change max time limit
NFL.setParam('MIPFOCUS',1) # Emphasize heuristics
NFL.setParam('MIPGAP',0.04) # Change tolarance level on optimal solution

# Set objective function
games = {}
for a, h, w, s, n in gameInfo:
    cname = 'x(%s_%s_%s_%s_%s)' % (a, h, w, s, n)
    games[a, h, w, s, n] = NFL.addVar(obj = gameInfo[a, h, w, s, n], lb=  0, 
                                   vtype = GRB.BINARY,
                                   name = cname)
NFL.update()

# Define Constraints
myConstrDict={}

# Constraint 1
for a in Teams:
    for h in awayGames[a]:
        cName = '01_Each_Game_Once_%s_%s' % (a, h)
        myConstrDict[cName] = NFL.addConstr((quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select(a, h, '*', '*', '*'))) == 1, name = cName)
NFL.update() 

# Constraint 2 
for t in Teams:
    for w in range(1,18):
        cName = '02_Each_Team_Once_%s_%s' % (t, w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select(t, '*', w, '*', '*')) +
                   quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', t, w, '*', '*')) == 1, name = cName)
NFL.update() 

# Constraint 3 is unnecessary due to problem/variable structure

# Constraint 4
for w in range(4,12):
    cName = '04_Six_Byes_Week_%s' % (w)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', 'BYE', w, 'SUNB', 'BYE')) <= 6, name = cName)
NFL.update() 

# Constraint 5
earlyByes = ['MIA', 'TB']
for t in earlyByes:
    cName = '05_No_Repeat_Early_Bye_%s' % (t)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select(t, 'BYE', 4, '*', '*')) == 0, name = cName)
NFL.update() 

# Constraint 6
for w in range(1,17):
    cName = '06a_One_Thur_Game_Week_%s' % (w)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', '*', w, 'THUN', '*')) == 1, name = cName)
NFL.update() 

for w in range(17,18):
    cName = '06b_No_Thur_Game_Week_%s' % (w)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', '*', w, 'THUN', '*')) == 0, name = cName)
NFL.update() 

# Constraint 7
for w in range(16,17):
    cName = '07_Two_Sat_Game_Week_%s_Early' % (w)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', '*', w, 'SATE', '*')) == 1, name = cName)
NFL.update() 

for w in range(16,17):
    cName = '07_Two_Sat_Game_Week_%s_Late' % (w)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', '*', w, 'SATL', '*')) == 1, name = cName)
NFL.update() 

# Constraint 8
for w in range(1,17):
    cName = '08a_One_Sun_Week_%s_DoubleH' % (w)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', '*', w, 'SUND', '*')) == 1, name = cName)
NFL.update()

for w in range(17,18):
    cName = '08b_Two_Sun_Week_%s_DoubleH' % (w)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', '*', w, 'SUND', '*')) == 2, name = cName)
NFL.update()

# Constraint 9
for w in range(1,17):
    cName = '09a_One_Sun_Week_%s_SUNN' % (w)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', '*', w, 'SUNN', '*')) == 1, name = cName)
NFL.update()

w=17
cName = '09b_No_Sun_Week_%s_SUNN' % (w)
myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', '*', 17, 'SUNN', '*')) == 0, name = cName)
NFL.update()

#Constraint 10
w=1
cName = '10a_One_Mon_Week_%s_MON1' % (w)
myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', '*', w, 'MON1', '*')) == 1, name = cName)
NFL.update()
cName = '10a_One_Mon_Week_%s_MON2' % (w)
myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', '*', w, 'MON2', '*')) == 1, name = cName)
NFL.update()

wCoast = ['SEA', 'SF', 'LAR', 'OAK', 'LAC']
notWestTeams = [x for x in Teams if x not in wCoast]
for t in notWestTeams:
    cName = '10b_West_Coast_Only_not_%s' % (t)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', t, 1, 'MON2', '*')) == 0, name = cName)
NFL.update()

for w in range(2,17):
    cName = '10c_One_Mon_Night_Games_Week_%s' % (w)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[a,h,w,s,n] for a,h,w,s,n in season.select('*','*',w,'MON1','*'))==1,name=cName)
NFL.update() 

## Hard Constraints
# No need for Constraint 11 -> no early west coast games are in the input data

# Constraint 12
for w in range(1,15):
    for t in Teams:
        w2 = [x for x in range(w, w+4)]
        cName = '12a_No_More_than_3_Cons_Road_Games_%s_Starting_Week_%s' % (t, w)
        myConstrDict[cName] = NFL.addConstr((quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select(t, '*', w2, '*', '*')) ) <= 3, name = cName)
NFL.update() 

#NFL.write('mylp.lp')


for w in range(1,15):
    for t in Teams:
        w2 = [x for x in range(w, w+4)]
        cName = '12b_No_More_than_3_Cons_Home_Games_%s_Starting_Week_%s' % (t, w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', t, w2, '*', '*')) <= 3, name = cName)
NFL.update() 

# Constraint 13
for w in range(1,13):
    for t in Teams:
        w2 = [x for x in range(w, w+6)]
        cName = '13a_At_Least_Two_Road_Games_10_Week_%s_Starting_Week_%s' % (t, w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select(t, '*', w2, '*', '*')) >= 2, name = cName)
NFL.update() 

for w in range(1,13):
    for t in Teams:
        w2 = [x for x in range(w, w+6)]
        cName = '13b_At_Least_Two_Home_Games_6_Week_%s_Starting_Week_%s' % (t, w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', t, w2, '*', '*')) >= 2, name = cName)
NFL.update() 

# Constraint 14
for w in range(1,9):
    for t in Teams:
        w2 = [x for x in range(w, w+10)]
        cName = '14a_At_Least_Four_Road_Games_10_Week_%s_Starting_Week_%s' % (t, w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select(t, '*', w2, '*', '*')) >= 4, name = cName)
NFL.update() 

for w in range(1,9):
    for t in Teams:
        w2 = [x for x in range(w, w+10)]
        cName = '14b_At_Least_Four_Home_Games_10_Week_%s_Starting_Week_%s' % (t, w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', t, w2, '*', '*')) >= 4, name = cName)
NFL.update() 

# Constraint 15
for t in Teams:
    for w in range(2,17):
        cName = '15_Home_Week_Before_Thurs_Road_%s_Week_%s' % (t, w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select('*', t, w-1, '*', '*')) 
        - quicksum(games[a, h, w, s, n] for a, h, w, s, n in season.select(t, '*', w, 'THUN', '*')) >= 0, name=cName)
NFL.update()

# Constraint 16
Link16 = {}
for t in Teams:
    for h in awayGames[t]:
        if h!= 'BYE':
            for w in range(5,13):
                cName = 'Link16(%s_%s_%s)' % (t, h, w)
                Link16[t,h,w] = NFL.addVar(obj = 0, vtype=GRB.BINARY, name = cName)
NFL.update() 
                
for t in Teams:
    for h in awayGames[t]:
        if h!= 'BYE':
            for w in range(4,12):                    
                cName = '16_No_More_Than_2_After_Bye_For_%s_%s_in_%s' % (t, h, w)
                myConstrDict[cName] = NFL.addConstr(games[h,'BYE', w, 'SUNB', 'BYE'] + quicksum(games[a, h, i, s, n] for a, h ,i,s,n
                            in season.select(t, h, w+1,'*','*')) <= 1 + Link16[t,h,w+1], name=cName)
NFL.update()

for t in Teams:
    cName = '16_Cap_%s' % (t)
    myConstrDict[cName] = NFL.addConstr(quicksum(Link16[t, h, w] for h in awayGames[t] if h != 'BYE' for w in range(5,13)) <= 2, name=cName)
NFL.update()


## Soft Constraints
# Constraint 17
pen17_home = {}
pen17_away = {}
for t in Teams:
    for w in range(4,15):
        cName = 'PEN17_home_Week_%s_%s' %(t,w)
        pen17_home[t,w] = NFL.addVar(obj=-3,vtype=GRB.BINARY,name =cName)
NFL.update()       
for t in Teams:
    for w in range(4,15):
        cName = 'PEN17_away_Week_%s_%s' %(t,w)       
        pen17_away[t,w] = NFL.addVar(obj=-3,vtype=GRB.BINARY, name=cName)
NFL.update()

for t in Teams:
    cName = '17_home_PenCapacity_away_PenCapacity_%s_%s'%(t,w)
    myConstrDict[cName] = NFL.addConstr(quicksum(pen17_home[t,w] for w in range(4,15))+quicksum(pen17_away[t,w] for w in range(4,15)) <=1,name = cName)
NFL.update()

for w in range(4,15):
    for t in Teams:
        cName = '17a_No3Consecutive_AWAY_Games_Week_%s_%s' %(t,w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[a,h,x,s,n] for a,h,x,s,n in season.select(t,'*','*','*','*') if x in range(w,w+3))<=2 +pen17_away[t,w], name=cName)
NFL.update()

for w in range(4,15):
    for t in Teams:                        
        cName = '17b_No3Consecutive_HOME_Games_Week_%s_%s'%(t,w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[a,h,x,s,n] for a,h,x,s,n in season.select('*',t,'*','*','*') if x in range(w,w+3))<=2 +pen17_home[t,w] , name=cName)
NFL.update()

# Constraint 18
pen18 = {}
for t in Teams:
    for w in range(1,17):
        cName = 'PEN18_week_%s_%s' %(t,w)
        pen18[t,w] =NFL.addVar(obj=-3,vtype=GRB.BINARY,name= cName)
NFL.update()
  
for t in Teams:
    tempList18 = []
    for x in awayGames[t]:
        if x != 'BYE':
            if abs(timeZone[t]-timeZone[x]) > 1:
                tempList18.append(x)
    for w in range(1,17):
        cName = '18_No_Consec_Road_Games_1TimeZone_%s_%s_%s' %(t,x,w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[t,x,i,s,n] for t,x,i,s,n in season.select(t,tempList18,'*','*','*') if i in (w,w+1)) <= 1 + pen18[t,w],name=cName)
NFL.update()

# Constraint 19
pen19 = {}
for t in Teams:
    for w in range(1,17):
        cName = 'PEN19_WEEK_%s%s' %(t,w)
        pen19[t,w] = NFL.addVar(obj=-3,vtype=GRB.BINARY,name= cName)
NFL.update()
        
for t in Teams:
    tempList19 = []
    for x in awayGames[t]:
        if x != 'BYE':
            if abs(timeZone[t]-timeZone[x]) > 1:
                tempList19.append(x)
    for w in range(1,17):
        cName = '19_No_THUN_Game1_TimeZone_From_Home_%s_%s_%s' %(t,x,w)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[t,x,w,s,n] for t,x,w,s,n in season.select(t,tempList19,w,'THUN','*')) <= 1 + pen19[t,w],name=cName)
NFL.update() 


# Constraint 20
pen20 = {}
for t in Teams:
    cName = 'PEN20_%s' %(t)
    pen20[t] = NFL.addVar(obj=-3,vtype=GRB.BINARY, name = cName)
NFL.update()

for t in Teams:
        cName = '20_NoTeam_Season_Opener_2Away_%s' %(t)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[t,h,w,s,n] for t,h,w,s,n in season.select(t,'*','*','*','*') if w in (1,2)) <= 1 + pen20[t],name=cName)
NFL.update()

# Constraint 21
pen21 = {}
for t in Teams:
    cName = 'PEN21_%s' %(t)
    pen21[t] = NFL.addVar(obj=-3,vtype=GRB.BINARY, name = cName)
NFL.update()

for t in Teams:
        cName = '21_No_Endof_Season_With_2Away_%s' %(t)
        myConstrDict[cName] = NFL.addConstr(quicksum(games[t,h,w,s,n] for t,h,w,s,n in season.select(t,'*','*','*','*') if w in (16,17)) <= 1 + pen21[t],name=cName)
NFL.update()

# Constraint 22
Pen22 = {}
for w in range(1,5):
    cname = 'Pen22_%s' % (w)
    Pen22[w] = NFL.addVar(obj =-3, vtype = GRB.BINARY,
                                   name = cname)
NFL.update() 

flTeams = ('TB', 'MIA', 'JAC')
for w in range(1,5):
    cName = '22_No_FL_Early_Games_Sept_%s' % (w)
    myConstrDict[cName] = NFL.addConstr(quicksum(games[t,h,w,s,n] for t,h,w,s,n in season.select('*',flTeams, w,'SUNE','*')) <= 0 + Pen22[w],name=cName)
NFL.update() 


# Check Model
NFL.write('mylp.lp')

# Solve Model
NFL.optimize()

# Print outputs to database
if NFL.Status == GRB.OPTIMAL:
    myConn = sqlite3.connect('NFL_DB.db')
    myCursor = myConn.cursor()
    nflSch = []
    for s in games:
        if games[s].x > 0.1: #0.1 instead of 0 to account for values slightly > 0
            nflSch.append((s[0], s[1], s[2], s[3], s[4]))
        

    # delete tblMill
    myCursor.execute('DROP TABLE IF EXISTS nflSol')
    
    # create the table    
    nflSol = """
                CREATE TABLE IF NOT EXISTS nflSol
                (Away_Team           TEXT,
                 Home_Team           TEXT,
                 Week                INTEGER,
                 Time_Slot           TEXT,
                 Network             TEXT);
                """
    myCursor.execute(nflSol)
    myConn.commit()
    
    # create the insert string
    sqlString = "INSERT INTO nflSol VALUES(?, ?, ?, ?, ?);"
    myCursor.executemany(sqlString, nflSch)    
    myConn.commit()
    
    myCursor.close()
myConn.close()
