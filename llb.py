from Modules.Utils import *
import json
import re
import shutil
import os

class smHelper:
    logger = ""
    state = ""
    states = []
    def __init__(self, logger, states):
        self.logger = logger
        self.states = states
        self.state = states[0]

    def setState(self, state):
        if state in self.states:
            self.state = state
        else:
            self.logger.error("Invalid state: {0}".format(state))

    def isInState(self, state):
        if state == self.state:
            return True
        return False

class Field:
    definition = ""

    def __init__(self,  definition):
        self.definition = definition

class Pin:
    definition = ""
    # X name pin X Y length orientation sizenum sizename part dmg type shape

    def __init__(self,  definition):

        self.definition = definition
    def getName(self):
        return self.definition.split()[1]

    def getX(self):
        return self.definition.split()[3]

    def getY(self):
        return self.definition.split()[4]

    def getUnit(self):
        return self.definition.split()[9]

    def setX(self,val):
        t = self.definition.split()
        t[3] = str(val)
        self.definition = " ".join(t)

    def setY(self,val):
        t = self.definition.split()
        t[4] = str(val)
        self.definition = " ".join(t)

    def setUnit(self, val):
        t = self.definition.split()
        t[9] = str(val)
        self.definition = " ".join(t)

    def get(self, index):
        return self.definition.split()[index]

    def set(self, index, val):
        t = self.definition.split()
        t[index] = str(val)
        self.definition = " ".join(t)


def sort_pins_by_array(o):
    arrayPattern = re.compile("(\[\d+\])$")

    if arrayPattern.search(o.getName()):
        n = arrayPattern.search(o.getName()).group(0)
        n = n.replace("[", "")
        n = n.replace("]", "")
        return int(n)
    return -1


def sort_pins_by_suffix_number(o):
    arrayPattern = re.compile("(\d+)$")

    if arrayPattern.search(o.getName()):
        n = arrayPattern.search(o.getName()).group(0)
        return int(n)
    return -1


def sort_pins_by_name(o):
    return o.getName()



class Symbol:
    logger = ""
    name = ""
    fields = []
    pins = []
    definition = ""

    def __init__(self, logger, name, definition):
        self.logger = logger
        self.name = name
        self.fields = []
        self.pins = []
        self.definition = definition
        self.logger.info("Create symbol: {0}".format(name))

    def addField(self, field):
        self.fields.append(field)

    def addPin(self, pin):
        self.pins.append(pin)

    def getName(self):
        return self.name

    def getNumberOfUnits(self):
        return self.definition.split()[7]

    def setNumberOfUnits(self, val):
        t = self.definition.split()
        t[7] = str(val)
        self.definition = " ".join(t)

    def getNumberOfPins(self):
        return len(self.pins)


    def invalidateUnitAndPins(self):
        self.setNumberOfUnits(0)
        for pin in self.pins:
            pin.setUnit(-1)


    def addUnit(self,unitcfg):
        n = int(self.getNumberOfUnits())
        self.setNumberOfUnits(n+1)
        pinNames = dict.get(unitcfg, "pins")
        indexes = []
        idx = 0
        pins = []
        pinsloc = []
        for pinName in pinNames:
            pinPattern = re.compile("^" +  pinName)
            for pin in self.pins:
                if pinPattern.search(pin.getName()):
                    pinsloc.append(Pin(pin.definition))


            pinsloc = sorted(pinsloc, key=sort_pins_by_array)
            pinsloc = sorted(pinsloc, key=sort_pins_by_suffix_number)
            for pin in pinsloc:
                pins.append(Pin(pin.definition))
            pinsloc.clear()

        for pin in pins:
            for i, o in enumerate(self.pins):
                if o.getName() == pin.getName():
                    del self.pins[i]
                    break


        n = int(self.getNumberOfUnits())
        for pin in pins:
            pin.setUnit(n-1)
            self.addPin(Pin(pin.definition))


    def printPins(self):
        for pin in self.pins:
            self.logger.info("Pin: {0} \t Unit: {1}".format(pin.getName(), pin.getUnit()))

    def write_pins(self, file):
        for pin in self.pins:
            file.write("{0}\n".format(pin.definition))
    def write_definition(self, file):
        file.write("{0}\n".format(self.definition))
        for field in self.fields:
            file.write("{0}\n".format(field.definition))

# Read a library file in return the symbols in it
def read_kicad_library(file):
    f = open(file,'r')
    partDefStart = re.compile("^DEF")
    partDefStop  = re.compile("^ENDDEF")
    drawStart = re.compile("^DRAW")
    drawStop  = re.compile("^ENDDRAW")
    fieldDef = re.compile("^F[0-9]")
    pinDef = re.compile("^X ")

    symbols = []

    sm = smHelper(logger,["init", "parseDef", "parseDraw"])

    lines = f.readlines()
    lines = [line.rstrip() for line in lines]
    for line in lines:
        if partDefStart.search(line):
            if sm.isInState("init"):
                sym = Symbol(logger, line.split()[1], line)
                sm.setState( "parseDef")
            else:
                logger.error("Not in idle state")
        elif partDefStop.search(line):
            if sm.isInState("parseDef"):
                symbols.append(sym)
                sm.setState("init")
            else:
                logger.error("Not in parseDef state")
        elif drawStart.search(line):
            if sm.isInState("parseDef"):
                sm.setState("parseDraw")
            else:
                logger.error("Not in parseDef state")
        elif drawStop.search(line):
            if sm.isInState("parseDraw"):
                sm.setState("parseDef")
            else:
                logger.error("Not in parseDraw state")
        elif fieldDef.search(line):
            if sm.isInState("parseDef"):
                sym.addField(Field(line))
            else:
                logger.error("Not in parseDef state")

        elif pinDef.search(line):
            if sm.isInState("parseDraw"):
                sym.addPin(Pin(line))
            else:
                logger.error("Not in parseDraw state")

    for sym in symbols:
        logger.info("Symbol {0} has {1} units and {2} pins".format(sym.getName(),sym.getNumberOfUnits(),sym.getNumberOfPins()))


    return symbols




def get_symbol(symbolsIn, name):
    for sym in symbolsIn:
        if sym.getName() == name:
            return sym

    return None

def process_library(symbolsIn, jsonCfg):
    parts = dict.get(jsonCfg,"parts")
    for part in parts:
        name = dict.get(part, "partname")
        sym = get_symbol(symbolsIn, name)
        if sym is not None:
            sym.invalidateUnitAndPins()
            units = dict.get(part, "units")
            logger.info("Before Symbol {0} has {1} units and {2} pins".format(sym.getName(), sym.getNumberOfUnits(),
                                                                       sym.getNumberOfPins()))
            for unit in units:
                sym.addUnit(unit)

            sym.printPins()
        else:
            logger.error("Symbol {0} not found".format(name))

def write_library(path,name, symbols):
    if not os.path.isdir(path):
        #shutil.rmtree(path)
        os.mkdir(path)
    with open(path + "/" + name + ".lbr", "w+") as f:
        f.write("EESchema-LIBRARY Version 2.3\n")
        for sym in symbols:
            f.write("#\n")
            f.write("# Part: {0}\n".format(sym.getName()))
            f.write("#\n")
            sym.write_definition(f)
            f.write("{0}\n".format("DRAW"))
            sym.write_pins(f)
            f.write("{0}\n".format("ENDDRAW"))
            f.write("{0}\n".format("ENDDEF"))

if __name__ == "__main__":
    logger.info("Beautify KiCad Library")

    thisLoc = os.path.dirname(os.path.abspath(__file__))

    libFile = thisLoc + "/Libs/LL/SamacSys_Parts.lib"
    cfgFile = thisLoc + "/Config/Config.json"
    outPath = thisLoc + "/tmp"
    with open(cfgFile) as config_file:
        jsonCfg = json.load(config_file)


    symbols = read_kicad_library(libFile)
    process_library(symbols, jsonCfg)
    write_library(outPath,"test",symbols)


