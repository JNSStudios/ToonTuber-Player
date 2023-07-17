import debug

import tkinter as tk
from tkinter import filedialog
import os


jsonPath = ""
currentlyLoadingFile = "Reading "

def setJSONPath(path):
    # check if there's a json file there
    if(os.path.isfile(path)):
        global jsonPath
        
        jsonPath = path
        # if windows OS, replace forward slashes with backslashes
        if(os.name == "nt"):
            jsonPath = jsonPath.replace("/", "\\")
        # remove file name from path
        jsonPath = os.path.dirname(jsonPath)
        return True
    else:
        debug.debugPrint("No JSON file found at " + path)
        return False


def selectJSON():
    global jsonPath
    debug.debugPrint("Prompting for new JSON file...")
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        filetypes=[("JSON files", "*.json")],
        title="Select a JSON file",
    )

    root.destroy()  # close the root window

    if(file_path is None or file_path == ""):
        print("No file selected.")
        return

    (jsonPath, filename) = os.path.split(file_path)
    # if windows OS, replace forward slashes with backslashes
    if(os.name == "nt"):
        jsonPath = jsonPath.replace("/", "\\")
    debug.debugPrint("Selected JSON path: " + jsonPath + "\\" + filename)
    return file_path

def getJSONPath():
    return jsonPath