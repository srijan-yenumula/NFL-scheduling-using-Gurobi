#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  9 01:22:34 2018

Products Summary
-List of teams: teams
-Dictionary of Home Games: homegames
-Dictionary of Away Games: awaygames
-Dictionary of dictionaries by division: Conf_Div
-Dictionary by conference: conf_div
-Dictionary of Team Data: teamData_dict
-Tuplelist of Game Data: gameData
-Testing of Tuplelist: see code at the bottom

@author: Srijan and Colin
"""

#### Products Summary
## List of teams: teams
## Dictionary of Home Games: homegames
## Dictionary of Away Games: awaygames
## Dictionary of dictionaries by division: Conf_Div
## Dictionary by conference: conf_div
## Dictionary of Team Data: teamData_dict
## Tuplelist of Game Data: gameData
## Testing of Tuplelist: see code at the bottom
    


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
with open ('NETWORK_SLOT_WEEK.csv','r') as myFile:
    myReader=csv.reader(myFile)
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


### creat the team variable data 
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

##### Create a list of teams
SQLString = "SELECT Team FROM tblTeam_data;"
myCursor.execute(SQLString)
teams_list = myCursor.fetchall()

teams=[]
for row in teams_list:
    teams.append(row[0])

#### create the dictionery of away games
sqlString = "SELECT Away_Team, Home_Team FROM tblgamevariables GROUP BY Away_Team, Home_Team;"
myCursor.execute(sqlString)
away_team = myCursor.fetchall()

awaygames={}
for row in away_team:
    awaygames.setdefault(row[0], [])
    awaygames[row[0]].append(row[1])



#### create the dictionary of home games
sqlString = "SELECT Home_Team, Away_Team FROM tblgamevariables GROUP BY Home_Team, Away_Team;"
myCursor.execute(sqlString)
home_team = myCursor.fetchall()

homegames={}
for row in home_team:
    homegames.setdefault(row[0], [])
    homegames[row[0]].append(row[1])
    
    
#####dictinary for division 
# Create a dictionary of teams by conference
sqlString = "SELECT * FROM tblTeam_data;"
myCursor.execute(sqlString)
teamData = myCursor.fetchall()

Conf_Div={}
for row in teamData:
    Conf_Div.setdefault(row[1], {})
    Conf_Div[row[1]].setdefault(row[2], [])
    Conf_Div[row[1]][row[2]].append(row[0])

# Create dictionary of teams by conferance
conf_dict={}
for row in teamData:
    conf_dict.setdefault(row[1], [])
    conf_dict[row[1]].append(row[0])

# Create a dictionary of data by team
teamData_dict={}
for row in teamData:
    teamData_dict[row[0]] = {'Conference': row[1], 'divison': row[2], 'Timezone': row[3], 'Quality': row[4]}

# Create tuplelist for game variables  
sqlString = "SELECT * FROM tblgameVariables;"
myCursor.execute(sqlString)
gameData = myCursor.fetchall()
gameData =tuplelist(gameData)



####### Expirement with tuplelist
# Print all of possible ARZ away game combinations
gameData.select('ARZ', '*', '*', '*', '*', '*')

# Print all possible DAL home games on ESPN
gameData.select('*', 'DAL', '*', '*', 'ESP', '*')

# Print all possible DAL Thanksgiving games
gameData.select('*', 'DAL', '*', 'THUL', '*', '*')

# Print all possible international games
gameData.select('*', '*', '*', '*', 'INT', '*')

myCursor.close()
myConn.close()