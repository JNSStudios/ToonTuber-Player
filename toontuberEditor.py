import tkinter as tk
from tkinter import filedialog

class Animation:
    # array of filenames for frames
    # frames per second

    def __init__(self, frames, fps):
        self.frames = frames
        self.fps = fps
    
    
    def add_frames(self, frames):
        self.frames.extend(frames)

    def add_frame(self, frame):
        self.frames.append(frame)
    
    def remove_frame(self, frame):
        self.frames.remove(frame)

    def get_frame_names(self):
        return [frame.name for frame in self.frames]
    
    def set_fps(self, fps):
        self.fps = fps
    
    def get_fps(self):
        return self.fps
    

class Node:
    # generic node class
    # name
    # requires nodes
    # enables nodes

    def __init__(self, name, images, requires, enables):
        self.name = name
        self.images = images
        self.receives_from = requires
        self.sends_to = enables
    
    def add_required_node(self, node):
        self.receives_from.append(node)

    def remove_required_node(self, node):
        self.receives_from.remove(node)

    def add_enabled_node(self, node):
        self.sends_to.append(node)

    def remove_enabled_node(self, node):
        self.sends_to.remove(node)



class UniversalTransitionNode(Node):
    # universal transition node
    # name
    # single image

    def __init__(self, name):
        super().__init__(name)
    
    def set_image(self):
        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.askopenfilename(title='Select the universal transition frame')
        self.images = filepath
    

class StandardAnimationNode(Node):
    # standard animation node
    # name
    # single freeze frame idle (optional)
    # 4 sets of Animation objects
    # hotkey for activation

    def __init__(self, name, freeze, animations, hotkey):
        super().__init__(name)
        self.freeze = freeze
        self.animations = animations
        self.hotkey = hotkey

    def set_freeze_frame(self):
        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.askopenfilename(title='Select a freeze-frame image')
        self.freeze = filepath

    def add_animation(self, animation):
        self.animations.append(animation)

    def remove_animation(self, animation):
        self.animations.remove(animation)

    def set_hotkey(self, hotkey):
        self.hotkey = hotkey

    def get_hotkey(self):
        return self.hotkey
    
