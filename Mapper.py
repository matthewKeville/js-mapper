import subprocess
import re  # search
import warnings
import json
import argparse

ALLOW_MISMATCHED_HANDLERS = False

"""
Execute the function func with the arguments from args
"""


def function_wrapper(func, args):
    print("the arg array is")
    print(args)
    if args:
        func(*args)
    else:
        func()


"""
Return all non overlapping strings between two chars 
"""


def captured_strings(leftChar, rightChar, string):
    escLeft = re.escape(leftChar)
    escRight = re.escape(rightChar)
    regex = "(?<="+escLeft+").+?(?="+escRight+")"
    return re.findall(regex, string)


""" 
Execute a shell command
 - This is broken for pipes
 - This is broken for escaped spaces
"""


def execute(command):
    argArray = command.split(" ")
    print("arg array to execute")
    print(argArray)
    subprocess.Popen(argArray)


"""
Check the handlers dictionary for handle that
acts on the current state of the digital buttons.
If that handle matches the current state. Execute
that handler
"""


def process_digital_state(digital, handlers):
    print(f'{digital} -> State')
    try:
        for handle in handlers:
            if handle['ButtonCombo'] == digital:
                print(f'Executing cmd {handle["Handle"]}')
                function_wrapper(handle['Handle'], handle['Args'])
    except Exception as e:
        print("Error Processing Handlers " + str(e))


"""
Given an xdotool complaint keystroke string
Run xdotool to simulate that key combination press
"""


def press_keys(keys):
    try:
        command = f'xdotool key {keys}'
        execute(command)
    except Exception as e:
        print(f'There was an error running xdotool key {keys}')
        print(f'Exception {e}')


"""
 given a ButtonCombo expressed as a list 
 of button indices that are active 
 return an equivalent digital state array
"""


def short_state_to_long_state(short, size):
    state = []
    for i in range(size):
        print(i)
        x = 0
        if i in short:
            x = 1
        state.append(x)
    return state



def parse_config(json_string):
    try:
        config = json.loads(json_string)
        if config["Type"] == "xkeys":
            return parse_xkeys_config(config)
        else:
            print(f"Unknown configuration type {config['Type']}")
    except Exception as e:
        print(f"Error parsing {config['Type']} configuration")
        print(f"Error {e}")
        exit(5)
    

# Return a list of handlers
def parse_xkeys_config(config):
    handlers = []
    for bind in config["DigitalBinds"]:
        state = short_state_to_long_state(bind["ButtonCombo"], config["DigitalKeys"])
        keystroke = bind["Keystroke"]
        handlers.append({
                "ButtonCombo": state,
                "Handle": press_keys,
                "Args": [keystroke]
        })
    return handlers



# -----------------------------------------------------------------------------
# User Args
# -----------------------------------------------------------------------------


parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config")
parser.add_argument("-f", "--config-file")
parser.add_argument("-d", "--device", required=True)
parser.add_argument("-M", "--allow-mismatch", action='store_true', default=False)
args = parser.parse_args()
print(args)
if (args.allow_mismatch is True):
    ALLOW_MISMATCHED_HANDLERS = True
    print("Mismatched Handlers Enabled")
if (args.config is None and args.config_file is None):
    print("You must supply a config or config file")
    exit(3)
if (args.config_file is not None):
    try: 
        file_handle = open(args.config_file, "r")
        config_string = file_handle.read()
    except Exception as e:
        print(f'Failed to read config file {args.config_file}')
        print(f'Exception {str(e)}')
        exit(4)
else:
    config_string = args.config

print(config_string)

# TODO Verify Device is valid
device_path = args.device
handlers = parse_config(config_string)
print(handlers)


# -----------------------------------------------------------------------------
# Testing Handles
# -----------------------------------------------------------------------------


handlers.append({
        "ButtonCombo": short_state_to_long_state([0], 11),
        "Handle": lambda n: print(f'Debug Handle {n} triggered'),
        "Args": [1]
})




# -----------------------------------------------------------------------------
# jstest Start
# -----------------------------------------------------------------------------

# https://stackoverflow.com/questions/1606795/catching-stdout-in-realtime-from-subprocess
# Albert is a wizard! without stdbuf This setup will readlines in batches, i don't want that
process = subprocess.Popen(["stdbuf", "-oL", '/usr/bin/jstest', '--select', device_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
rawline = process.stdout.readline()
ButtonLine1 = rawline.rstrip().decode('utf-8')
# Get Controller Name
# Matches = re.search('('+'(.+?)'+')', ButtonLine1)
# Matches = re.findall(r'(?<=\().+?(?=\))', ButtonLine1)
Matches = captured_strings('(', ')', ButtonLine1)
Name = Matches[0].replace(" ", "")
Axes = Matches[1].replace(" ", "").split(",")
print(f'Controller Name {Name}')
print(f'Axes {Axes}')
rawline = process.stdout.readline()
ButtonLine2 = rawline.rstrip().decode('utf-8')
Matches = captured_strings('(', ')', ButtonLine2)
Buttons = Matches[0].replace(" ", "").split(",")
print(f'Buttons {Buttons}')
TestLines = len(Buttons)+len(Axes)


# -----------------------------------------------------------------------------
# Joystick State Initialization
# -----------------------------------------------------------------------------

digital = [0 for x in range(len(Buttons))]
analag = [0 for x in range(len(Axes))]
running = True

# -----------------------------------------------------------------------------
# Discard Testing Lines
# -----------------------------------------------------------------------------

for x in range(TestLines):
    process.stdout.readline()


# -----------------------------------------------------------------------------
# Validate Handler
# -----------------------------------------------------------------------------

for handle in handlers:
    if (len(handle["ButtonCombo"]) != len(digital)):
        warnings.warn("Button Handle is different dimension then Button State")
        if (not ALLOW_MISMATCHED_HANDLERS):
            print("Registered Button Combo\n" + str(handle['ButtonCombo']))
            print("But ButtonState is\n" + str(digital))
            exit(2)


# -----------------------------------------------------------------------------
# Process Normal Execution
# -----------------------------------------------------------------------------


while running:
    rawline = process.stdout.readline()
    exit_code = process.poll()
    if exit_code is not None:
        if exit_code == 0:
            print("jstest has terminated gracefully")
            break
        print(f'jstest exited with error code {exit_code}')
        try:
            rawerrorline = process.stderr.read()
            print(f'This error occurred {errorline}')
        except Exception as e:
            pass
        break
    line = rawline.rstrip().decode('utf-8')
    try:
        [EventString, TimeString, NumberString, ValueString] = line.split(',')
        Type = EventString[-1]
        if (Type == "1"):  # Digital Press

            Time = TimeString.strip().split(' ')[1]
            Number = NumberString.strip().split(' ')[1]
            Value = ValueString.strip().split(' ')[1]

            digital[int(Number)] = int(Value)
            process_digital_state(digital, handlers)
        elif (Type == "2"):  # Analog Press
            print("An Analog press has transpired")
        print(digital)
    except Exception as e:
        print("Unexpected Error " + str(e))

process.kill()



