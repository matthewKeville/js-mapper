import subprocess
import re  # search
import warnings
import json
import argparse

ALLOW_MISMATCHED_HANDLERS = False
MAX_VALUE = 32000
MIN_VALUE = 32000



# -----------------------------------------------------------------------------
# Events
# -----------------------------------------------------------------------------

"""
Return True iff the state
matches the combination
"""

def named_print(Value):
    print(Value)


# -----------------------------------------------------------------------------
# Triggers
# -----------------------------------------------------------------------------


def in_state(State, Combo):
    for x in Combo:
        if State[x] != 1:
            return False
    return True



# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------


"""
Execute the function func with the keyword args (kwards)
From the dictionary
"""


def function_wrapper(func, kwargs):
    if kwargs:
        return func(**kwargs)
    else:
        print("This function wrapper makes no sense")
        print("Quiting ... ")


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
    subprocess.Popen(argArray)



# -----------------------------------------------------------------------------
# Evaluation
# -----------------------------------------------------------------------------



"""
Check the handlers dictionary for handle that
acts on the current state of the digital buttons.
If that handle matches the current state. Execute
that handler
"""


def process_digital_binds(digital, binds):
    try:
        for bind in binds:
            process_bind(digital, bind)
    except Exception as e:
        print("Error Processing Digital Binds " + str(e))

"""
"Name": "Debug0",
"Trigger": {
    "Function": lambda State, Key: (State[Key] == 1), # A boolean function that evalutates if state triggers bind,
                                                               # When triggers are evaluated state is injected into the kwargs
    "Parameters": {"Key": 0}
},
"Handle": {
    "Function": lambda Debug: print(f'Debug Handle {Debug} triggered'), # A function that execute in response to Trigger activation
                                                                        # These function must defined kwargs that map to Parameters
    "Parameters": { "Debug": 0}
}
"""


def process_bind(state, bind):

    # print(f' Evaluating Bind {bind["Name"]}')

    kwargs = (bind["Trigger"])["Parameters"]
    kwargs["State"] = state
    fire = function_wrapper((bind["Trigger"])["Function"], kwargs)

    # print(f' The Bind Trigger is {fire}')

    if (fire):
        print(f' The bind named {bind["Name"]} has triggered')

        kwargs = (bind["Event"])["Parameters"]
        function_wrapper((bind["Event"])["Function"], kwargs)

"""
Given a list of axes and a rule
transform the state of the axes into 
a finite digital state. This can transform multiple axes into 
one state arrray. Or just 1 axis to one state array.
"""


def transform_axes_to_digital_state(axes, rule):
    if rule == "trigger":
        # anticipate axes to be an array with one value
        u = axes[0]
        if (u > 0 ):
            return [0, 1]
        else:
            return [1, 0]
        pass
    elif rule == "joystick":
        # anticipate axes to be an array with two values
        # zones = 4
        # deadzone_percentage = .30
        pass
    else:
        print("Unknown transformation quiting ..")
        exit(10)


"""
Given an xdotool complaint keystroke string
Run xdotool to simulate that key combination press
"""


def press_keys(Keystroke):
    try:
        command = f'xdotool key {Keystroke}'
        execute(command)
    except Exception as e:
        print(f'There was an error running xdotool key {Keystroke}')
        print(f'Exception {e}')


"""
 given a ButtonCombo expressed as a list 
 of button indices that are active 
 return an equivalent digital state array
"""


def short_state_to_long_state(short, size):
    state = []
    for i in range(size):
        x = 0
        if i in short:
            x = 1
        state.append(x)
    return state


# -----------------------------------------------------------------------------
# Parsing
# -----------------------------------------------------------------------------


def parse_bind(bind):
    # Name
    model = {"Name": bind["Name"]}

    # Trigger
    trigger = bind["Trigger"]
    trigger_model = {}
    if (trigger["Type"] == "in_state"):
        trigger_model["Function"] = in_state
        trigger_model["Parameters"] = trigger["Parameters"]
    else:
        pass

    # Event
    event = bind["Event"]
    event_model = {}
    if (event["Type"] == "print"):
        event_model["Function"] = named_print
        event_model["Parameters"] = event["Parameters"]
        pass
    elif (event["Type"] == "xkeys"):
        event_model["Function"] = press_keys
        event_model["Parameters"] = event["Parameters"]

    model["Trigger"] = trigger_model
    model["Event"] = event_model
    return model

"""
    Return a list of digital binds
    Return a list of lists virtual binds
"""
def parse_config(json_string):
    try:
        config = json.loads(json_string)

        # Process Digital
        d = config["Digital"]
        digital_binds = parse_digital(d)


        # Process Analog
        # a = config["Analog"]
        # parse_analog(a)
        analog_binds = []

        return (digital_binds, analog_binds)

    except Exception as e:
        print("Error Parsing Config")
        print(f"Error {e}")
        exit(5)


def parse_digital(d):
    digital_binds = []
    for bind in d["Binds"]:
        digital_binds.append(parse_bind(bind))
    return digital_binds


def parse_analog(a):
    pass



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
    print("Mismatched Binds Enabled")
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

# TODO Verify Device is valid
device_path = args.device
digital_binds = []

(digital_binds, analog_binds) = parse_config(config_string)
print(digital_binds)


# -----------------------------------------------------------------------------
# Testing Handles
# -----------------------------------------------------------------------------


#digital_binds.append({
#        "ButtonCombo": short_state_to_long_state([0], 11),
#        "Handle": lambda n: print(f'Debug Handle {n} triggered'),
#        "Args": [1]
#})

digital_binds.append({
        "Name": "Debug0",
        "Trigger": {
            "Function": lambda State, Key: (State[Key] == 1), # A boolean function that evalutates if state triggers bind,
                                                                       # When triggers are evaluated state is injected into the kwargs
            "Parameters": {"Key": 0}
        },
        "Event": {
            "Function": lambda Debug: print(f'Debug Handle {Debug} triggered'), # A function that execute in response to Trigger activation
                                                                                # These function must defined kwargs that map to Parameters
            "Parameters": { "Debug": 0}
        }
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
analog = [0 for x in range(len(Axes))]
running = True

# -----------------------------------------------------------------------------
# Discard Testing Lines
# -----------------------------------------------------------------------------

for x in range(TestLines):
    process.stdout.readline()


# -----------------------------------------------------------------------------
# Validate Handler
# -----------------------------------------------------------------------------


# for handle in handlers:
#    if (len(handle["ButtonCombo"]) != len(digital)):
#        warnings.warn("Button Handle is different dimension then Button State")
#        if (not ALLOW_MISMATCHED_HANDLERS):
#            print("Registered Button Combo\n" + str(handle['ButtonCombo']))
#            print("But ButtonState is\n" + str(digital))
#            exit(2)


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

        Strings = [EventString, TimeString, NumberString, ValueString] = line.split(',')

        Type = EventString[-1]
        Time = TimeString.strip().split(' ')[1]
        Number = NumberString.strip().split(' ')[1]
        Value = ValueString.strip().split(' ')[1]

        if (Type == "1"):  # Digital Press

            Time = TimeString.strip().split(' ')[1]
            Number = NumberString.strip().split(' ')[1]
            Value = ValueString.strip().split(' ')[1]
            digital[int(Number)] = int(Value)


            process_digital_binds(digital, digital_binds)
        elif (Type == "2"):  # Analog Press

            analog[int(Number)] = int(Value)


        # print(f'digital {digital}')
        # print(f'analog  {analog}')
        # left_trigger = transform_axes_to_digital_state([analog[2]], "trigger")
        # right_trigger = transform_axes_to_digital_state([analog[5]], "trigger")

    except Exception as e:
        print("Unexpected Error " + str(e))

process.kill()



