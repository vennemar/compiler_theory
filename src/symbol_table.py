
class Symbol():
    def __init__(self, name, value, data_type, id_type='variable'):
        self.name = name
        self.value = value
        self.type = data_type
        self.id_type = id_type


class SymbolTable():
    def __init__(self):
        self.globals = {}
        self.locals = []

    def update(self, symbol):
        """ returns (result, err) as a tuple, err is None on a success"""
        # check local scope
        if symbol.name in self.locals[-1].keys():
            old = self.locals[-1][symbol.name]
            if old.type == symbol.type and old.id_type == symbol.id_type:
                return False, "variable {} expected a value of type {}".format(old.name, old.type)
            self.locals[-1][symbol.name] = symbol
        # check global scope
        elif symbol.name in self.globals.keys():
            old = self.globals[symbol.name]
            if old.type == symbol.type and old.id_type == symbol.id_type:
                return False, "identifier {} was expected as a {} of type {}".format(old.name, old.id_type, old.type)
            self.globals[symbol.name] = symbol
        else:
            return False
        return True

    def pushLocal(self):
        self.locals.append({})

    def popLocal(self):
        self.locals.remove(-1)

    def get(self, name):
        if name in self.locals[-1].keys():
            return self.locals[-1][name]
        elif name in  self.globals.keys():
            return self.globals[name]
        else:
            return None

    def __getattribute__(self, name):
        return self.get(name)

    