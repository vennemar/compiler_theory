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

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "BinOpExpr({})".format(self.Op)
        out += "\n" + level * (7*" ") + "Left > "
        out += self.LHS.toString(level=level+1) if self.LHS else "None"
        out += "\n" + level * (7*" ") + "Right> "
        out += self.RHS.toString(level=level+1) if self.RHS else "None"
        return out

    def codegen(self):
        pass

class VariableExpr(exprNode):
    def __init__(self, name, data_type, array_index=None, has_negative=False):
        self.name = name
        self.type = data_type
        self.array_index = array_index
        self.has_negative = has_negative

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
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

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        return "Literal {}: value={}".format(self.type, self.value)

    def codegen(self):
        pass

class CallExpr(exprNode):
    def __init__(self, name):
        self.name = name
        self.params = []

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "function call (name: {})".format(self.name)
        for expr in self.params:
            out += "\n" + level * (7*" ") + "param> "
            out += expr.toString(level=level+1) if expr else "None"
        return out

    def codegen(self):
        pass

class returnExpr(exprNode):
    def __init__(self, expr):
        self.expr = expr

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "return statement"
        out += "\n" + level * (7*" ") + "expr > "
        out += self.expr.toString(level=level+1) if self.expr else "None"
        return out

class AssignmentNode():
    def __init__(self, destination, expression):
        self.expr = expression
        self.dest = destination

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "assignment"
        out += "\n" + level * (7*" ") + "dest > "
        out += self.dest.toString(level=level+1) if self.dest else "None"
        out += "\n" + level * (7*" ") + "expr > " 
        out += self.expr.toString(level=level+1) if self.expr else "None"
        return out

    def codegen(self):
        pass

class declarationNode():
    def __init__(self, name, data_type, is_global=False, array_size=None):
        self.name = name
        self.type = data_type
        self.is_global = is_global
        self.array_size = array_size # None if var is not an array

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "declaration of {} as {} global={}".format(self.name, self.type, self.is_global)
        if self.array_size != None:
            out += " array_size= {}".format(self.array_size)
        return out

    def codegen(self):
        pass

class IfNode():
    def __init__(self, condition):
        self.condition = condition
        self.thenBlock = []
        self.elseBlock = None

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "IF statement"
        out += "\n" + level * (7*" ") + "cond > " 
        out += self.condition.toString(level=level+1) if self.condition else "None"
        out += "\n" + level * (7*" ") + "then > " 
        for statement in self.thenBlock:
            out += "\n" + (level + 1) * (7*" ") + statement.toString(level=level+1)
        if self.elseBlock != None:
            out += "\n" + level * (7*" ") + "else > "
            for statement in self.elseBlock: # pylint: disable=not-an-iterable
                out += "\n" + (level + 1) * (7*" ") + statement.toString(level=level+1)
        return out

class LoopNode():
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.body = []

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out =  "For Loop"
        out += "\n" + level * (7*" ") + "start> "
        out += self.start.toString(level=level+1) if self.start else "None"
        out += "\n" + level * (7*" ") + "end  > "
        out += self.end.toString(level=level+1) if self.end else "None"
        out += "\n" + level * (7*" ") + "body > "
        for statement in self.body:
            out += "\n" + (level + 1) * (7*" ") + statement.toString(level=level+1)
        return out

class functionNode():
    def __init__(self, name, retType, params):
        self.name = name
        self.retType = retType
        self.params = params
        self.body = []

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        pl = ", ".join(["{} {}".format(p.type, p.name) for p in self.params])
        out = "function {}: ".format(self.name)
        out += "{} ({})\n".format(self.retType, pl)
        out +=  "body >" 
        for statement in self.body:
            out += "\n" + (level+1) * (7*" ") 
            out += statement.toString(level+2) if statement else "None"
        return out

    def codegen(self):
        pass



