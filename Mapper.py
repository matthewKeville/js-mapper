import subprocess
import re  # search
import warnings
import json
import argparse
import copy

ALLOW_MISMATCHED_HANDLERS = False
MAX_VALUE = 32000
MIN_VALUE = 32000



# -----------------------------------------------------------------------------
# Transformation
# -----------------------------------------------------------------------------

# TBD

# -----------------------------------------------------------------------------
# Events
# -----------------------------------------------------------------------------

"""
Return True iff the state
matches the combination
"""

def named_print(Value):
    print(Value)


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


# -----------------------------------------------------------------------------
# Triggers
# -----------------------------------------------------------------------------

"""
 Triggers take in a State timeline
    [
        {   Time: "xxx",
            State: [x,y,z]
        }, 
        ...
    ]
"""


"""
Currently in state
"""

def in_state(State_Matrix, Combo):
    current_state = (State_Matrix[-1])["State"]
    for x in Combo:
        if current_state[x] != 1:
            return False
    return True


"""
Entered into this state, but not previously here
"""

def enter_state(State_Matrix, Combo):
    if (len(State_Matrix) < 2):
        return False
    previous_state = (State_Matrix[-2])["State"]
    current_state = (State_Matrix[-1])["State"]

    # Not previously in state
    already_in_state = True
    for x in Combo:
        already_in_state = already_in_state and (previous_state[x] == 1)

    if (already_in_state):
        return False

    # In State Now?
    for x in Combo:
        if current_state[x] != 1:
            return False
    # Wasn't in this state previously but am now!
    return True



"""
previously in this state, but now no longer
"""


def exit_state(State_Matrix, Combo):
    if (len(State_Matrix) < 2):
        return False
    previous_state = (State_Matrix[-2])["State"]
    current_state = (State_Matrix[-1])["State"]

    for x in Combo:
        if (previous_state[x] != 1):
            return False

    for x in Combo:
        if (current_state[x] != 1):
            return True

    return False

"""
    If the given combo is pressed *Multiplicity* times
    in the Duration given in seconds, return true
    Do not recount previous presses for new multipresses
"""

def multipress_state(State_Matrix, Combo, Multiplicity, Duration):
    if (len(State_Matrix) < 2):
        return False
    # Duration is in seconds
    # input time is 1 / 2^10 ratio
    current_time = (State_Matrix[-1])["Time"]
    input_time_min = current_time - (Duration * 1024)

    # find earliest valid state 

    earliest_valid_index = 0  # relative to the end
    while (earliest_valid_index < len(State_Matrix)):
        if (State_Matrix[-1*(earliest_valid_index+1)])["Time"] > input_time_min:
            earliest_valid_index = earliest_valid_index+1
        else:
            break
   
    occurrences = 0
    for state in State_Matrix[-earliest_valid_index:]:
        valid = True
        for c in Combo:
            if (state["State"])[c] != 1:
                valid = False
        if (valid):
            occurrences = occurrences + 1

    # was the combo fired this state?
    for c in Combo:
        if ((State_Matrix[-1])["State"])[c] != 1:
            return False

    # fires once 
    return (occurrences == Multiplicity)








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


def dump_state_matrix(state_matrix):
    for state in state_matrix:
        print(f'{state["Time"]} : {state["State"]}')



# -----------------------------------------------------------------------------
# Evaluation
# -----------------------------------------------------------------------------



"""
Check the handlers dictionary for handle that
acts on the current state of the digital buttons.
If that handle matches the current state. Execute
that handler
"""


def process_digital_binds(digital_state_matrix, binds):
    try:
        for bind in binds:
            process_bind(digital_state_matrix, bind)
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


def process_bind(state_matrix, bind):

    if not bind["Trigger"]:
        return

    kwargs = (bind["Trigger"])["Parameters"]
    kwargs["State_Matrix"] = state_matrix
    try:
        #print(f'Checking {bind["Name"]}')
        fire = function_wrapper((bind["Trigger"])["Function"], kwargs)
    except Exception as e1:
        print(f'error checking trigger for bind {bind["Name"]}')
        print(bind["Trigger"])
        print(e1)


    # print(f' The Bind Trigger is {fire}')

    if (fire):
        print(f'The bind named {bind["Name"]} has triggered')
        try:
            kwargs = (bind["Event"])["Parameters"]
            function_wrapper((bind["Event"])["Function"], kwargs)
        except Exception as e2:
            print(f'error firing event')
            print(bind["Event"])

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
    elif (trigger["Type"] == "enter_state"):
        trigger_model["Function"] = enter_state
        trigger_model["Parameters"] = trigger["Parameters"]
    elif (trigger["Type"] == "exit_state"):
        trigger_model["Function"] = exit_state
        trigger_model["Parameters"] = trigger["Parameters"]
    elif (trigger["Type"] == "multipress_state"):
        trigger_model["Function"] = multipress_state
        trigger_model["Parameters"] = trigger["Parameters"]
    else:
        pass

    # Event
    event = bind["Event"]
    event_model = {}
    if (event["Type"] == "print_message"):
        event_model["Function"] = named_print
        event_model["Parameters"] = event["Parameters"]
        pass
    elif (event["Type"] == "press_keys"):
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
        a = config["Analog"]
        virtual_binds = parse_analog(a)

        return (digital_binds, virtual_binds)

    except Exception as e:
        print("Error Parsing Config")
        print(f"Error {e}")
        exit(5)

"""
    Return a list of binds
"""
def parse_digital(d):
    digital_binds = []
    for bind in d["Binds"]:
        digital_binds.append(parse_bind(bind))
    return digital_binds


"""
    Return a list of virtual binds
    virtual bind is a (transformation, and bind array)
"""
def parse_analog(a):
    virtual_binds = []
    # for virtual in a["Virtuals"]:
    #    virtual_model = {"Name": virtual["Name"]}
    return virtual_binds



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

(digital_binds, virtual_binds) = parse_config(config_string)
print(digital_binds)


# -----------------------------------------------------------------------------
# Testing Handles
# -----------------------------------------------------------------------------



"""
digital_binds.append({
        "Name": "Debug0",
        "Trigger": {
            "Function": lambda States, Key: ((States[-1])[Key] == 1), # A boolean function that evalutates if state triggers bind,
                                                                       # When triggers are evaluated state is injected into the kwargs
            "Parameters": {"Key": 0}
        },
        "Event": {
            "Function": lambda Debug: print(f'Debug Handle {Debug} triggered'), # A function that execute in response to Trigger activation
                                                                                # These function must defined kwargs that map to Parameters
            "Parameters": { "Debug": 0}
        }
})
"""




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
digital_state_matrix = []
analog = [0 for x in range(len(Axes))]
analog_state_matrix = []
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
            digital_state = {"Time": int(Time), "State": digital}

            digital_state_matrix.append(copy.deepcopy(digital_state)) 

            process_digital_binds(digital_state_matrix, digital_binds)
           
            #print("--------------------------------")
            #dump_state_matrix(digital_state_matrix)

        elif (Type == "2"):  # Analog Press
            pass
            # analog[int(Number)] = int(Value)
            # analog_state_matrix.append(list(analog)) 

    except Exception as e:
        print("Unexpected Error " + str(e))

process.kill()



