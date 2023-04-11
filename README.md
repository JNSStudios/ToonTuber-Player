## ToonTuber-Player
A standalone program designed to recreate, consolidate, and optimize the ToonTuber system created by ScottFalco. (Original tutorial here: https://www.youtube.com/watch?v=i-yW-3dI1oE)

![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/PlayerScreenshot.png)


# How it works
ToonTubers are created by organizing a set of animations (either *PNG(s)* or *GIFs*) and referencing them in *JSON* data files. 

(NOTE: As of right now, **the only way to create these JSON files is MANUALLY.** I do want to add some sort of graphical program for constructing these to make the user experience smoother, but for now this will have to do. I have provided a "referenceTuber.json" users can refer to for the creation of their own.)

When the program begins, the program reads from a "preferences.ini" file to get select information preserved from previous sessions. This includes the last JSON file loaded, the last microphone used, and the talk volume and peak volume threshold values.

If the program is unable to load the last JSON file for any reason, the program will prompt the user to either create a new ToonTuber (**coming soon**) or load an existing one's JSON file.

When a tuber is loaded, all the images are imported and organized into Animation objects, which are then further organized into Canned Animation objects and Expression Sets. The exact structure of each type is described below, as well as how they are represented within the JSON file. You can use these JSON representations to build your own by copying and pasting it in, and by referencing the "referenceTuber.json" file

# Animation objects: (object for all animation types) 
- *frames*                (path(s) to PNG(s) or a GIF. You can have a single PNG, a sequence of PNGs, or a GIF.)
![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/pngsequenceEx.png)
![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/gifEx.png)

- *frames per second*     (the framerate at which the images should be played. If you're using a GIF, the framerate will be taken from that, but it is still recommended to enter the framerate manually just to be safe)

- *locking*               (if this is set to **true**, the animation **must** finish playing before a different animation can be played. This is recommended for Transition animations, but can be enabled for any.)

    (**JSON**):
    ```
    {
        "frames": [
        "relative path to PNG/GIF used (use commas to separate PNG file names.)"
        ],
        "fps": number,
        "locking": true or false
    }
    ```

# Idle Set objects: (object to contain a set of Animations designated as "Idle" animations)
- *animations*            (A list of *Animation* objects, described above)

- *min random seconds*    (represents the minimum number of seconds needed before an Idle animation is selected)

- *max random seconds*    (represents the maximum seconds allowed before an Idle is selected)

    (**JSON**):
    ```
    {
        "randomSecMin": number,
        "randomSecMax": bigger number,
        "idleAnims": [
            {
                Animation JSON Object
            },
            {
                another Animation JSON Object(s)
            }
        ]
    }
    ```

# Expression Set objects:
- *name*            The name of the Expression

- *hotkey*          The text representing the key you have to press in order to trigger this expression. Use the "hotkey names" program that displays the name of the keys you press to figure out what to put for this data.

- *requires*        A list of Expression Set names. You can have multiple of them, but *only one of them needs to currently be playing in order for this one to play next*. (IE: If I have three Expressions called "Happy," "Laughing," and "Wheezing," I can tell the "Wheezing" animation to require the "Happy" or "Laughing" animations here. If either of those animations are playing when the "Wheezing" animation is requested, it will play "Wheezing" next. Otherwise, it won't trigger the animation.) If you do not want an animation to require anything, type the word "null" (without the quotation marks).

- *blockers*        A list of Expression Set names. This functions similar to the "requires" list, but it will prevent this Expression from playing if the Expression that is currently playing is within this list. (IE: If you have a "Happy," and "Sad" Expression, you can prevent the "Sad" Expression from triggering when "Happy" is playing.) Typing the word "null" (without the quotation marks) will mean no Expressions will block this one.

- *animations*        A specific list of 6 Animation objects:
    
    -- the "Main" Animation.            Plays when your character is doing nothing. (**REQUIRED**)
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/mainEx.png)
    
    -- the "Idles" IdleSet.             Contains the set of Idle animations to randomly be played when your character is doing nothing. (Can be NULL)
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/idleEx.gif)
    
    -- the "Talk" Animation.            Plays when your character is speaking
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/talkEx.gif)
    
    -- the "Peak" Animation.            Plays when your character is yelling
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/peakEx.gif)
    
    -- the "TransitionIN" Animation     Plays when your character is ENTERING this Expression (**REQUIRED**)
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/trInEx.gif)
    
    -- the "TransitionOut" Animation    Plays when your character is LEAVING this Expression (**REQUIRED**)
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/trOutEx.gif)


    (**JSON**):
    ```{
        "name": type the name of the animation surrounded by quotation marks,
        "hotkey": type the text shown by the "hotkey names" program, surrounded by quotation marks,
        "requires": [
        list all the names of the Expression Sets that ALLOW this one to play
        ],
        "blockers": [
        list all the names of the Expression sets that PREVENT this one from playing
        ],
        "anims": {
        "Main": {
            Animation JSON Object (**REQUIRED**)
        },
        "Idles": {
            IdleSet JSON Object (or null)
        },
        "Talk": 
        {
            Animation JSON Object (or null)
        },
        "Peak":
        {
            Animation JSON Object (or null)
        },
        "TransitionIN":
        {
            Animation JSON Object (**REQUIRED**)
        }, 
        "TransitionOUT": 
        {
            Animation JSON Object (**REQUIRED**)
        } 
        }
    }```

