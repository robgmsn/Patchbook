"""
PATCHBOOK MARKUP LANGUAGE & PARSER
CREATED BY SPEKTRO AUDIO
http://spektroaudio.com/
"""

import sys
import re
import os
import argparse
import json

# Parser INFO
parserVersion = "b2"

# Reset main dictionary
mainDict = {}

# Available connection types
connectionTypes = {
    "->": "audio",
    ">>": "cv",
    "p>": "pitch",
    "g>": "gate",
    "t>": "trigger",
    "c>": "clock"
}


# Reset global variables
lastModuleProcessed = ""
lastVoiceProcessed = ""

# Parse script arguments
parser = argparse.ArgumentParser()
parser.add_argument("-file", type=str, default="",
                        help="Name of the text file that will be parsed (including extension)")
parser.add_argument("-debug", type=int, default=0,
                    help="Enable Debugging Mode")
args = parser.parse_args()
filename = args.file
debugMode = args.debug

# Set up debugMode
if args.debug == 1:
    debugMode = True
else:
    debugMode = False

def initial_print():
    print()
    print("██████████████████████████████")  
    print("       PATCHBOOK PARSER       ")
    print("   Created by Spektro Audio   ")
    print("██████████████████████████████")
    print()
    print("Version " + parserVersion)
    print()


def get_script_path():
    # Get path to python script
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def getFilePath(filename):
    try:
        # Append script path to the filename
        base_dir = get_script_path()
        filepath = os.path.join(base_dir, filename)
        if debugMode: print("File path: " + filepath)
        return filepath
    except IndexError:
        pass

def parseFile(filename):
    # This function reads the txt file and process each line.
    lines = []
    try:
        print("Loading file: " + filename)
        with open(filename, "r") as file:
            for l in file:
                lines.append(l)
                regexLine(l)
    except TypeError:
        print("ERROR. Please add text file path after the script.")
    except FileNotFoundError:
        print("ERROR. File not found.")
    print("File successfully processed.")
    print()


def regexLine(line):
    global lastModuleProcessed
    global lastVoiceProcessed

    if debugMode: print()
    if debugMode: print("Processing: " + line)

    # CHECK FOR VOICES
    if debugMode: print("Cheking input for voices...")
    re_filter = re.compile(r"^([^\*]).+")  # Regex for "VOICE 1:"
    re_results = re_filter.search(line)
    try:
        # For some reason the Regex filter was still detecting parameter declarations as voices, 
        # so I'm also running the results through an if statement.
        results = re_results.group().replace(":", "") 
        if "*" not in results and "-" not in results and "|" not in results:
            if debugMode: print("New voice found: " + results.upper())
            lastVoiceProcessed = results.upper()
    except AttributeError:
        pass

    # CHECK FOR CONNECTIONS
    if debugMode: print("Cheking input for connections...")
    re_filter = re.compile(r"\-\s(.+)[(](.+)[)]\s(\>\>|\-\>|[a-z]\>)\s(.+)[(](.+)[)]")
    re_results = re_filter.search(line)
    try:
        results = re_results.groups()
        voice = lastVoiceProcessed
        if len(results) == 5:
            if debugMode: print("New connection found, parsing info...")
            addConnection(results, voice)
    except AttributeError:
        pass

    # CHECK PARAMETERS
    if debugMode: print("Checking for parameters...")
    # If single-line parameter declaration:
    if ":" in line and "*" in line:
        # Get module name
        module = line.split(": ")[0].replace("*", "").strip().lower()
        if debugMode: print("New module found: " + module)
        try:
            # If parameters are also declared
            parameters = line.split(": ")[1].split(" | ")
            for p in parameters:
                p = p.split(" = ")
                addParameter(module, p[0].strip().lower(), p[1].strip()) 
        except IndexError:
            if debugMode: print("No parameters found. Storing module as global variable...")
            lastModuleProcessed = module.replace(":", "").strip()

    # If multi-line parameter declaration:
    if "|" in line and "=" in line and "*" not in line:
        module = lastModuleProcessed.lower()
        if debugMode: print("Using global variable: " + module)
        parameter = line.split(" = ")[0].replace("|", "").strip().lower()
        value = line.split(" = ")[1].strip()
        addParameter(module, parameter, value)


def addConnection(list, voice="none"):
    global mainDict
    global connectionTypes

    if debugMode: print("Adding new connection...")
    if debugMode: print("-----")

    output_module = list[0].lower().strip()
    output_port = list[1].lower().strip()

    if debugMode: print("Output module: " + output_module)
    if debugMode: print("Output port: " + output_port)

    try:
        connection_type = connectionTypes[list[2].lower()]
        if debugMode: print("Matched connection type: " + connection_type)
    except KeyError:
        print("Invalid connection: " + list[2])
        connection_type = "cv"

    input_module = list[3].lower().strip()
    input_port = list[4].lower().strip()

    if debugMode: print("Input module: " + input_module)
    if debugMode: print("Input port: " + output_port)

    checkModuleExistance(output_module, output_port, "out")
    checkModuleExistance(input_module, input_port, "in")

    if debugMode: print("Appending output and input connections to mainDict...")
    mainDict[output_module]["connections"]["out"][output_port].append((input_module, input_port, connection_type, voice))
    mainDict[input_module]["connections"]["in"][input_port] = [output_module, output_port, connection_type, voice]
    if debugMode: print("-----")


def checkModuleExistance(module, port="port", direction=""):
    global mainDict

    if debugMode: print("Checking if module already existing in main dictionary: " + module)

    # Check if module exists in main dictionary
    if module not in mainDict:
        mainDict[module] = {}
        mainDict[module]["parameters"] = {}
        mainDict[module]["connections"] = {}
        mainDict[module]["connections"]["out"] = {}
        mainDict[module]["connections"]["in"] = {}

    # If it exists, check if the port exists
    if direction == "in":
        if port not in mainDict[module]["connections"]["in"]:
            mainDict[module]["connections"]["in"][port] = []

    if direction == "out":
        if port not in mainDict[module]["connections"]["out"]:
            mainDict[module]["connections"]["out"][port] = []


def addParameter(module, name, value):
    checkModuleExistance(module)
    # Add parameter to mainDict
    if debugMode: print("Adding parameter: " + module + " - " + name + " - " + value)
    mainDict[module]["parameters"][name] = value


def askCommand():
    command = input("> ").lower().strip()
    if command == "module":
        detailModule()
    elif command == "print":
        printDict()
    elif command == "export":
        exportJSON()
    elif command == "connections":
        printConnections()
    elif command == "graph":
        graphviz()
    else:
        print("Invalid command, please try again.")
    askCommand()


def detailModule():
    global mainDict
    module = input("Enter module name: ").lower()
    if module in mainDict:
        print("-------")
        print("Showing information for module: " + module.upper())
        print()
        print("Inputs:")
        for c in mainDict[module]["connections"]["in"]:
            keyvalue = mainDict[module]["connections"]["in"][c]
            print(keyvalue[0].title() + " (" + keyvalue[1].title() + ") > " + c.title() + " - " + keyvalue[2].title())
        print()

        print("Outputs:")
        for x in mainDict[module]["connections"]["out"]:
            port = mainDict[module]["connections"]["out"][x]
            for c in port:
                # print(str(c))
                keyvalue = c
                print(x.title() + " > " + keyvalue[0].title() + " (" + keyvalue[1].title() + ") " + " - " + keyvalue[2].title() + " - " + keyvalue[3])
        print()

        print("Parameters:")
        for p in mainDict[module]["parameters"]:
            value = mainDict[module]["parameters"][p]
            print(p.title() + " = " + value)
        print()

        print("-------")


def printConnections():
    print()
    print("Printing all connections by type...")
    print()

    for ctype in connectionTypes:
        ctype_name = connectionTypes[ctype]
        print("Connection type: " + ctype_name)
        # For each module
        for module in mainDict:
            # Get all outgoing connections:
            connections = mainDict[module]["connections"]["out"]
            for c in connections:
                connection = connections[c]
                for subc in connection:
                    # print(connection)
                    if subc[2] == ctype_name:
                        print(module.title() + " > " + subc[0].title() + " (" + subc[1].title() + ") ")
        print()


def exportJSON():
    # Exports mainDict as json file
    name = filename.split(".")[0]
    filepath = getFilePath(name + '.json')
    print("Exporting dictionary as file: " + filepath)
    with open(filepath, 'w') as fp:
        json.dump(mainDict, fp)


def graphviz():
    linetypes = {
        "audio": "[style=bold]",
        "cv": "[color=gray]",
        "gate": "[color=red, style=dashed]",
        "trigger": "[color=orange, style=dashed]",
        "pitch": "[color=blue]",
        "clock": "[color=purple, style=dashed]"
    }
    print("Generating signal flow code for GraphViz.")
    print("Copy the code between the line break and paste it into https://dreampuf.github.io/GraphvizOnline/ to download a SVG / PNG chart.")
    conn = []
    total_string = ""
    print("-------------------------")
    print("digraph G{\nrankdir = LR;\nsplines = polyline;\nordering=out;")
    total_string += "digraph G{\nrankdir = LR;\nsplines = polyline;\nordering=out;\n"
    for module in sorted(mainDict):

        # Get all outgoing connections:
        outputs = mainDict[module]["connections"]["out"]
        module_outputs = ""
        out_count = 0
        for out in sorted(outputs):
            out_count += 1
            out_formatted = "_" + re.sub('[^A-Za-z0-9]+', '', out)
            module_outputs += "<" + out_formatted + "> " + out.upper()
            if out_count < len(outputs.keys()):
                module_outputs += " | "
            connections = outputs[out]
            for c in connections:
                line_style = ""
                try:
                    line_style = linetypes[c[2]]
                except KeyError:
                    pass
                in_formatted = "_" + re.sub('[^A-Za-z0-9]+', '', c[1])
                connection_line = module.replace(" ", "") + ":" + out_formatted + ":e  -> " + c[0].replace(" ", "") + ":" + in_formatted + ":w " + line_style
                conn.append([c[2], connection_line])

        # Get all incoming connections:
        inputs = mainDict[module]["connections"]["in"]
        module_inputs = ""
        in_count = 0
        for inp in sorted(inputs):
            inp_formatted = "_" + re.sub('[^A-Za-z0-9]+', '', inp)
            in_count += 1
            module_inputs += "<" + inp_formatted + "> " + inp.upper()
            if in_count < len(inputs.keys()):
                module_inputs += " | "


        # Get all parameters:
        params = mainDict[module]["parameters"]
        module_params = ""
        in_count = 0
        for inp in sorted(params):
            inp_formatted = "_" + re.sub('[^A-Za-z0-9]+', '', inp)
            in_count += 1
            module_params += inp.title() + " = " + params[inp]
            if in_count < len(params.keys()):
                module_params += r'\n'


        final_box = module.replace(" ", "") + "[label=\"{ {" + module_inputs + "}|{{" + module.upper() + "}|{" + module_params + "}}| {" + module_outputs + "}}\"  shape=Mrecord]";
        print(final_box)
        total_string += final_box + "; "

    # Print Connections
    for c in sorted(conn):
        print(c[1])
        total_string += c[1] + "; "

    print("}")
    total_string += "}"

    print("-------------------------")
    print()
    return total_string

def printDict():
    global mainDict
    for key in mainDict:
        print(key.title() + ": " + str(mainDict[key]))


if __name__ == "__main__":
    initial_print()
    parseFile(filename)
    askCommand()
