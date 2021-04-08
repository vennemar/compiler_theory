## this module builds a parse tree from the token stream

## scanner and token code
from token import tkn_type as tkn
from token import Token
from scanner import Scanner
# ===========================================================================
# define parse tree nodes

class exprNode():
    pass

class BinOpExpr(exprNode):
    def __init__(self, LHS, RHS, Op):
        self.LHS = LHS
        self.RHS = RHS
        self.Op = Op

    def __repr(self, level=0):
        out = "BinOpExpr({})".format(self.Op)
        out += "\n" + level * (6*" ") + "Left >" + self.LHS.__repr__(level=level+1)
        out += "\n" + level * (6*" ") + "Right>" + self.RHS.__repr__(level=level+1)
        return out

    def codegen(self):
        pass

class VariableExpr(exprNode):
    def __init__(self, name, data_type, array_index=None, has_negative=False):
        self.name = name
        self.type = data_type
        self.array_index = array_index
        self.has_negative = has_negative
    
    def __repr__(self, level=0):
        out = "variable ('{}', {}, negative={})".format(self.name, self.type, self.has_negative)
        if self.array_index:
            out += " index={}".format(self.array_index)
        return out

    def codegen(self):
        pass

class LiteralExpr(exprNode):
    def __init__(self, value, data_type):
        self.value = value
        self.type = data_type

    def __repr__(self, level=0):
        return "Literal {}: value={}".format(self.type, self.value)

    def codegen(self):
        pass

class CallExpr(exprNode):
    def __init__(self, name, params=[]):
        self.name = name
        self.params = params
    
    def __repr__(self, level=0):
        out = "function call (name: {})".format(self.name)
        for expr in self.params:
            out += "\n" + level * (6*" ") + "param>" + expr.__repr__(level=level+1)

    def codegen(self):
        pass

class returnExpr(exprNode):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self, level=0):
        out = "return statement"
        out += "\n" + level * (6*" ") + "expr >" + self.expr.__repr__(level=level+1)

class AssignmentNode():
    def __init__(self, destination, expression):
        self.expr = expression
        self.dest = destination

    def __repr__(self, level=0):
        out = "assignment"
        out += "\n" + level * (6*" ") + "dest >" + self.dest.__repr__(level=level+1)
        out += "\n" + level * (6*" ") + "expr >" + self.expr.__repr__(level=level+1)

    def codegen(self):
        pass

class declarationNode():
    def __init__(self, name, data_type, is_global=False, array_size=None):
        self.name = name
        self.type = data_type
        self.is_global = is_global
        self.array_size = array_size # None if var is not an array

    def __repr__(self, level=0):
        return "declaration of {} as {} global={} array={}".format(self.name, self.type, self.is_global, self.array_size)

    def codegen(self):
        pass

class IfNode():
    def __init__(self, condition, thenBlock=[], elseBlock=None):
        self.condition = condition
        self.thenBlock = thenBlock
        self.elseBlock = elseBlock

    def __repr__(self, level=0):
        out = "IF statement"
        out += "\n" + level * (6*" ") + "cond >" + self.condition.__repr__(level=level+1)
        out += "\n" + level * (6*" ") + "then >" 
        for statement in self.thenBlock:
            out += "\n" + (level + 1) * (6*" ") + statement.__repr__(level=level+1)
        if self.elseBlock != None:
            out += "\n" + level * (6*" ") + "else >"
            for statement in self.elseBlock:
                out += "\n" + (level + 1) * (6*" ") + statement.__repr__(level=level+1)
        return out

class LoopNode():
    def __init__(self, start, end, body=[]):
        self.start = start
        self.end = end
        self.body = body

    def __repr__(self, level=0):
        out =  "For Loop"
        out += "\n" + level * (6*" ") + "start>" + self.start.__repr__(level=level+1)
        out += "\n" + level * (6*" ") + "end  >" + self.end.__repr__(level=level+1)
        out += "\n" + level * (6*" ") + "body >"
        for statement in self.body:
            out += "\n" + (level + 1) * (6*" ") + statement.__repr__(level=level+1)

class functionNode():
    def __init__(self, name, retType, params):
        self.name = name
        self.retType = retType
        self.params = params
        self.body = []

    def __repr__(self, level=0):
        pl = ", ".join(["{} {}".format(p[0], p[1]) for p in self.params])
        out = "function: {}\n"
        out +="type: {}({})".format(self.retType, pl)
        for statement in self.body:
            out += statement.__repr__(level+1)
        return out

    def codegen(self):
        pass



