import requests
import json
import sqlite3
import datetime
import time
import vlc 
import sys
from dateutil.relativedelta import relativedelta

program_version = 1.00
database_file='database.db'
program_state = 0 
next_event=  datetime.datetime.now()
output_trigger=0

def getDate(offset):
    x = datetime.datetime.now()
    if (offset == 1 ):
        x = x + datetime.timedelta(days = 1)
    formattedTime = x.strftime("%d") + "-"+ x.strftime("%m") + "-"+ x.strftime("%Y")
    #formattedTime = "17-01-2023"
    #print(x.strftime("%d"))
    #print(x.strftime("%d"))
    #print(x.strftime("%m"))
    #print(x.strftime("%Y"))
    return formattedTime



def add_time( timing_data):
    query = "INSERT INTO prayer_times (Date, Fajr, Dhuhr, Asr, Maghrib, Isha) VALUES (?, ?, ?, ?, ?, ?);"
    connection = sqlite3.connect(database_file)
    cursor = connection.cursor()
    cursor.execute(query,  (timing_data["date"]["gregorian"]["date"],timing_data["timings"]["Fajr"],timing_data["timings"]["Dhuhr"],
    timing_data["timings"]["Asr"],timing_data["timings"]["Maghrib"],timing_data["timings"]["Isha"]))
    cursor.close()
    connection.commit()
    connection.close()

def update_status(next_timing):
    query = "UPDATE Settings SET setting1='" + next_timing +"';"
    connection = sqlite3.connect(database_file)
    cursor = connection.cursor()
    cursor.execute(query)
    cursor.close()
    connection.commit()
    connection.close()   


def connectAPI(dt_month, dt_year):
    r =requests.get('http://api.aladhan.com/v1/calendar?latitude=44.75286358770571&longitude=-63.665015163839975&method=2&month='+dt_month+'&year='+dt_year)
    y = json.loads(r.content)
    for i in y["data"]:
        print(i["date"]["gregorian"]["date"])
        print(i["timings"]["Fajr"])
        print(i["timings"]["Dhuhr"])
        print(i["timings"]["Asr"])
        print(i["timings"]["Maghrib"])
        print(i["timings"]["Isha"])
        add_time(i)
    
def clearDatabase():
    query = "DELETE FROM 'main'.'prayer_times';"
    connection = sqlite3.connect(database_file)
    cursor = connection.cursor()
    cursor.execute(query)
    cursor.close()
    connection.commit()
    connection.close()
    print ('database cleared')

def getDBStatus():
    query = "SELECT * FROM 'main'.'settings';"
    connection = sqlite3.connect(database_file)
    cursor = connection.cursor()
    cursor.execute(query)
    for row in cursor:
        return (row[2])


def getTiming():
    currentTime =  datetime.datetime.now()
    query = "SELECT * FROM 'main'.'prayer_times' WHERE Date = '" + getDate(0) +"';"
    connection = sqlite3.connect(database_file)
    cursor = connection.cursor()
    cursor.execute(query)
    timing_status =0
    for row in cursor:
        for n in range(2,7):
            tempTime =  datetime.datetime(int(currentTime.strftime("%Y")), int(currentTime.strftime("%m")), int(currentTime.strftime("%d")), int(row[n][0:2]),int(row[n][3:5]))
            if (tempTime > currentTime ):
                timing_status =1
                print ("true")
                #print (tempTime)
                break
                
    cursor.close()
    connection.close()
    if (timing_status == 1):
        return tempTime         
    elif (timing_status == 0):
        print ("try#2")      
        query = "SELECT * FROM 'main'.'prayer_times' WHERE Date = '" + getDate(1) +"';"
        connection = sqlite3.connect(database_file)
        cursor = connection.cursor()
        cursor.execute(query)
        timing_status =0
        tomorrowTime = currentTime
        tomorrowTime = tomorrowTime + datetime.timedelta(days = 1)
        for row in cursor:
            for n in range(2,7):
                tempTime =  datetime.datetime(int(tomorrowTime.strftime("%Y")), int(tomorrowTime.strftime("%m")), int(tomorrowTime.strftime("%d")), int(row[n][0:2]),int(row[n][3:5]))
                if (tempTime > currentTime ):
                    timing_status =1
                    print ("true")
                    #print (tempTime)
                    break
                
        cursor.close()
        connection.close()
        if (timing_status == 1):
            return tempTime  
        else:
            return 0    


def playMedia():
    p = vlc.MediaPlayer("Duck.mp3")
    p.play()
    

def refreshDatabaseTimings():
    input_dt = datetime.datetime.now()
    temp_month = input_dt.strftime("%m")
    temp_year = input_dt.strftime("%Y")
    print("The original date is:", input_dt.date())
    # add 31 days to the input datetime
    res = input_dt + relativedelta(day=31)
    print(f"Last date of month is:", res.date())
    print ((res-input_dt).days)
    if ((res-input_dt).days > 0):
        print("clear database")
        clearDatabase()
        print ("getting data for: m:" + temp_month + " y:" +temp_year)
        connectAPI(temp_month, temp_year)
    else:
        input_dt = input_dt + datetime.timedelta(days = 1)
        temp_month = input_dt.strftime("%m")
        temp_year = input_dt.strftime("%Y")
        print("clear database")
        clearDatabase() 
        print ("getting data for: m:" + temp_month + " y:" +temp_year)
        connectAPI(temp_month, temp_year)   


def mainLoop():
    print("Prayer Pod Loader")
    print ("Version: " + str(program_version))
    program_state=0
    while True:
        if (program_state == 0):
            output_trigger=1
            temp_time =getTiming()
            if (temp_time ==0):
                print("get timing error")
                refreshDatabaseTimings()
            else:
                print("next state")
                next_event = temp_time
                program_state=1
            

        elif (program_state == 1):
            currentTime =  datetime.datetime.now()
            if (currentTime>next_event):
                playMedia()
                program_state=0
            else:
                if (output_trigger== 1):
                    output_trigger=0
                    print("waiting for next event at: "+ str(next_event))
                    time.sleep(1) 
                    update_status (str(next_event))

def mainLoopLoader():
    try:
        mainLoop()
    except KeyboardInterrupt:
       sys.stdout.write(" HALT ")

if __name__ == '__main__':
    mainLoopLoader()