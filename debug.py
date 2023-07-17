
import logging

debugMode = False

def setDebug(debug):
    global debugMode
    debugMode = debug
    return

def debugEnabled():
    return debugMode

# helper function, comment out the "print" line to disable this function
def debugPrint(str):
    if(debugMode):
        logging.debug(str)
        print(str)
    return
