## Scanner
from token import Token
from token import tkn_type as tkn
#===================================================================================
# Terminal symbols


class Scanner:
    """ scans the file contents and returns tokens or errors"""
    # Setup and Teardown
    def __init__(self, fName, tabsize=4):
        self.fName = fName
        self.fd = open(fName, "r")
        
        self.line = 1
        self.col = 0
        self._next_char = self.fd.read(1)
        self.tabsize = tabsize

    def __del__(self):
        self.fd.close()

    # Character Stream Implementation

    def getNextChar(self):
        """
        return the next char in the stream. the text is buffered one char ahead
        to allow convenient peeking of the next char. this peek means that there
        shouldn't be a need for the tokenizer to track any kind of line or column
        info. It's all handled automatically here and is available when an error
        or warning is found
        """

        this_char = self._next_char
        
        if this_char == '\n':
            self.line += 1
            self.col = 0
        elif this_char == '\t':
            self.col += self.tabsize
        else:
            self.col += 1
        
        self._next_char = self.fd.read(1)

        return this_char


    def peekNextChar(self):
        return self._next_char

    # Error reporting 

    def reportError(self, message):
        print("Error L{} C{}: {}".format(self.line, self.col, message))

    def reportWarning(self, message):
        print("Warning L{} C{}: {}".format(self.line, self.col, message))

    # Tokenizer

    def getToken(self):
        """
        Gets the next token from the code. Comments and whitespace are discarded.
        """
        c = self.getNextChar()

        # check for EOF
        if c == None:
            return Token(tkn.EOF, location=(self.line, self.col))        

        # Trim leading whitespace characters
        while c.isspace():
            c = self.getNextChar()

        # Comments (not recorded as tokens)
        if c == '/':
            print("Comment found!")
            ## Single Line Comments
            if self.peekNextChar() == "/":
                print("single line!")
                while c != '\n':
                    c = self.getNextChar()
                print("found new line")
            ## Multi Line Comments
            elif self.peekNextChar() == "*":
                print("Multi line!")
                self.getNextChar()
                openCount = 1
                closedCount = 0
                ### must handle nested multiline comments
                while openCount != closedCount:
                    c = self.getNextChar()
                    if c == "/" and self.peekNextChar() == "*":
                        openCount += 1
                        self.getNextChar()
                    elif c == "*" and self.peekNextChar() == "/":
                        closedCount += 1
                        self.getNextChar()
            c = self.getNextChar()

            ### Trim whitespace after comments
            while c.isspace():
                c = self.getNextChar()

        ## Now any further parsing will generate a token
        token_start = (self.line, self.col)

        # Strings
        if c == '"':
            value = c # gets first quote
            while not (self.peekNextChar() == '"' and c !="\\"):
                c = self.getNextChar()
                value += c
            value += self.getNextChar() # gets last quote
            return Token(tkn.STRING, token_start, value)
        
        # Symbols

        two_char_operators = {
            
            '>=' : tkn.OP_GE,
            '<=' : tkn.OP_LE,
            '==' : tkn.OP_EQ,
            '!=' : tkn.OP_NE,
            ':=' : tkn.OP_ASSIGN
        }
        if c == '>' or c == '<' or c == '=' or c == '!' or c == ':':
            if c + self.peekNextChar() in two_char_operators.keys():
                op = c + self.getNextChar()
                return Token(two_char_operators[op], token_start)

        single_char_tokens = {
            '[' : tkn.LEFT_BRACKET,
            ']' : tkn.RIGHT_BRACKET,
            '(' : tkn.LEFT_PAREN,
            ')' : tkn.RIGHT_PAREN,
            '{' : tkn.LEFT_CURLY,
            '}' : tkn.RIGHT_CURLY, 
            ';' : tkn.SEMICOLON,
            ':' : tkn.COLON,
            '.' : tkn.PERIOD,
            ',' : tkn.COMMA,
            '&' : tkn.BOOL_AND,
            '|' : tkn.BOOL_OR,
            '+' : tkn.OP_ADD,
            '-' : tkn.OP_SUB,
            '*' : tkn.OP_MUL,
            '/' : tkn.OP_DIV,
            '>' : tkn.OP_GT,
            '<' : tkn.OP_LT,
        }

        if c in single_char_tokens.keys():
            return Token(single_char_tokens[c], token_start)

        # Numbers
        ## the language spec says floats must start with a digit 0-9
        ## so a leading decimal is not handled
        if c.isdigit():
            value = ""
            while self.peekNextChar().isdigit():
                value += self.getNextChar()

            ## number is floating point
            if self.peekNextChar() == '.':
                value += c
                while self.peekNextChar().isdigit():
                    value += self.getNextChar()
                return Token(tkn.FLOAT, token_start, value)
            ## number is an Integer
            else:
                return Token(tkn.INTEGER, token_start, value)
        
        # identifiers/reserved words

        ## identifiers must start with [A-Z | a-z]
        if c.isalpha():
            value = c
            while self.peekNextChar().isalnum() or self.peekNextChar() == '_':
                value += self.getNextChar()

            ## Check for reserved words
            reserved_words = {
                'program'   : tkn.PROGRAM,
                'procedure' : tkn.PROCEDURE,
                'is'        : tkn.IS,
                'begin'     : tkn.BEGIN,
                'end'       : tkn.END,
                'global'    : tkn.GLOBAL,
                'type'      : tkn.TYPE,
                'integer'   : tkn.INT_TYPE,
                'float'     : tkn.FLOAT_TYPE,
                'string'    : tkn.STRING_TYPE,
                'bool'      : tkn.BOOL_TYPE,
                'enum'      : tkn.ENUM_TYPE,
                'not'       : tkn.BOOL_NOT,
                'if'        : tkn.IF,
                'then'      : tkn.THEN,
                'else'      : tkn.ELSE,
                'for'       : tkn.FOR,
                'while'     : tkn.WHILE,
                'return'    : tkn.RETURN,
                'true'      : tkn.TRUE,
                'false'     : tkn.FALSE,
                'variable'  : tkn.VARIABLE
            }

            ## token is a reserved word
            if value in reserved_words.keys():
                return Token(reserved_words[value], token_start)
            
            ## token is an Identifier
            else:
                return Token(tkn.ID, token_start, value)

            # Unknown Token... no patterns match
            return Token(tkn.UNKNOWN, token_start)

def main():
    """ for debugging the scanner """

    #fName = "../test/testPgms/correct/iterativeFib.src"
    fName = "../test/testPgms/correct/logicals.src"
    scanner = Scanner(fName)
    token = scanner.getToken()
    print(token)
    while token.type != tkn.EOF:
        token = scanner.getToken()
        print(token)

if __name__ == '__main__':
    main()