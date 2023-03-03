# Intro

jstest is a package for debian that allows you test all the features of the Linux joystick API (See Man jstest)
As a second focus the project aims to serve as an example for those wishing to implement joystick applications.

This project will read from jstest the inputs fired from a joystick. It uses jstest as an API
ontop of the joystick API to process joystick events.

# Project Statement

This project aims to be a low level program to bind button presses to keystrokes.

# Goals

This project has two goals.

- Allow the creation of button combinations to execute keyboard combinations.
- Expose the mapping functionality as a python library that allows a developer
  to map functional responses to button combination events.

# Features

- Multipress Button Combinations Ex. (3 x button clicks in 2 seconds)
- Timed Press Ex. (Hold Right trigger for 10 seconds)

# Why?

I use a program called Emulation Station DE to launch emulators with a controller.
Sometimes this requires some scripting on my part because some emulators lack the ability
to exit from a button mapped hotkey. 

I looked for programs that could map my joystick buttons to keys (so I can execute scripts from xbindkeys).
Some progrmas do this okay, such as antimicrox. Antimicrox lacks critical features such as button combination mapping
combinations. Additionally Antimicrox or the parent project Antimicro has arcane/elusive documentation.

Additional motivation for this project is a script that will allow me to display a pdf manual of a game I am 
playing launched from ES-DE. I want to navigate this pdf with button presses and resume gaming all from
the comfort of my controller.
