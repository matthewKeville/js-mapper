import subprocess
import io
import os
import re  # search

# This is broken for pipelines , this is broken for escaped spaces

# Given Left and Right Chars, return a list of strings that are
# between these chars with no overlapping results
def CapturedStrings(leftChar, rightChar, string):
    escLeft = re.escape(leftChar)
    escRight = re.escape(rightChar)
    regex = "(?<="+escLeft+").+?(?="+escRight+")"
    return re.findall(regex, string)

def Execute(command):
    argArray = command.split(" ")
    print("arg array to execute")
    print(argArray)
    subprocess.Popen(argArray)


def ProcessState(digital, handlers):
    print(f'{digital} -> State')
    try:
        for handle in handlers:
            print(f'{handle["ButtonCombo"]} -> handle')
            if handle['ButtonCombo'] == digital:
                print(f'Executing cmd {handle["Handle"]}')
                handle['Handle']()
    except Exception as e:
        print("Error Processing Handlers " + str(e))


# -----------------------------------------------------------------------------


handlers = []
handlers.append({
        "ButtonCombo": [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        "Handle": lambda: print("Combo 0")
})
handlers.append({
        "ButtonCombo": [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
        "Handle": lambda: print("Combo 1")
})


# def toggle_fullscreen():
#     Execute('xdotool key super+f')

# handlers.append({
#         "ButtonCombo": [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
#         "Handle": toggle_fullscreen
# })


def focus_mupdf():
    Execute('i3-msg "[id="`wmctrl -l | grep "SuperMonkey" | cut -d " "  -f 1`"] focus"')


# Execute broken on ~
def launch_mupdf():
    Execute('mupdf -r 200 /home/galaxy/downloads/SuperMonkeyBall.pdf')
    focus_mupdf()



# handlers.append({
#        "ButtonCombo": [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
#         "Handle": launch_mupdf
#})


# -----------------------------------------------------------------------------

discard = 30
digital = [0 for x in range(11)] # xbox one controller
viewing_manual = True

# https://stackoverflow.com/questions/1606795/catching-stdout-in-realtime-from-subprocess
# Albert is a wizard! without stdbuf This setup will readlines in batches, i don't want that
process = subprocess.Popen(["stdbuf", "-oL", '/usr/bin/jstest', '--select', '/dev/input/js0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# -----------------------------------------------------------------------------
# Process Start Output
# -----------------------------------------------------------------------------

rawline = process.stdout.readline()
FirstLine = rawline.rstrip().decode('utf-8')

# Startup Error ?

if (FirstLine == ""):
    rawline = process.stderr.readline()
    print("Unable to start jstest")
    if rawline.rstrip().decode("utf-8") == "jstest: No such file or directory":
        print("The Target Joystick is not connected")
    exit(1)
else:
    print("Target joystick found")

# Ok?

DriverLine = FirstLine
print(f'Driver Line is {DriverLine}')
rawline = process.stdout.readline()
ButtonLine1 = rawline.rstrip().decode('utf-8')
# Get Controller Name
# Matches = re.search('('+'(.+?)'+')', ButtonLine1)
# Matches = re.findall(r'(?<=\().+?(?=\))', ButtonLine1)
Matches = CapturedStrings('(', ')', ButtonLine1)
Name = Matches[0].replace(" ", "")
Axes = Matches[1].replace(" ", "").split(",")
print(f'Button Line 1 is {ButtonLine1}')
print(f'Controller Name {Name}')
print(f'Axes {Axes}')
rawline = process.stdout.readline()
ButtonLine2 = rawline.rstrip().decode('utf-8')
Matches = CapturedStrings('(', ')', ButtonLine2)
Buttons = Matches[0].replace(" ", "").split(",")
print(f'Button Line 2 is {ButtonLine2}')
print(f'Buttons {Buttons}')
TestLines = len(Buttons)+len(Axes)

# Line 0 : Driver Version
# Line 1 : Joystick name and axes (...)
# Line 2 : and buttons (...)


# -----------------------------------------------------------------------------
# Process Normal Execution
# -----------------------------------------------------------------------------

while viewing_manual:
    rawline = process.stdout.readline()
    if (TestLines != 0):
        TestLines -= 1
        continue
    if not rawline:
        break
    line = rawline.rstrip().decode('utf-8')
    try:
        # Type, Time , Number , Value
        PressEvent = [EventString, TimeString, NumberString, ValueString] = line.split(',')
        Type = EventString[-1]
        if (Type == "1"):  # Digital Press
            Time = TimeString.strip().split(' ')[1]
            Number = NumberString.strip().split(' ')[1]
            Value = ValueString.strip().split(' ')[1]
            digital[int(Number)] = int(Value)
            ProcessState(digital, handlers)
        else: # Analog Press
            pass
        print(digital)
    except Exception as e:
        print("Unexpected Error " + str(e))

process.kill()



