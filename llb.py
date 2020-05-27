from Modules.Utils import *
import json
import re
import shutil
import os
import shlex
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

    def getX(self):
        return shlex.split(self.definition, posix=False)[2]

    def getY(self):
        return shlex.split(self.definition, posix=False)[3]

    def setX(self,val):
        t = shlex.split(self.definition, posix=False)
        t[2] = str(val)
        self.definition = " ".join(t)

    def setY(self,val):
        t = shlex.split(self.definition, posix=False)
        t[3] = str(val)
        self.definition = " ".join(t)

    def getIndex(self):
        t = shlex.split(self.definition, posix=False)[0]
        t = t.replace("F", "")
        return int(t)

class Pin:
    definition = ""
    # X name pin X Y length orientation sizenum sizename part dmg type shape

    def __init__(self,  definition):

        self.definition = definition
    def getName(self):
        return shlex.split(self.definition, posix=False)[1]

    def getX(self):
        return shlex.split(self.definition, posix=False)[3]

    def getY(self):
        return shlex.split(self.definition, posix=False)[4]

    def getUnit(self):
        return shlex.split(self.definition, posix=False)[9]

    def setX(self,val):
        t = shlex.split(self.definition, posix=False)
        t[3] = str(val)
        self.definition = " ".join(t)

    def setY(self,val):
        t = shlex.split(self.definition, posix=False)
        t[4] = str(val)
        self.definition = " ".join(t)

    def setUnit(self, val):
        t = shlex.split(self.definition, posix=False)
        t[9] = str(val)
        self.definition = " ".join(t)

    def setOrientation(self, val):
        t = shlex.split(self.definition, posix=False)
        t[6] = str(val)
        self.definition = " ".join(t)

    def disableVisibilityOnAllSheets(self):
        t = shlex.split(self.definition, posix=False)
        t[6] = str(val)
        self.definition = " ".join(t)

    def get(self, index):
        return shlex.split(self.definition, posix=False)[index]


    def set(self, index, val):
        t = shlex.split(self.definition, posix=False)
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
    outlines = []
    drawspecs = []
    def __init__(self, logger, name, definition):
        self.logger = logger
        self.name = name
        self.fields = []
        self.pins = []
        self.outlines = []
        self.drawspecs = []
        self.definition = definition
        self.logger.info("Create symbol: {0}".format(name))

    def addField(self, field):
        self.fields.append(field)

    def addPin(self, pin):
        self.pins.append(pin)

    def addDrawSpec(self, spec):
        self.drawspecs.append(spec)

    def getName(self):
        return self.name

    def getNumberOfUnits(self):
        return shlex.split(self.definition, posix=False)[7]

    def setNumberOfUnits(self, val):
        t = shlex.split(self.definition, posix=False)
        t[7] = str(val)
        self.definition = " ".join(t)

    def getNumberOfPins(self):
        return len(self.pins)

    def getFootprint(self):
        for field in self.fields:
            if field.getIndex() == 2:
                return shlex.split(field.definition, posix=False)[1]

    def invalidateUnitAndPins(self):
        self.setNumberOfUnits(0)
        for pin in self.pins:
            pin.setUnit(-1)

    def delete_draw_specs(self):
        self.drawspecs = []

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
        y = -100
        incr = y
        longestPinName = 0
        for pin in pins:
            if len(pin.getName()) > longestPinName:
                longestPinName = len(pin.getName())
            pin.setUnit(n)
            pin.setX(0)
            pin.setY(y)
            y = y + incr
            pin.setOrientation("R")
            self.addPin(Pin(pin.definition))
        xstart = 200
        xend = xstart + (longestPinName + 3) *50

        self.outlines.append("S {0} {1} {2} {3} {4} 1 6 N".format(xstart,0,xend,y,n))

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

    def write_outline(self,file):
        for outline in self.outlines:
            file.write("{0}\n".format(outline))
        for drawspec in self.drawspecs:
            file.write("{0}\n".format(drawspec))



# Read a library file in return the symbols in it
def extract_symbols_from_lib(path, file,jsonCfg):
    libFile = path + "/" + file + ".lib"
    dcmFile = path + "/" + file + ".dcm"

    f = open(libFile,'r')
    partDefStart = re.compile("^DEF")
    partDefStop  = re.compile("^ENDDEF")
    drawStart = re.compile("^DRAW")
    drawStop  = re.compile("^ENDDRAW")
    fieldDef = re.compile("^F[0-9]")
    pinDef = re.compile("^X ")

    symbols = []
    names = []
    parts = dict.get(jsonCfg,"parts")
    for part in parts:
        names.append(dict.get(part, "partname"))



    sm = smHelper(logger,["init", "parseDef", "parseDraw"])

    lines = f.readlines()
    lines = [line.rstrip() for line in lines]
    for line in lines:
        if partDefStart.search(line):
            if sm.isInState("init"):
                name = shlex.split(line, posix=False)[1]
                if name in names:
                    sym = Symbol(logger, shlex.split(line, posix=False)[1], line)
                    sm.setState( "parseDef")
            else:
                logger.error("Not in init state")
        elif partDefStop.search(line):
            if sm.isInState("parseDef"):
                symbols.append(sym)
                sm.setState("init")

        elif drawStart.search(line):
            if sm.isInState("parseDef"):
                sm.setState("parseDraw")

        elif drawStop.search(line):
            if sm.isInState("parseDraw"):
                sm.setState("parseDef")

        elif fieldDef.search(line):
            if sm.isInState("parseDef"):
                field = Field(line)
                #if field.getIndex() < 3:
                field.setX(0)
                sym.addField(field)

        elif pinDef.search(line):
            if sm.isInState("parseDraw"):
                sym.addPin(Pin(line))

        else:
            if sm.isInState("parseDraw"):
                sym.addDrawSpec(line)
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
    symbolsOut = []
    for part in parts:
        name = dict.get(part, "partname")
        sym = get_symbol(symbolsIn, name)
        if sym is not None:
            units = dict.get(part, "units")
            if units is not None:
                sym.delete_draw_specs()
                sym.invalidateUnitAndPins()
                logger.info("Before Symbol {0} has {1} units and {2} pins".format(sym.getName(), sym.getNumberOfUnits(),
                                                                           sym.getNumberOfPins()))
                for unit in units:
                    sym.addUnit(unit)
        else:
            logger.error("Symbol {0} not found".format(name))


def write_library(outPath,outlibfilename,jsonCfg,InFpDir,In3dDir,symbols):

    OutFpDir = outPath + "/" + outlibfilename + ".pretty"
    Out3dDir = outPath + "/" + outlibfilename + ".3dshape"

    if not os.path.isdir(outPath):
        #shutil.rmtree(path)
        os.mkdir(path)

    if not os.path.isdir(OutFpDir):
        #shutil.rmtree(path)
        os.mkdir(OutFpDir)

    if not os.path.isdir(Out3dDir):
        #shutil.rmtree(path)
        os.mkdir(Out3dDir)

    with open(outPath + "/" + outlibfilename + ".lib", "a") as f:
        f.write("EESchema-LIBRARY Version 2.3\n")
        parts = dict.get(jsonCfg, "parts")

        for part in parts:
            name = dict.get(part, "partname")
            sym = get_symbol(symbols, name)
            if sym is not None:
                f.write("#\n")
                f.write("# Part: {0}\n".format(sym.getName()))
                f.write("#\n")
                sym.write_definition(f)
                f.write("{0}\n".format("DRAW"))
                sym.write_pins(f)
                sym.write_outline(f)
                f.write("{0}\n".format("ENDDRAW"))
                f.write("{0}\n".format("ENDDEF"))

    with open(outPath + "/" + outlibfilename + ".lib", "r") as f:
        lines = f.readlines()
        lines = [line.rstrip() for line in lines]

        partDefStart = re.compile("^DEF")
        fpLine = re.compile("^F2")

        for line in lines:
            if fpLine.search(line):
                fpName = shlex.split(line, posix=False)[1]

                footprintFileName = fpName + ".kicad_mod"
                footprintFileName = footprintFileName.replace("\"", "")

                InFp = InFpDir + "/" + footprintFileName
                if os.path.isfile(InFp):
                    shutil.copy(InFp, OutFpDir)
            elif partDefStart.search(line):
                pName = shlex.split(line, posix=False)[1]
                name3dMod = pName + ".stp"
                name3dMod = name3dMod.replace("\"", "")

                In3d = In3dDir + "/" + name3dMod

                if os.path.isfile(In3d):
                    shutil.copy(In3d, Out3dDir)





def copy_unmodified_symbols(inpath, inlibfilename, outPath,outlibfilename,jsonCfg):
    libFile = inpath + "/" + inlibfilename + ".lib"

    f = open(libFile, 'r')
    lines = f.readlines()
    lines = [line.rstrip() for line in lines]
    f.close()

    if not os.path.isdir(outPath):
        os.mkdir(outPath)
    with open(outPath + "/" + outlibfilename + ".lib", "w+") as f:
        f.write("EESchema-LIBRARY Version 2.3\n")

        names = []
        partDefStart = re.compile("^DEF")
        partDefStop  = re.compile("^ENDDEF")

        parts = dict.get(jsonCfg,"parts")
        for part in parts:
            names.append(dict.get(part, "partname"))

        sm = smHelper(logger,["init", "copy"])


        for line in lines:
            if partDefStart.search(line):
                if sm.isInState("init"):
                    name = shlex.split(line, posix=False)[1]
                    if name not in names:
                        f.write("{0}\n".format(line))
                        sm.setState( "copy")
                else:
                    logger.error("Not in init state")
            elif partDefStop.search(line):
                if sm.isInState("copy"):
                    f.write("{0}\n".format(line))
                    sm.setState("init")
            else:
                if sm.isInState("copy"):
                    f.write("{0}\n".format(line))




if __name__ == "__main__":
    logger.info("Beautify KiCad Library")

    thisLoc = os.path.dirname(os.path.abspath(__file__))

    libPath = thisLoc + "/Libs/LL"
    libFileName = "SamacSys_Parts"
    InFpDir = libPath + "/" + libFileName + ".pretty"
    In3dDir = libPath + "/" + libFileName + ".3dshapes"

    cfgFile = thisLoc + "/Config/Config.json"
    outPath = thisLoc + "/tmp"
    with open(cfgFile) as config_file:
        jsonCfg = json.load(config_file)


    symbols = extract_symbols_from_lib(libPath, libFileName, jsonCfg)
    process_library(symbols, jsonCfg)
    copy_unmodified_symbols(libPath, libFileName,outPath,"test",jsonCfg)
    write_library(outPath,"test",jsonCfg,InFpDir,In3dDir, symbols)


