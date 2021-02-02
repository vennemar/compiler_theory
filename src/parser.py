## Parser
from token import t_type as tkn
from token import Token
from scanner import Scanner

# parser will define non-terminals as functions that examine the next token to derive the next terminal function.
# fun is returned so that it can be called when checking the next symbol

## language spec

class Parser():

    def __init__(self, fName):
        self.scanner = Scanner(fName)
        self.token = self.scanner.getToken()

    def reportError(self, message):
        self.scanner.reportError(message)

    def parse_0_or_more(self, NT_parse_func, closing_terminal):
        """
        parses productions in the form (<Non terminal>)* closing_terminal
        """
        while self.token.type != closing_terminal:
            #check for EOF in loop
            if self.token.type == tkn.EOF:
                self.reportError("unexpected EOF")
                return False 

            NT_parse_func() # call parse function for expected Non terminal
            self.token = self.scanner.getToken()

        return True

    # ================================================= #
    # Non Terminal derivation functions                 #
    # ================================================= #
    # Terminals are represented by the tokens
    # defined in token.py
    #
    # Non-terminals are represented by functions that
    # define production rules for that non terminal.
    #
    # production rules are included in comments using 
    # <name> to denote a non-terminal and the token name 
    # in all caps to denote a terminal.

    def parseNT_program(self):
        """
        <program> --> <program_header> <program_body> PERIOD
        """
        self.parseNT_program_header()
        self.parseNT_program_body()

        if self.token.type == tkn.PERIOD:
            self.token = self.scanner.getToken()
            if self.token.type == tkn.EOF:
                return True # or return None as EOF denotation? we could also use the EOF from the scanner
            else:
                self.reportError("tokens detected after program terminating symbol '.'")


    def parseNT_program_header(self):
        """
        <program_header> --> PROGRAM <identifier> IS
        """
        # PROGRAM
        if self.token.type == tkn.PROGRAM:
            return True
        else:
            self.reportError("expected token 'program', found: {}".format(self.token))
            return False
        # <identifier>
        # self.parse_identifier()
        # IS
        if self.token.type == tkn.IS:
            return True
        else:
            self.reportError("expected token 'is', found: {}".format(self.token))
            return False

    def parseNT_program_body(self):
        """
        <program_body>  --> (<declaration>)* BEGIN (<statement>)* END PROGRAM
        """
        # declerations followed by begin
        self.parse_0_or_more(self.parseNT_declaration, tkn.BEGIN)
        self.token = self.scanner.getToken()

        # statements followed by end program
        self.parse_0_or_more(self.parseNT_statement(), tkn.END)
        self.token = self.scanner.getToken()

        if self.token == tkn.PROGRAM:
            return True
        else:
            self.reportError("expected token 'program', found: {}".format(self.token))
            return False

    def parseNT_declaration(self):
        """
        <declaration> -->   [GLOBAL] <procedure_declaration> SEMICOLON
                        |   [GLOBAL] <variable_declaration> SEMICOLON
                        |   [GLOBAL] <type_declaration> SEMICOLON
        """
        # check optional global
        if self.token.type == tkn.GLOBAL:
            # add parsing here
            self.token = self.scanner.getToken()

        # check for non-terminal options
        if self.parseNT_procedure_delcaration():
            pass
           
        elif self.parseNT_variable_declaration():
            pass

        elif self.parseNT_type_declaration():
            pass

        else:
            # maybe report error? maybe wait for a more specific one later on?
            return False
        
        self.token = self.scanner.getToken()
        if self.token.type == tkn.SEMICOLON:
            return True
        else:
            self.reportError("expected token ';', found {}".format(self.token))

    def parseNT_procedure_delcaration(self):
        """
        <procedure_declaration> --> <procedure_header> <procedure_body>
        """
        return True

    def parseNT_variable_declaration(self):
        """
        <variable_declaration> --> VARIABLE <identifier> COLON <type_mark> [ LEFT_BRACKET <bound> RIGHT_BRACKET ]
        """
        return True

    def parseNT_type_declaration(self):
        """
        <type_declaration> --> TYPE <identifier> IS <type_mark>
        """
        return True

    def parseNT_procedure_header(self):
        """
        <procedure_header> --> PROCEDURE <identifier> COLON <type_mark> LEFT_PAREN [<parameter_list>] RIGHT_PAREN
        """
        return True

    def parseNT_parameter_list(self):
        """
        <parameter_list>  -->   <parameter> COMMA <parameter_list> 
                            |   <parameter>
        """
        return True

    def parseNT_parameter(self):
        """
        <parameter> --> <variable_declaration>
        """
        return True

    def parseNT_procedure_body(self):
        """
        <procedure_body> --> (<declaration>)* BEGIN (<statement>)* END PROCEDURE
        """
        return True

    def parseNT_type_mark(self):
        """
        <type_mark>   -->   INT_TYPE 
                        |   FLOAT_TYPE
                        |   STRING_TYPE
                        |   BOOL_TYPE
                        |   <identifier>
                        |   ENUM_TYPE LEFT_CURLY <identifier> ( COMMA <identifier> )* RIGHT_CURLY
        """
        return True
    
    def parseNT_bound(self):
        """
        <bound> --> <number>
        """
        return True

    def parseNT_statement(self):
        """
        NOTE: does a procedure call fit in here?

        <statement>   -->   <assignment_statement> SEMICOLON
                        |   <if_statement> SEMICOLON
                        |   <loop_statement> SEMICOLON
                        |   <return_statement> SEMICOLON
        """
        return True

    def parseNT_procedure_call(self):
        """
        <procedure_call> --> <identifier> LEFT_PAREN [<argument_list>] RIGHT_PAREN
        """
        return True

    def parseNT_assignment_statement(self):
        """
        <assignment_statement> --> <destination> OP_ASSIGN <expression>
        """
        return True

    def parseNT_destination(self):
        """
        <destination> --> <identifier> [LEFT_BRACKET <expression> RIGHT_BRACKET]
        """
        return True

    def parseNT_if_statement(self):
        """
        <if_statement> --> IF LEFT_PAREN <expression> RIGHT_PAREN THEN (<statement>)* [ ELSE (<statement>)* ] END IF
        """
    
    def parseNT_loop_statement(self):
        """
        <loop_statement> --> FOR LEFT_PAREN <assignment_statement> SEMICOLON <expression> RIGHT_PAREN (<statement>)* END FOR
        """
        return True

    def parseNT_return_statement(self):
        """
        <return_statement> --> RETURN <expression>
        """
        return True

    def parseNT_expression(self):
        """
        <expression>  -->   <expression> OP_AND <arithOp>
                        |   <expression>
                        |   <arithOp>
                        |   [ NOT ] <arithOp>
        """
        return True

    def parseNT_arithOp(self):
        """
        <arithOp> -->   <arithOp> OP_ADD <relation>
                    |   <arithOp> OP_SUB <relation>
                    |   <relation>
        """
        return True

    def parseNT_relation(self):
        """
        <relation> -->  <relation> OP_LT <term>
                     |  <relation> OP_GE <term>
                     |  <relation> OP_LE <term>
                     |  <relation> OP_GT <term>
                     |  <relation> OP_EQ <term>
                     |  <relation> OP_NE <term>
                     |  <term>
        """
        return True
    
    def parseNT_term(self):
        """
        <term> -->  <term> OP_MUL <factor>
                 |  <term> OP_DIV <factor>
                 |  <factor>
        """
        return True

    def parseNT_factor(self):
        """
        <factor>  -->   LEFT_PAREN <expression> RIGHT_PAREN
                    |   <procedure_call>
                    |   [ OP_MINUS ] <name> 
                    |   [ OP_MINUS ] <number> 
                    |   STRING
                    |   TRUE
                    |   FALSE
        """
        return True

    def parseNT_name(self):
        """
        <name> ::= <identifier> [ LEFT_BRACKET <expression> RIGHT_BRACKET ]
        """
        return True

    def parseNT_argument_list(self):
        """
        <argument_list>   -->   <expression> COMMA <argument_list>
                            |   <expression>
        """
        return True