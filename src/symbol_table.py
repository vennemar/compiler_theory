from token import tkn_type as tkn
from llvmlite import ir

class Symbol():
    def __init__(self, name, value, data_type, id_type='variable', unique_name=None):
        self.name = name
        self.value = value
        self.type = data_type
        self.id_type = id_type
        self.unique_name = unique_name

class SymbolTable():
    def __init__(self):
        self.globals = {}
        self.locals = [{}]
        self.namespaces = ['main']
        self.nextUnique = 0 # for generating unique global identifiers

    def update(self, symbol):
        """ returns (result, err) as a tuple, err is None on a success"""
        # check local scope

        i = len(self.locals) -1
        while i >= 0:
            if symbol.name in self.locals[i].keys():
                old = self.locals[i][symbol.name]
                if old.type == symbol.type and old.id_type == symbol.id_type:
                    self.locals[i][symbol.name] = symbol
                    return True 
                else:
                    return False, "variable {} expected a(n) {} of type {}".format(old.name, old.id_type, old.type)
            i -= 1

        # check global scope
        if symbol.name in self.globals.keys():
            old = self.globals[symbol.name]
            if old.type == symbol.type and old.id_type == symbol.id_type:
                return False, "identifier {} was expected as a {} of type {}".format(old.name, old.id_type, old.type)
            self.globals[symbol.name] = symbol
            return True
        else:
            return False


    def add(self, symbol, is_global=False):
        """ add a new symbol to the symbol table if not a duplicate"""
        entry = {symbol.name : symbol}
        if is_global:
            if symbol.name in self.globals.keys():
                return False
            self.globals.update(entry)
        else:
            if symbol.name in self.locals[-1].keys():
                return False
            self.locals[-1].update(entry)
        return True

    def getNameSpace(self):
        """ return the current namespace"""
        return self.namespaces[-1]

    def pushLocal(self, namespace):
        """ adds a local scope and assigned it a name for 
            the purpose of llvm level function signature resolution
        """
        self.locals.append({})
        self.namespaces.append(namespace)

    def popLocal(self):
        self.locals.pop()
        self.namespaces.pop()

    def get(self, name):
        i = len(self.locals) -1
        while i >= 0:
            if name in self.locals[i].keys():
                return self.locals[i][name]
            i -= 1
        if name in  self.globals.keys():
            return self.globals[name]
        else:
            return None

    def get_ir_type(self, tkn_type, is_array=False, length=None):
        type_map = {
            tkn.INT_TYPE    : ir.IntType(32),
            tkn.FLOAT_TYPE  : ir.FloatType(), 
            tkn.BOOL_TYPE   : ir.IntType(1),
            tkn.STRING_TYPE : ir.IntType(8) 
            # a char is an 8 bit int, so strings longet than 1 char must have is_array=True and length set
        }

        if is_array:
            if length <= 0:
                return (None, "array bounds must be greater than 0")
            return ir.ArrayType(self.get_ir_type(tkn_type), length)
        else:
            return type_map[tkn_type]

    def get_unique_name(self):
        """ generate a unique identifier for anonymous global values"""
        name = "main.{}".format(self.nextUnique)
        self.nextUnique += 1
        return name