# ToonTuber-Player
A standalone program designed to recreate, consolidate, and optimize the ToonTuber system created by ScottFalco. 

[Find the latest release here](https://github.com/JNSStudios/ToonTuber-Player/releases)

![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/PlayerScreenshot.png)

# What is a ToonTuber?
ToonTubers were originally created by YouTuber ScottFalco as "a middle-ground between PNGTubers and VTubers, for when PNGTubers are too limited and, maybe you just don't like the smoothness of a VTuber." 

ToonTubers consist of a set of animation frames that play back to create expressions and movement. These animations can be triggered with a hotkey or button, and react to you speaking and/or yelling. It's like having a hand-animated character as your avatar!

ScottFalco released [his original tutorial](https://www.youtube.com/watch?v=i-yW-3dI1oE) for creating a ToonTuber on Feburary 4th, 2023, and his original setup required multiple programs (one of which became paywalled) and possibly needed you to mess with a bunch of files for OBS in order for the encoder to work correctly. As this system wasn't perfect (ScottFalco said so himself, he called this system a "public beta"), I decided to create my own ToonTuber player (inspired by [veadotube mini](https://olmewe.itch.io/veadotube-mini)) using Python. 

With ToonTuber Player, all you need is the one program which you can then do a Window Capture of in OBS!

This program is FREE and OPEN-SOURCE, so anyone can use it and change it as their heart desires. The goal is to make it so the user doesn't need to mess with as much technical stuff, and all they have to provide is their animations. 

## How it works
ToonTubers are created by organizing a set of animations (either *PNG(s)* or *GIFs*) and referencing them in *JSON* data files. 

(NOTE: As of right now, **the only way to create these JSON files is MANUALLY.** I do want to add some sort of graphical program for constructing these to make the user experience smoother, but for now this will have to do. I have provided a "referenceTuber.json" users can refer to for the creation of their own.)

When the program begins, the program reads from a "preferences.ini" file to get select information preserved from previous sessions. This includes the last JSON file loaded, the last microphone used, and the talk volume and peak volume threshold values.

If the program is unable to load the last JSON file for any reason, the program will prompt the user to either create a new ToonTuber (**coming soon**) or load an existing one's JSON file.

When a tuber is loaded, all the images are imported and organized into Animation objects, which are then further organized into Canned Animation objects and Expression Sets. The exact structure of each type is described below, as well as how they are represented within the JSON file. You can use these JSON representations to build your own by copying and pasting it in, and by referencing the "referenceTuber.json" file

## Program features
 - Press "p" key (or other assigned key) to open the Settings screen
     - "Load Tuber" button to load in new JSON data
     - Change background color
     - Toggle pixel smoothing (antialiasing)
     - Change the keys used to open the Settings screen, toggle hotkey ignoring, and toggle mic muting
     - A dropdown menu to change audio input device used for the program
     - A slider to change the animation sound effect volume
 - Press hotkeys assigned by the Tuber JSON to play the related animation (even if the window is out of focus!)
   (**NOTE:** While the Player window will continue to run when minimized, OBS cannot capture it while it's minimized. This is unfortunately an issue that I have no control over.)
 - If the program crashes, an error report is saved in the same folder. A loud error sound will also play so the user will know that the program crashed even if they cannot see it.
 - This program supports pressing keyboard hotkeys, and I want it to support StreamDecks in the future (I have some code ready for it, but I cannot test if it works as I do not own a StreamDeck. If one of you does and would like to contribute, fork this repository and program in StreamDeck functionality into this program.)
 - Canned Animations can have sound effects attached to them. WAV, MP3, and OGG files are supported.

## What you will need:
   - for running as Python code:
      - Python 3.10
      - an IDE to run the code (I use VSCode with Python extensions)
      - import the following libraries using "pip":
         - pygame (pip install pygame)
         - pygame-gui (pip install pygame_gui)
         - PyAudio (pip install pyaudio)
         - numpy (pip install numpy)
         - keyboard (pip install keyboard)
         - streamdeck (pip install streamdeck)
         - imageio (pip install imageio)
      
   - if you are running this as a compiled EXE file, you should be all set!

## A guide to making your own ToonTuber JSON
**(since the editor program doesn't exist yet)**

### Animation objects
- *frames*:                path(s) to a single PNG, a sequence of PNGs, or a GIF.
![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/pngsequenceEx.png)
![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/gifEx.png)

- *frames per second*:     the framerate at which the images should be played. If you're using a GIF, the framerate will be taken from that, but it is still recommended to enter the framerate manually just to be safe

- *locking*:               if this is set to **true**, the animation **must** finish playing before a different animation can be played. This is ALWAYS set to True for Transition animations and Canned Animations, and are not necessary to add in the JSON when setting transition or canned animations.

    (**JSON**):
    ```
        "frames": [
            "relative path to PNG/GIF used (use commas to separate PNG file names.)",
            "(a relative path is the path from the "toontuber.py" file to the image.)",
            "(usually, these should be inside of the ToonTuber's folder. If it is, use the below template:)",
            "ToonTubers\\(name of the ToonTuber folder)\\(name of folder that contains your frames)\\(file name)",
        ],
        "fps": number,
        "locking": true or false (no need to type this in if it's a canned animation or transition animation)
    ```

### Idle Set objects
- *animations*:            A list of *Animation* objects, described above

- *min random seconds*:    represents the minimum number of seconds needed before an Idle animation is selected

- *max random seconds*:    represents the maximum seconds allowed before an Idle is selected

    (**JSON**):
    ```
        "randomSecMin": number,
        "randomSecMax": bigger number,
        "idleAnims": [
            {
                Animation JSON Object
            },
            {
                another Animation JSON Object(s)
            },
            {
                etc.
            }
        ]
    ```

### Expression Set objects
- *name*:            The name of the Expression

- *hotkeys*:         The numbers representing the IDs of the key(s) you have to press in order to trigger this expression. Use the "**hotkey IDs**" program that displays the ID of the keys you press to figure out what to put for this data. Separate numbers with commas. If you do not want a hotkey for an expression set, you can type the word "null" (without the quotation marks).

- *requires*:        A list of Expression Set names. You can have multiple of them, but *only one of them needs to currently be playing in order for this one to play next*. (IE: If I have three Expressions called "Happy," "Laughing," and "Wheezing," I can tell the "Wheezing" animation to require the "Happy" or "Laughing" animations here. If either of those animations are playing when the "Wheezing" animation is requested, it will play "Wheezing" next. Otherwise, it won't trigger the animation.) If you do not want an animation to require anything, type the word "null" (without the quotation marks).

- *blockers*:        A list of Expression Set names. This functions similar to the "requires" list, but it will prevent this Expression from playing if the Expression that is currently playing is within this list. (IE: If you have a "Happy," and "Sad" Expression, you can prevent the "Sad" Expression from triggering when "Happy" is playing.) Typing the word "null" (without the quotation marks) will mean no Expressions will block this one.

- *animations*:        A **specific list of 6 Animation objects**:
    
    -- the "Main" Animation.            Plays when your character is doing nothing. (**REQUIRED**)
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/mainEx.png)
    
    -- the "Idles" IdleSet.             Contains the set of Idle animations to randomly be played when your character is doing nothing. Can be NULL.
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/idleEx1.gif)![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/idleEx2.gif)
    
    -- the "Talk" Animation.            Plays when your character is speaking. Can be NULL.
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/talkEx.gif)
    
    -- the "Peak" Animation.            Plays when your character is yelling. Can be NULL.
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/peakEx.gif)
    
    -- the "TransitionIN" Animation     Plays when your character is ENTERING this Expression (**REQUIRED**)
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/trInEx.gif)
    
    -- the "TransitionOut" Animation    Plays when your character is LEAVING this Expression (**REQUIRED**)
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/trOutEx.gif)

    (Please note that **just because some animations are required, that doesn't mean they can't be "removed."** For example, I have a "HIDDEN" Expression Set that is supposed to be used when my character is offscreen, and all I did for the Main, Transition In, and Transition Out animations was a single blank frame. In essence, I made it so there was no visual animation occurring, and it could be overwritten at a moments notice because it was only one frame.)

    (**JSON**):
    ```
        "name": type the name of the animation surrounded by quotation marks,
        "hotkeys": [
            for each hotkey desired, type the numbers shown by the "hotkey IDs" program, surrounded by quotation marks. Separate them with commas. If you don't want a hotkey, type null.
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
    ```

### Canned Animation objects
- *name*:            The name of the Canned Animation

- *hotkeys*:          Same as the Expression Set "hotkeys" list. List as many key IDs as you want in quotation marks, separated by commas, or type "null" (without the quotation marks) if you don't want a hotkey.

- *requires*:        Same as the Expression Set "requires" list. List as many as you want, or type "null."

- *blockers*:        Same as the Expression Set "blockers" list. List as many as you want, or type "null."

- *result*:            The name of the Expression Set or Canned Animation that will be played after this Canned Animation is finished. **THIS IS REQUIRED.** If you do not list a result, the Canned Animation will get stuck in an infinite loop.

- *sound*:            A path to a sound file that will play once the animation is triggered. Can be null if you don't want one.

- *animation*:        The Animation object that will be played when this Canned Animation is triggered.

(Below are two examples of Canned animations, one of the character appearing and waving, and another of the character leaving)

![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/cannedEx1.gif) ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/cannedEx2.gif)

    (**JSON**)
    ```
      "name": type the name of the animation surrounded by quotation marks,
      "hotkeys": [
        for each hotkey desired, type the numbers shown by the "hotkey IDs" program, surrounded by quotation marks. Separate them with commas. If you don't want a hotkey, type null.
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
        A SINGLE Animation JSON Object ("locking" parameter not necessary for Canned)
      }
    ```

### Full ToonTuber JSON data structure
- *name*:                          The name of the ToonTuber

- *creator*:                       The name of the person who created the ToonTuber

- *created*:                       The date the ToonTuber was created (this will be added automatically by the editor program)

- *last_modified*:                 The date the ToonTuber was last modified (this will be added automatically by the editor program)

- *random_duplicate_reduction*:    A number between 0 and 1. This is the percentage of the time that the player will attempt to reduce the chance of playing the same animation twice in a row. (IE: If this number is 0, the player will NOT try to prevent the same animation from playing twice in a row. If this number is 1, the player will ALWAYS try to prevent the same animation from playing twice in a row.)

- *expressions*:                   A list of Expression Set objects. **Remember that transition animations in expressions do NOT need a "locking" parameter, as the program will AUTOMATICALLY lock all transition animations.**

- *canned_anims*:                  A list of Canned Animation objects. **NOTE: It is not necessary to list a "locking" parameter for Animations put inside of Canned Animations, as the program will AUTOMATICALLY lock ALL Canned Animations.**

    (**JSON**)
    ```
    {
        "name": "type the name of your ToonTuber here",
        "creator": "type your username and/or real name here",
        "created": "don't worry about this, it'll be overwritten by the editor program",
        "last_modified": "same with this one",
        "random_duplicate_reduction": 0 to 1,
        "expressions": [
            {
                Expression Set JSON Object
            }, 
            {
                Another Expression Set JSON Object
            }, 
            {
                etc.
            }
        ],
        "canned_anims": [
            {
                Canned Animation JSON Object
            }, 
            {
                Another Canned Animation JSON Object
            }, 
            {
                etc.
            }
        ]
    }
    ```

## How ToonTubers are Controlled/Played Back
When loading a ToonTuber JSON, the "Main" animation of the **first** Expression listed in the file is what the player will play first. 

For **Main** animations, the player will simply loop them until the player is told to do something else.

For **Idle** animations, the player will pick a random number between the two numbers provided in the Expression's IdleSet object, and will start a timer when the **Main** animation is played. The player will then wait that many seconds before randomly selecting an Idle animation from that Set. If any action happens to override the Main animation, this timer will be reset (but the number of seconds will not change).

For **Talk** animations, the player will check the detected volume from the microphone input and check if it's over the "*Talk Threshold*." If it is, it will interrupt the current animation (if it isn't locked) and play the Talk animation until the volume drops below the threshold, in which case it will load the Main animation.

For **Peak** animations, the player does the same thing as Talk, but compares the volume against the "*Peak Threshold*." If the volume is over the Peak Threshold, it will play the Peak animation until the volume drops below the threshold, in which case it will load the Main animation.

**When a Hotkey is pressed,** the player will get a list of all Expressions and/or Canned Animations that are triggered by that hotkey. It will then filter the list down to any animations that meet ALL of the following criteria:
    - NOT blocked by the current animation
    - the current animation is in the "requires" list of the animation
    - is NOT the current animation (to prevent duplicates)
Before selecting the next animation, the player will then **give selection weights to the animations** in the filtered list that have the current animation listed as a requirement. This is to ensure that **animations with a met requirement will be more likely to be selected**. 
The player will then randomly select one of the animations from the filtered list (using the selection weights), and **queue** that animation. (Or it will do nothing if the list is empty.)

When **a new animation is queued**, the player will check if the current animation is locked. If it is, it will wait until the current animation is unlocked before playing the queued animation. (**NOTE: ALL Canned animations are automatically LOCKED.**)

When the player is ready to play the queued animation, it will do one of two things:
    - If the current animation is an **EXPRESSION**, it will load the "Transition Out" animation from that expression set and wait until that is finished. 
    If the current animation is a **CANNED ANIMATION**, it will wait until that animation is finished.
    Then:
        - If the queued animation is an **EXPRESSION**, the player will load the "Transition In" animation from the queued expression set, and then load the "Main" animation from the queued expression set when the "Transition In" animation is finished.
        - If the queued animation is a **CANNED ANIMATION**, the player will load the Canned Animation and start playing it immediately. When the animation is finished, the player will then load the Expression Set or Canned Animation designated as the "result" of completed Canned Animation.

If you press another hotkey while the player is transitioning into another animation, the player will **attempt to queue** any viable animation to play once the transition is complete. For example, if you have "Happy" and "Laughing" Expressions set to the same hotkey, with the "Laughing" animation requiring the "Happy" animation, and you press that hotkey twice in a row, the player will transition out of the current animation, skip "Happy," and transition straight into "Laughing."
    
If a Canned Animation has a **sound** attached to it, the sound will immediately begin playing after the Canned Animation is loaded. It will play until it is finished. I recommend using a sound editor to exactly time with your animation. (I use Audacity.)
