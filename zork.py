"""
Zork Mastodon Bot

AI6YR Ben - Nov 2022

This "bot" is a conceptual bot which can interact with users, and store a state of interaction with any number of users. 
The bot is driven off notifications from Mastodon on direct (follower only) mentions.

Logic is based on the "PY Edition" Zork here:
https://github.com/iamjawa/zork-py

"""
# imports 
import configparser
from mastodon import Mastodon
import time
import re

import re
clean = re.compile('<.*?>')

playerstate = {}

statedescription = { 4  :  "You are standing in an open field west of a white house, with a boarded front door.\n(A secret path leads southwest into the forest.)\nThere is a Small Mailbox.\nWhat do you do?",
                     8 :   "This is a forest, with trees in all directions. To the east, there appears to be sunlight.\nWhat do you do?",
                     9 :   "You are in a clearing, with a forest surrounding you on all sides. A path leads south.\nThere is an open grating, descending into darkness. \nWhat do you do?",
                     10 :  "You are in a tiny cave with a dark, forbidding staircase leading down.\nThere is a skeleton of a human male in one corner.\nWhat do you do? ",
                     11 : "You have entered a mud-floored room.\nLying half buried in the mud is an old trunk, bulging with jewels.\nWhat do you do? " }

commanddict = { 4 : { "take mailbox" : "It is securely anchored.",
                    "open mailbox" : "Opening the small mailbox reveals a leaflet.",
                    "go east" : "The door is boarded and you cannot remove the boards.",
                    "open door": "The door cannot be opened.",
                    "take boards": "The boards are securely fastened.",
                    "look at house": "The house is a beautiful colonial house which is painted white. It is clear that the owners must have been extremely wealthy.",
                    "go southwest": "LOOP 8",
                    "read leaflet": "Welcome to the Unofficial Mastodon Version of (a mini) Zork. Your mission is to find a Jade Statue."
                   },
                8 : { "go west": "You would need a machete to go further west.",
                    "go north": "The forest becomes impenetrable to the North.",
                    "go south": "Storm-tossed trees block your way.",
                    "go east": "LOOP 9"
                   },
                9 : { "go south": "You see a large ogre and turn around.",
                     "descend grating": "LOOP 10"
                   },
                10: { "descend staircase" : "LOOP 11",
                     "take skeleton" : "Why would you do that? Are you some sort of sicko?",
                     "smash skeleton" : "Sick person. Have some respect mate.",
                     "light up room": "You would need a torch or lamp to do that.",
                     "break skeleton": "I have two questions: Why and With What?",
                     "go down staircase" : "LOOP 11",
                     "scale staircase" : "LOOP 11",
                     "suicide": "You throw yourself down the staircase as an attempt at suicide. You die."
                   },
                11 : { "open trunk" : "You have found the Jade State and have completed your quest!" }}


# Load the config
config = configparser.ConfigParser()
config.read('config.ini')

# connect to mastodon
mastodonBot = Mastodon(
    access_token=config['mastodon']['access_token'],
    api_base_url=config['mastodon']['app_url']
)

print ("Starting Zork Bot")
lastpost = ""
while(1):
     notifications = mastodonBot.notifications()
     for note in notifications:
           print (note)
           message = ""
           #print("Notification ID:",note['id'],note['type'],note['created_at'],note['account'],note['status']) 
           print ("VISIBILITy: ", note['status']['visibility'])
           account = note['account']['acct']
           visibility = note['status']['visibility']
           replyinput =  note['status']['content']
           replyinputclean = re.sub(clean, '', replyinput)
           command = replyinputclean.replace("@zorkbot ","").lower()
           if (command == "reset") or (command=="restart"):
               showintro = 1
               statemachine = -1
               playerstate.pop(account)
           
           # don't do anything unless we're private. No reason to spew our game across the Fediverse   
           if (visibility == "direct"):
               statusid = note['status']['id']
               showintro = 0
               try:
                   statemachine = playerstate[account]
               except:
                   statemachine = 4
                   playerstate[account] = statemachine
                   showintro = 1
               if (not showintro):
                   try:  
                      message =  commanddict[statemachine][command]
                      firstfour = message[:4]
                      if (firstfour == "LOOP"):
                          print ("changing state")
                          statemachine = int(message[4:])
                          print (statemachine)
                          playerstate[account] = statemachine
                          message = ""
                   except:
                      message =  "I could not understand that command."
                   if (statemachine == 10):
                      if (command == "suicide"):
                          statemachine = -1
                          playerstate.pop(account)
                          # reset 
                          message = "\n\nYou are dead. Thanks for playing! You can play again by replying to this account."
                   elif (statemachine == 11):
                      if (command == "open trunk"):
                          statemachine = -1
                          playerstate.pop(account)
                          message = "\n\nYou won the game! Thanks for playing! You can play again by replying to this account."

               if (showintro):
                  #mastodonBot.status_post("@"+account + "\nWelcome to Zork - The Unofficial Mastodon Version. Please only sent us direct (mentioned acounts only) messages!", statusid,None,False,"direct") 
                  message = message + "\nWelcome to Zork - The Unofficial Mastodon Version. Send us direct (mentioned acounts only) messages to play the game!"
               if (statemachine > -1):
                   message = message+"\n\n"+statedescription[statemachine]
               mastodonBot.status_post("@"+account +"\n"+ message,statusid,None,False,"direct")
           mastodonBot.notifications_dismiss(note['id'])
                    
     time.sleep(2)
