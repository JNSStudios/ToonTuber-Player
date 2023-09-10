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

(NOTE: As of right now, **the only way to create these JSON files is MANUALLY.** I do want to add some sort of graphical program for constructing these to make the user experience smoother, but for now this will have to do. I have provided a "Template Tuber" folder that users can refer to for the creation of their own.)

When the program begins, the program reads from a "preferences.ini" file to get select information preserved from previous sessions. This includes the last JSON file loaded, the last microphone used, and the talk volume and peak volume threshold values.

If the program is unable to load the last JSON file for any reason, the program will prompt the user to either create a new ToonTuber (**coming soon**) or load an existing one's JSON file.

When a tuber is loaded, all the images are imported and organized into Animation objects, which are then further organized into Canned Animation objects and Expression Sets. The exact structure of each type is described below, as well as how they are represented within the JSON file. You can use these JSON representations to build your own by copying and pasting it in, and by referencing the "Template Tuber"'s JSON file.

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
 - Press "right ctrl" key (or other assigned key) to toggle ignoring hotkeys (useful for when you want to type something without triggering animations)
 - Press "right shift" key (or other assigned key) to toggle muting the microphone (useful for when you want to mute your mic within the program)
 - If the program crashes, an error report is saved in the same folder. A loud error sound will also play so the user will know that the program crashed even if they cannot see it.
 - Animations can have sound effects attached to them. WAV, MP3, and OGG files are supported. (note: if you are streaming or recording while using this program, you will likely have to add an Application Audio Capture source in OBS to capture the sound effects, as they are played within the window.)
 - This program supports pressing keyboard hotkeys, and I want it to support StreamDecks in the future (I have some code ready for it, but I cannot test if it works as I do not own a StreamDeck. If one of you does and would like to contribute, fork this repository and program in StreamDeck functionality into this program.)


## What you will need:
   - for running the source Python code:
      - Python 3.10 or later (this program was written in Python 3.10.11)
      - an IDE to run the code (I use VSCode with Python extensions)
      - import the following libraries using "pip":
         - pygame (pip install pygame)
         - pygame-gui (pip install pygame_gui)
         - PyAudio (pip install pyaudio)
         - numpy (pip install numpy)
         - keyboard (pip install keyboard)
         - streamdeck (pip install streamdeck)
         - Pillow (pip install pillow)
         - notify-py (pip install notify-py)
      
   - if you are running this as a compiled EXE file, you should be all set!

## Project Files and Structure

- **assets/** - contains the images and sounds used in the program, as well as the image examples in this README.

- **Template Tuber/** - an example folder for how a ToonTuber should be structured. For more details, view the "Tuber Example README" inside this folder.

- **Jay ToonTuber/** - my own personal ToonTuber that I created for developing this program. Use it to play around with it and see how it works!

- **debug.py** - A Python class that contains debugging-related methods. If the Player is run in debug mode, it will print out debugging information to the console and to a log file.

- **file_reading.py** - A Python class that contains methods for reading and writing to files. Primarily used for the JSON files that ToonTubers use. 

- **LICENSE** - This project uses the GNU General Public License. See the LICENSE file for more details.

- **player.py** - Contains the visual display that the user sees.

- **README.md** - this file.

- **requirements.txt** - a list of all the Python libraries that this program uses. Use this to install all the libraries at once.

- **setup.py** - similar use as "requirements.txt," but this is used for compiling the program into an EXE file.

- **toontuber.py** - a Class file that contains all the methods and structures pertaining to the ToonTuber system.

- **toontuberEditor.py** - `NOT FINISHED YET,` but this would be the program that would allow users to create their own ToonTubers without having to manually edit the JSON files, using a GUI.


## A guide to making your own ToonTuber JSON
**(since the editor program doesn't exist yet)**

### Animation objects
- *frames*:                names of the images used as the frames of animations (can be a single PNG, a sequence of PNGs, or a GIF). These images **MUST be inside the "frames" folder inside the Tuber folder** in order for the program to be able to find them. 
![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/pngsequenceEx.png)
![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/gifEx.png)

- *frames per second*:     the framerate at which the images should be played. This applies to ALL file types. (Example: even if you're using a GIF, the framerate will still be determined from this value, as GIFs can have differing durations between frames.)

- *locking*:               if this is set to **true**, the animation **must** finish playing before a different animation can be played. This is ALWAYS set to True for Transition animations and Canned Animations, and are not necessary to add in the JSON when setting transition or canned animations.

    (**JSON**):
    ```
        "frames": [
            type the names of the image(s) here,
            use multiple by separating them with commas like this,
            ex: "Character-Basic-Main.gif"
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

- *hotkeys*:         The numbers representing the IDs of the key(s) you have to press in order to trigger this expression. Look in the **"Keybind Settings" screen** in the Player to view the Key IDs of the keys you press to figure out what to put for this data. Separate IDs with commas to have multiple keys trigger the same expression. If you do not want a hotkey for an expression set, you can type the word "null" (without the quotation marks).

- *requires*:        A list of Expression Set names. You can have multiple of them, but *only one of them needs to currently be playing in order for this one to play next*. (IE: If I have three Expressions called "Happy," "Laughing," and "Wheezing," I can tell the "Wheezing" animation to require the "Happy" or "Laughing" animations here. If either of those animations are playing when the "Wheezing" animation is requested, it will play "Wheezing" next. Otherwise, it won't trigger the animation.) If you do not want an animation to require anything, type the word "null" (without the quotation marks).

- *blockers*:        A list of Expression Set names. This functions similar to the "requires" list, but it will prevent this Expression from playing if the Expression that is currently playing is within this list. (IE: If you have a "Happy," and "Sad" Expression, you can prevent the "Sad" Expression from triggering when "Happy" is playing.) Typing the word "null" (without the quotation marks) will mean no Expressions will block this one.

- *instant*:         If this value is true, the player will immediately jump to this expression instead of playing the "Transition Out" animation of the previous animation. If it's false, the transitions will play.

- *sound*:           The name of a sound file (either .wav or .mp3). This sound will play when the expression begins (either during the transition in, or when the main animation first appears if either no transition exists or the "instant" value is true.) Type the word "null" (without quotation marks) if you do not want a sound to play. The sound file **MUST be inside of the "sounds" folder inside of the Tuber folder** in order for the program to be able to find it.

- *animations*:      A **specific list of 6 Animation objects**:
    
    -- the "Main" Animation.            Plays when your character is doing nothing. (**REQUIRED**)
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/mainEx.png)
    
    -- the "Idles" IdleSet.             Contains the set of Idle animations to randomly be played when your character is doing nothing. Can be NULL.
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/idleEx1.gif)![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/idleEx2.gif)
    
    -- the "Talk" Animation.            Plays when your character is speaking. Can be NULL.
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/talkEx.gif)
    
    -- the "Peak" Animation.            Plays when your character is yelling. Can be NULL.
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/peakEx.gif)
    
    -- the "TransitionIN" Animation     Plays when your character is ENTERING this Expression. Can be NULL.
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/trInEx.gif)
    
    -- the "TransitionOut" Animation    Plays when your character is LEAVING this Expression. Can be NULL.
    
    ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/trOutEx.gif)


    (**JSON**):
    ```
        "name": type the name of the animation surrounded by quotation marks,
        "hotkeys": [
            for each hotkey desired, type the numbers shown by the "Keybind Settings" screen in the player. If you want to have multiple hotkeys, separate the IDs with commas. If you don't want a hotkey, type null.
        ],
        "requires": [
            list all the names of the Expression Sets that ALLOW this one to play (or null)
        ],
        "blockers": [
            list all the names of the Expression sets that PREVENT this one from playing (or null)
        ],
        "instant": true or false (if true, the animation will play instantly, without a transition animation)
        "sound": either type the name of the sound file, or type null if you don't want a sound to play,
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
                Animation JSON Object (or null)
            }, 
            "TransitionOUT": 
            {
                Animation JSON Object (or null)
            } 
        }
    ```

### Canned Animation objects
- *name*:            The name of the Canned Animation

- *hotkeys*:          Same as the Expression Set "hotkeys" list. List as many key IDs as you want in quotation marks, separated by commas, or type "null" (without the quotation marks) if you don't want a hotkey.

- *requires*:        Same as the Expression Set "requires" list. List as many as you want, or type "null."

- *blockers*:        Same as the Expression Set "blockers" list. List as many as you want, or type "null."

- *result*:            The name of the Expression Set or Canned Animation that will be played after this Canned Animation is finished. **THIS IS HIGHLY RECOMMENDED.** If you type the word "null" to not assign a resulting animation, the Canned Animation will loop until a hotkey is pressed to trigger a new animation.

- *instant*:         If this value is true, the current animation's transition will be skipped and the canned animation will begin immediately. If it's false, the current animation will transition out before playing the canned animation.

- *sound*:            The name of a sound file that will play once the animation is triggered. Can be null if you don't want one. Again, the sound file **MUST be inside of the "sounds" folder inside of the Tuber folder.**

- *animation*:        The Animation object that will be played when this Canned Animation is triggered.

(Below are two examples of Canned animations, one of the character appearing and waving, and another of the character leaving)

![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/cannedEx1.gif) ![](https://github.com/JNSStudios/ToonTuber-Player/blob/main/assets/cannedEx2.gif)

    (**JSON**)
    ```
      "name": type the name of the animation surrounded by quotation marks,
      "hotkeys": [
        for each hotkey desired, type the numbers shown by the "Keybind Settings" screen in the player. If you want to have multiple hotkeys, separate the IDs with commas. If you don't want a hotkey, type null.
      ], 
      "requires": [
        list all the names of the Expression Sets that ALLOW this one to play (or null)
      ],
      "blockers": [
        list all the names of the Expression sets that PREVENT this one from playing (or null)
      ],
      "result": type the name of the resulting Expression Set surrounded by quotation marks,
      "instant: true or false (if true, the animation will play instantly, without a transition animation),
      "sound": type the name of the sound file surrounded by quotation marks (or null) (similar to adding a frame of Animation),
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

- *player_version*:                The version of the ToonTuber Player that this ToonTuber was created for.

- *random_duplicate_reduction*:    A number between 0 and 1. This is the percentage of the time that the player will attempt to reduce the chance of playing the same idle animation multiple times in a row. (IE: If this number is 0, the player will NOT try to prevent the same idle from playing twice in a row. If this number is 1, the player will ALWAYS try to prevent the same idle from playing twice in a row. This does not affect Expressions with one or no idles.)

- *expressions*:                   A list of Expression Set objects. **Remember that transition animations in expressions do NOT need a "locking" parameter, as the program will AUTOMATICALLY lock all transition animations.**

- *canned_anims*:                  A list of Canned Animation objects. **NOTE: It is not necessary to list a "locking" parameter for Animations put inside of Canned Animations, as the program will AUTOMATICALLY lock ALL Canned Animations.**

    (**JSON**)
    ```
    {
        "name": "type the name of your ToonTuber here",
        "creator": "type your username and/or real name here",
        "created": "don't worry about this, it'll be overwritten by the editor program",
        "last_modified": "same with this one",
        "player_version": "IMPORTANT: type the version of ToonTuber Player that this Tuber is intended for",
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
### ToonTuber Folder Structure

A Tuber folder follows this structure:
```
Tuber
├── frames                  # Folder for all Animation frames 
│   └── ...                     # pngs and gifs
├── sounds                  # Folder for all Sounds
│   └── ...                     # mp3, wav, or oggs
└── tuber.json              # The JSON file (doesn't have to be this exact name)
```
You have to have two folders, "frames" and "sounds," for storing the animation frames and sounds. The program will look in these EXACT folder names when loading the animation frames and sounds (case sensitive). The JSON file can be named anything you want, but it must be a JSON file. The user selects the JSON file to load, and the program will then use the folder that the selected JSON file is inside to find the "frames" and "sounds" folders.

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

- If the current animation is an **EXPRESSION**, it will load the "Transition Out" animation from that expression set, if it exists and the next animation doesn't utilize an instant transition, and wait until that is finished. If there is no Out transition or the next expression requires instant transition, the player will immediately load the next animation.

- If the current animation is a **CANNED ANIMATION**, it will wait until that animation is finished.

Then:

- If the queued animation is an **EXPRESSION**, the player will load and play the "Transition In" animation from the queued expression set (if it exists, *even if the Expression has an "Instant Transition" attribute to it*). If there is no In transition, or if the previous animation was a Canned animation, the player will immediately load the Main animation from the queued expression set. 

- If the queued animation is a **CANNED ANIMATION**, the player will load the Canned Animation and start playing it immediately. When the animation is finished, the player will then load the Expression Set or Canned Animation designated as the "result" of completed Canned Animation. If no result is designated, the player will loop the Canned Animation until a new animation is queued.

If you press another hotkey while the player is transitioning into another animation, the player will **attempt to queue** any viable animation to play once the transition is complete. For example, if you have "Happy" and "Laughing" Expressions set to the same hotkey, with the "Laughing" animation requiring the "Happy" animation, and you press that hotkey twice in a row, the player will transition out of the current animation, skip "Happy," and transition straight into "Laughing."
    
If an Expression or Canned Animation has a **sound** attached to it, the sound will immediately begin playing after the animation is loaded. It will play until it is finished. For Canned Animations, the sound will begin playing with the start of the Canned Animation. For Expressions, the sound will trigger when the animation is transitioned into (this works even if the animation has an "Instant Transition" attribute.)

I recommend using a sound editor to exactly time the sound effect with your animation. (I use Audacity.)

## Special Thanks and Collaborators

- Thanks to **Piximator** for helping with macOS and crossplatform compatibility testing!