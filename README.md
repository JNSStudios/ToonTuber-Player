## ToonTuber-Player
A standalone program designed to recreate, consolidate, and optimize the ToonTuber system created by ScottFalco. (Original tutorial here: https://www.youtube.com/watch?v=i-yW-3dI1oE)

![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/PlayerScreenshot.png)


# How it works
ToonTubers are created by organizing a set of animations (either *PNG(s)* or *GIFs*) and referencing them in *JSON* data files. 

(NOTE: As of right now, **the only way to create these JSON files is MANUALLY.** I do want to add some sort of graphical program for constructing these to make the user experience smoother, but for now this will have to do. I have provided a "referenceTuber.json" users can refer to for the creation of their own.)

When the program begins, the program reads from a "preferences.ini" file to get select information preserved from previous sessions. This includes the last JSON file loaded, the last microphone used, and the talk volume and peak volume threshold values.

If the program is unable to load the last JSON file for any reason, the program will prompt the user to either create a new ToonTuber (**coming soon**) or load an existing one's JSON file.

When a tuber is loaded, all the images are imported and organized into Animation objects, which are then further organized into Canned Animation objects and Expression Sets. The exact structure of each type is described below, as well as how they are represented within the JSON file. You can use these JSON representations to build your own by copying and pasting it in, and by referencing the "referenceTuber.json" file

# Animation objects 
- *frames*:                path(s) to a single PNG, a sequence of PNGs, or a GIF.
![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/pngsequenceEx.png)
![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/gifEx.png)

- *frames per second*:     the framerate at which the images should be played. If you're using a GIF, the framerate will be taken from that, but it is still recommended to enter the framerate manually just to be safe

- *locking*:               if this is set to **true**, the animation **must** finish playing before a different animation can be played. This is recommended for Transition animations, but can be enabled for any.

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

# Idle Set objects
- *animations*:            A list of *Animation* objects, described above

- *min random seconds*:    represents the minimum number of seconds needed before an Idle animation is selected

- *max random seconds*:    represents the maximum seconds allowed before an Idle is selected

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

# Expression Set objects
- *name*:            The name of the Expression

- *hotkeys*:         The text representing the key(s) you have to press in order to trigger this expression. Use the "hotkey names" program that displays the name of the keys you press to figure out what to put for this data. If you have multiple, separate them with commas. If you do not want a hotkey for an expression set (for example, if you want a "Hidden" Expression that makes your character invisible, and you only want accessible after a canned "Disappear" animation), you can type the word "null" (without the quotation marks).

- *requires*:        A list of Expression Set names. You can have multiple of them, but *only one of them needs to currently be playing in order for this one to play next*. (IE: If I have three Expressions called "Happy," "Laughing," and "Wheezing," I can tell the "Wheezing" animation to require the "Happy" or "Laughing" animations here. If either of those animations are playing when the "Wheezing" animation is requested, it will play "Wheezing" next. Otherwise, it won't trigger the animation.) If you do not want an animation to require anything, type the word "null" (without the quotation marks).

- *blockers*:        A list of Expression Set names. This functions similar to the "requires" list, but it will prevent this Expression from playing if the Expression that is currently playing is within this list. (IE: If you have a "Happy," and "Sad" Expression, you can prevent the "Sad" Expression from triggering when "Happy" is playing.) Typing the word "null" (without the quotation marks) will mean no Expressions will block this one.

- *animations*:        A specific list of 6 Animation objects:
    
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
    ```
    {
        "name": type the name of the animation surrounded by quotation marks,
        "hotkeys": [
            for each hotkey desired, type the text shown by the "hotkey names" program, surrounded by quotation marks. Separate them with commas. If you don't want a hotkey, type null.
        ],
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
    }
    ```

# Canned Animation objects
- *name*:            The name of the Canned Animation

- *hotkeys*          Same as the Expression Set "hotkeys" list. List as many as you want in quotation marks, separated by commas, or type "null" (without the quotation marks) if you don't want a hotkey.

- *requires*        Same as the Expression Set "requires" list. List as many as you want, or type "null."

- *blockers*        Same as the Expression Set "blockers" list. List as many as you want, or type "null."

- *result*            The name of the Expression Set or Canned Animation that will be played after this Canned Animation is finished. **THIS IS REQUIRED.** If you do not list a result, the Canned Animation will get stuck in an infinite loop.

- *animation*        The Animation object that will be played when this Canned Animation is triggered.

    (**JSON**)
    ```
    {
      "name": type the name of the animation surrounded by quotation marks,
      "hotkeys": [
        for each hotkey desired, type the text shown by the "hotkey names" program, surrounded by quotation marks. Separate them with commas. If you don't want a hotkey, type null.
      ], 
      "requires": [
        list all the names of the Expression Sets that ALLOW this one to play (or null)
      ],
      "blockers": [
        list all the names of the Expression sets that PREVENT this one from playing (or null)
      ],
      "result": type the name of the resulting Expression Set surrounded by quotation marks,
      "anim": 
      {
        Animation JSON Object
      }
    }
    ```

# Full ToonTuber JSON data structure
- *name*:                          The name of the ToonTuber

- *creator*:                       The name of the person who created the ToonTuber

- *created*:                       The date the ToonTuber was created (this will be added automatically by the editor program)

- *last_modified*:                 The date the ToonTuber was last modified (this will be added automatically by the editor program)

- *random_duplicate_reduction*:    A number between 0 and 1. This is the percentage of the time that the player will attempt to reduce the chance of playing the same animation twice in a row. (IE: If this number is 0, the player will NOT try to prevent the same animation from playing twice in a row. If this number is 1, the player will ALWAYS try to prevent the same animation from playing twice in a row.)

- *expressions*:                   A list of Expression Set objects

- *canned_anims*:                  A list of Canned Animation objects

(**JSON**)
{
  "name": "type the name of your ToonTuber here",
  "creator": "type your username and/or real name here",
  "created": "don't worry about this, it'll be overwritten by the editor program",
  "last_modified": "same with this one",
  "random_duplicate_reduction": 0 to 1,
  "expressions": [
    List of ExpressionSet Objects
  ],
  "canned_anims": [
    List of Canned Animation Objects
  ]
}
