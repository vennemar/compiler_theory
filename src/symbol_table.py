
class Symbol():
    def __init__(self, name, value, data_type):
        self.name = name
        self.value = value
        self.type = data_type


class SymbolTable():
    def __init__(self):
        self.globals = {}
        self.locals = []

    def update(self, symbol):
        """ returns (result, err) as a tuple, err is None on a success"""
        # check local scope
        if symbol.name in self.locals[-1].keys():
            old = self.locals[-1][symbol.name]
            if old.type == symbol.type:
                return False, "variable {} expected a value of type {}".format(old.name, old.type)
            self.locals[-1][symbol.name] = symbol
        # check global scope
        elif symbol.name in self.globals.keys():
            old = self.globals[symbol.name]
            if old.type == symbol.type:
                return False, "variable {} expected a value of type {}".format(old.name, old.type)
            self.globals[symbol.name] = symbol
        else:
            return False
        return True