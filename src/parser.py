## Parser
from token import tkn_type as tkn
from token import Token
from scanner import Scanner

# Codegen
import llvm
import llvm.core as lc
from symbol_table import * 

# parser will define non-terminals as functions that examine the next token to derive the next terminal function.
# fun is returned so that it can be called when checking the next symbol

## language spec

class Parser():

    def __init__(self, fName):
        self.scanner = Scanner(fName)
        self.token = self.scanner.getToken()
        self._next_token = self.scanner.getToken()
        self.codegen_enabled = True # disable on error but continue to parse for debug

    def reportError(self, message):
        """ prints the given error msg """
        print("Error L{}, C{}: {}".format(self.token.line, self.token.col, message))
        self.codegen_enabled = False

    def next_token(self):
        """ gets the next token in the stream"""
        self.token = self._next_token
        self._next_token = self.scanner.getToken()

    def reportUnexpectedToken(self, expected):
        self.reportError("expected token '{}', found: {}".format(expected, self.token))

    def token_is(tkn_type, consume=False):
        """ check the token type and consume token if consume=True and token is of tkn_type"""
    res = self.token.type == tkn_type
    if consume and res:
        self.next_token()
    return res



    def parse_0_or_more(self, NT_parse_func, closing_terminal):
        """
        parses productions in the form (<Non terminal>)* closing_terminal
        """
        if not isinstance(closing_terminal, list):
            closing_terminal = [closing_terminal]

        while self.token.type not in closing_terminal:
            #check for EOF in loop
            if self.token.type == tkn.EOF:
                #self.reportError("unexpected EOF")
                self.reportUnexpectedToken(expected=closing_terminal)
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
        if self.token_is(tkn.PROGRAM, consume=True):
            self.reportUnexpectedToken(expected='program')
            return False
        
        # <identifier>
        if self.token_is(tkn.ID):
            self.reportError("token: {} is Not a valid Module name".format(self.token.value))
            return False
        codegen.initialize_module(name=self.token.value) 
        self.next_token()

        # IS
        if self.token_is(tkn.IS, consume=True):
            self.reportUnexpectedToken(expected='is')
            return False

        return True

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

        if self.token != tkn.PROGRAM:
            self.reportUnexpectedToken(expected='program')
            return False

        return True

    def parseNT_declaration(self):
        """
        <declaration> -->   [GLOBAL] <procedure_declaration> SEMICOLON
                        |   [GLOBAL] <variable_declaration> SEMICOLON
                        |   [GLOBAL] <type_declaration> SEMICOLON
        """
        # check optional global
        has_global = False
        if self.token_is(tkn.GLOBAL, consume=True):
            # handle optional global token
            has_global = True

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
        if not self.parseNT_procedure_header():
            # not a procedure declaration
            return False
            

        if not self.parseNT_procedure_body():
            self.reportError("expected procedure body")

        return True

    def parseNT_variable_declaration(self):
        """
        <variable_declaration> --> VARIABLE <identifier> COLON <type_mark> [ LEFT_BRACKET <bound> RIGHT_BRACKET ]
        """
        if self.token.type != tkn.VARIABLE:
            # not a variable declaration
            return False

        self.token = self.scanner.getToken()
        if not self.parse_identifier():
            self.reportError("bad identifier: {}".format(self.token))

        if self.token.type != tkn.COLON:
            self.reportUnexpectedToken(expected=':')
        
        return True

    def parseNT_type_declaration(self):
        """
        <type_declaration> --> TYPE <identifier> IS <type_mark>
        """

        if self.token != tkn.TYPE:
            # not a type declaration
            return False
        
        if not self.parse_identifier():
            self.reportError("identifier")

        return True

    def parseNT_procedure_header(self):
        """
        <procedure_header> --> PROCEDURE <identifier> COLON <type_mark> LEFT_PAREN [<parameter_list>] RIGHT_PAREN
        """

        if self.token != tkn.PROCEDURE:
            # not a procedure header
            return False
        self.token = self.scanner.getToken()
    
        if not self.token.type == tkn.ID:
            self.reportError("token '{}' is not a valid procedure name".format(self.token.value))
        procedure_name = token.value
        self.token = self.scanner.getToken()

        if self.token != tkn.COLON:
            self.reportUnexpectedToken(expected=':')
        
        ret_type = self.parseNT_type_mark()
        if not ret_type:
            self.reportError('Expected a type marking, got {}'.format(self.token))

        if self.token != tkn.LEFT_PAREN:
            self.reportUnexpectedToken(expected='(')

        if not self.parseNT_parameter_list():
            self.reportError("bad parameter list")

        if self.token != tkn.RIGHT_PAREN:
            self.reportUnexpectedToken(expected=')')

        return True

    def parseNT_parameter_list(self):
        """
        <parameter_list>  -->   <parameter> COMMA <parameter_list> 
                            |   <parameter>
        """

        if not self.parseNT_parameter():
            return False

        while self.token == tkn.COMMA:
            if not self.parseNT_parameter_list():
                self.reportError("additional parameter expected after token ','")

        return True

    def parseNT_parameter(self):
        """
        <parameter> --> <variable_declaration>
        """
        return parseNT_variable_declaration()

    def parseNT_procedure_body(self):
        """
        <procedure_body> --> (<declaration>)* BEGIN (<statement>)* END PROCEDURE
        """
        
        # parse declarations if they exist
        self.parse_0_or_more(self.parseNT_declaration, tkn.BEGIN)

        self.parse_0_or_more(self.parseNT_statement, tkn.END)

        if self.token != tkn.PROCEDURE:
            self.reportUnexpectedToken(expected='procedure')

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

        if self.token == tkn.INT_TYPE:
            # do stuff
            return True

        if self.token == tkn.FLOAT_TYPE:
            #do stuff
            return True

        if self.token == tkn.STRING_TYPE:
            # do stuff
            return True

        if self.token == tkn.BOOL_TYPE:
            # do stuff
            return True

        if self.token == tkn.ID:
            # lookup in symbol table and return type Identifier
            return True
        
        # Move enum definition to separate function for readability
        if self.parseNT_enum_definition():
            return True
        return False
    
    def parseNT_enum_definition(self):
        """
        ENUM_TYPE LEFT_CURLY <identifier> ( COMMA <identifier> )* RIGHT_CURLY
        """

        if self.token != tkn.ENUM_TYPE:
            # not an enum declaration
            return False

        if self.token != LEFT_CURLY:
            self.reportUnexpectedToken(expected='{')
        self.token = self.scanner.getToken()

        if not self.parse_identifier():
            self.reportError("identifier expected")
        self.token = self.scanner.getToken()

        while self.token == tkn.COMMA:
            if not self.parse_identifier():
                self.reportError("identifier expected")
            self.token = self.scanner.getToken()

        if self.token != tkn.RIGHT_CURLY:
            self.reportUnexpectedToken(expected="}")

        return True

    def parseNT_bound(self):
        """
        for array size specification
        <bound> --> <number>
        """
        
        if self.token.type == tkn.INTEGER:
            return True

        if self.token.type == tkn.FLOAT:
            return True

        if self.parse_identifier():
            return True

        return False

    def parseNT_statement(self):
        """
        NOTE: does a procedure call fit in here?

        <statement>   -->   <assignment_statement> SEMICOLON
                        |   <if_statement> SEMICOLON
                        |   <loop_statement> SEMICOLON
                        |   <return_statement> SEMICOLON
        """
        # add some kind of return to statement on failure?

        if self.parseNT_assignment_statement():
            pass

        elif self.parseNT_if_statement():
            pass

        elif self.parseNT_loop_statement():
            pass

        elif self.parseNT_return_statement():
            pass

        else:
            return False

        if self.token.type != tkn.SEMICOLON:
            self.reportUnexpectedToken(expected=';')
        self.token = self.scanner.getToken()

        return True

    def parseNT_procedure_call(self):
        """
        <procedure_call> --> LEFT_PAREN [<argument_list>] RIGHT_PAREN
        """

        if self.token.type != tkn.LEFT_PAREN:
            return False
        self.token = self.scanner.getToken()

        if not self.parseNT_argument_list():
            self.reportError("bad argument list")

        if self.token.type != tkn.RIGHT_PAREN:
            self.reportUnexpectedToken(expected=')')
        self.token = self.scanner.getToken()

        return True

    def parseNT_assignment_statement(self):
        """
        <assignment_statement> --> <destination> OP_ASSIGN <expression>
        """
        dest = self.parseNT_destination()
        if not dest:
            return False
        
        if self.token.type != tkn.OP_ASSIGN:
            self.reportUnexpectedToken(expected=":=")
        self.token = self.scanner.getToken() 

        expr = self.parseNT_expression():
        if not expr
            return False

        return True

    def parseNT_destination(self):
        """
        <destination> --> <identifier> [LEFT_BRACKET <expression> RIGHT_BRACKET]
        """
        if not self.token.type != tkn.ID:
            return False
        

        self.token = self.scanner.getToken()
        # do identifier stuff

        if self.token.type == tkn.LEFT_BRACKET:
            #process array index
            pass
        self.token = self.scanner.getToken()


        if not self.parseNT_expression():
            self.reportError("invalid expression")
        
        if self.token.type != tkn.RIGHT_BRACKET:
            self.reportUnexpectedToken(expected=']')
        self.token = self.scanner.getToken()


        return True

    def parseNT_if_statement(self):
        """
        <if_statement> --> IF LEFT_PAREN <expression> RIGHT_PAREN THEN (<statement>)* [ ELSE (<statement>)* ] END IF
        """

        if self.token.type != tkn.IF:
            return False
        self.token = self.scanner.getToken()

        if self.token.type != tkn.LEFT_PAREN:
            self.reportUnexpectedToken(expected='(')
        self.token = self.scanner.getToken()


        if not self.parseNT_expression():
            self.reportError("invalid expression")

        if self.token.type != tkn.RIGHT_PAREN:
            self.reportUnexpectedToken(expected=')')
        self.token = self.scanner.getToken()

        if self.token.type != tkn.THEN:
            self.reportUnexpectedToken(expected='then')
        self.token = self.scanner.getToken()

        self.parse_0_or_more(self.parseNT_expression, [tkn.THEN, tkn.END])

        if self.token.type == tkn.THEN:
            self.token = self.scanner.getToken()
        self.parse_0_or_more(self.parseNT_expression, tkn.END)

        if self.token.type != tkn.IF:
            self.reportUnexpectedToken(expected='if')

        return True

    def parseNT_loop_statement(self):
        """
        <loop_statement> --> FOR LEFT_PAREN <assignment_statement> SEMICOLON <expression> RIGHT_PAREN (<statement>)* END FOR
        """

        if self.token.type != tkn.FOR:
            return False
        self.token = self.scanner.getToken()

        if self.token.type != tkn.LEFT_PAREN:
            self.reportUnexpectedToken(expected='(')

        return True

    def parseNT_return_statement(self):
        """
        <return_statement> --> RETURN <expression>
        """

        if self.token.type != tkn.RETURN:
            return False

        if not self.parseNT_expression():
            self.reportError("invalid expression")

        return True

    def parseNT_expression(self):
        """ original 
        <expression>  -->   <expression> BOOL_AND <arithOp>
                        |   <expression> BOOL_OR <arithOp>
                        |   <arithOp>
                        |   [ BOOL_NOT ] <arithOp>

        re-written to avoid infinate recursive calls

        <expression>  -->   <arithOp> BOOL_AND <expression>
                        |   <arithOp> BOOL_OR <expression>
                        |   <arithOp>
                        |   [ BOOL_NOT ] <arithOp>
        
        """

        has_bool_not = False
        if self.token.type == tkn.BOOL_NOT:
            has_bool_not = True
            self.token = self.scanner.getToken()

        if not self.parseNT_arithOp():
            if has_bool_not:
                self.reportError("expected an expression following token 'not'")
            else:
                return False

        if self.token.type == tkn.BOOL_AND:
            self.token = self.scanner.getToken()
            if not self.parseNT_expression():
                self.reportError("expected expression after token '&' ")
        elif self.token.type == tkn.BOOL_OR:
            self.token = self.scanner.getToken()
            if not self.parseNT_expression():
                self.reportError("expected expression after token '|' ")
        
        return True

    def parseNT_arithOp(self):
        """
        <arithOp> -->   <relation> OP_ADD <arithOp>
                    |   <relation> OP_SUB <arithOp>
                    |   <relation>
        """

        if not self.parseNT_relation():
            return False

        if self.token.type == tkn.OP_ADD:
            self.token = self.scanner.getToken()
            if not self.parseNT_arithOp():
                self.reportError("invalid operand after token '+'")
        elif self.token.type == tkn.OP_SUB:
            self.token = self.scanner.getToken()
            if not self.parseNT_arithOp():
                self.reportError("invalid operand after token '-'")

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
        # Get Left hand side of the relation
        LHS = self.parseNT_term()
        if not LHS:
            return None


        if self.token.type == tkn.OP_LT:
            self.token = self.scanner.getToken()
            RHS = self.parseNT_relation():
            if not RHS:
                self.reportError("invalid operand after token '<'")
                return None
            return builder.fcmp('<', LHS, RHS, name='booltmp')


        elif self.token.type == tkn.OP_GE:
            self.token = self.scanner.getToken()

            if not self.parseNT_relation():
                self.reportError("invalid operand after token '>='")
        elif self.token.type == tkn.OP_LE:
            self.token = self.scanner.getToken()
            if not self.parseNT_relation():
                self.reportError("invalid operand after token '<='")
        elif self.token.type == tkn.OP_GT:
            self.token = self.scanner.getToken()
            if not self.parseNT_relation():
                self.reportError("invalid operand after token '>'")
        elif self.token.type == tkn.OP_EQ:
            self.token = self.scanner.getToken()
            if not self.parseNT_relation():
                self.reportError("invalid operand after token '=='")
        elif self.token.type == tkn.OP_NE:
            self.token = self.scanner.getToken()
            if not self.parseNT_relation():
                self.reportError("invalid operand after token '!='")

        return None
    
    def parseNT_term(self):
        """
        <term> -->  <term> OP_MUL <factor>
                 |  <term> OP_DIV <factor>
                 |  <factor>
        """
        if not self.parseNT_factor():
            return False

        if self.token.type == tkn.OP_MUL:
            self.token = self.scanner.getToken()
            if not self.parseNT_factor():
                self.reportError("invalid operand after token '*'")
        if self.token.type == tkn.OP_DIV:
            self.token = self.scanner.getToken()
            if not self.parseNT_factor():
                self.reportError("invalid operand after token '/'")

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

        #check for name or number with optional minus
        has_minus = False
        if self.token.type == tkn.OP_SUB:
            has_minus = True
            self.token = self.scanner.getToken()

        if self.parseNT_name():
            # do stuff
            return True
        elif self.token.type == tkn.INTEGER:
            # do stuff
            return True
        elif self.token.type == tkn.FLOAT:
            # do stuff
            return True
        elif has_minus:
            self.reportError("expected a name or number following token '-'")

        # check for parenthetical expression
        if self.token.type == tkn.LEFT_PAREN:
            self.token = self.scanner.getToken()
            if not self.parseNT_expression():
                self.reportError("expected expression after token '('")

            if self.token.type != tkn.RIGHT_PAREN:
                self.reportUnexpectedToken(expected=')')
            self.token = self.scanner.getToken()

        # check for procedure call
        elif self.parseNT_procedure_call()
        return True

    def parseNT_name(self, with_identifier=True):
        """
        <name> ::= <identifier> [ LEFT_BRACKET <expression> RIGHT_BRACKET ]
        """
        if with_identifier:
            if not self.parse_identifier():
                return False


        if self.token.type == tkn.LEFT_BRACKET:
            self.token = self.scanner.getToken()

            if not self.parseNT_expression():
                self.reportError("invalid expression after token '[")

            if self.token.type != tkn.RIGHT_BRACKET:
                self.reportUnexpectedToken(expected=']')
        elif not with_identifier:
            return False

        return True


    def parseNT_argument_list(self):
        """
        <argument_list>   -->   <expression> COMMA <argument_list>
                            |   <expression>
        """
            if not self.parseNT_expression():
                self.reportError("invalid expression")

        while self.token.type == tkn.COMMA:
            self.token = self.scanner.getToken()
            if not self.parseNT_expression():
                self.reportError("invalid expression")

        return True

    def parseNT_name_or_procedure():
        """
        <identifier> [ LEFT_BRACKET <expression> RIGHT_BRACKET ]
        <identifier> LEFT_PAREN [<argument_list>] RIGHT_PAREN

        """

        if not self.parse_identifier()
            return False

        if self.parseNT_procedure_call():
            return True

        if self.parseNT_name(with_identifier=False):
            return True


    def parse_identifier(self):
        if self.token.type != tkn.ID:
            return False

        self.last_id = self.token.value
        self.symbol_table.add_id(self.token.value)
        self.token = self.scanner.getToken()
        return True