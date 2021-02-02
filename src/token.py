# Defines the enumeration of valid token types and the Token data structure

from enum import unique, Enum, auto

@unique
class t_type(Enum):
    # creates an enumeration of valid token types
    # auto will assign a unique number starting at 1 and incrementing
    # single char operators are assigned their ascii char to enable 
    # easy token type assignment my the scanner

    # Program control flow
    PROGRAM = auto()
    BEGIN = auto()
    IS = auto()
    END = auto()
    GLOBAL = auto()
    PROCEDURE = auto()
    VARIABLE = auto()
    TYPE = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    RETURN = auto()

    # Type Identifiers
    INT_TYPE = auto()
    STRING_TYPE = auto()
    FLOAT_TYPE = auto()
    BOOL_TYPE = auto()
    ENUM_TYPE = auto()

    # Operators
    BOOL_AND =  auto()
    BOOL_OR =  auto()
    BOOL_NOT = auto()
    OP_ADD = auto()
    OP_SUB = auto()
    OP_MUL = auto()
    OP_DIV = auto()
    OP_ASSIGN = auto()
    ## Relation Operators
    OP_EQ = auto()
    OP_NE = auto()
    OP_LT = auto()
    OP_LE = auto()
    OP_GT = auto()
    OP_GE = auto()

    # Literals
    STRING = auto()
    INTEGER = auto()
    FLOAT = auto()
    TRUE = auto()
    FALSE = auto()

    # Other stuff
    ID = auto()
    LEFT_BRACKET =  auto()
    RIGHT_BRACKET =  auto()
    LEFT_PAREN =  auto()
    RIGHT_PAREN =  auto()
    LEFT_CURLY =  auto()
    RIGHT_CURLY =  auto()
    SEMICOLON =  auto()
    COLON = auto()
    PERIOD =  auto()
    COMMA =  auto()
    UNKNOWN = auto()
    EOF = auto()

class Token:
    def __init__(self, t_type, location, val=None):
        self.type = t_type
        self.val = val
        self.line = location[0]
        self.col = location[1]

    def __str__(self):
        return "<token {} L{} C{} val={}>".format(self.type, self.line, self.col, self.val)