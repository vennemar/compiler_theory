from token import tkn_type as tkn
from token import Token
from scanner import Scanner
from parse_tree import * # pylint: disable=unused-wildcard-import
# ================================================================================
#  Parser Module
# ================================================================================
# builds the parse tree data structure from the token stream
class Parser():
    def __init__(self, fName):
        self.scanner = Scanner(fName)
        self.token = self.scanner.getToken()
        self._next_token = self.scanner.getToken()
        self._has_errors = False 

    def reportError(self, message):
        print("Error L{}, C{}: {}".format(self.token.line, self.token.col, message))

    def reportUnexpectedToken(self, expected):
        self.reportError("expected token '{}', found: {}".format(expected, self.token))

    def next_token(self):
        self.token = self._next_token
        self._next_token = self.scanner.getToken()
    
    def token_is(self, tkn_type, consume=False):
        res = self.token.type == tkn_type
        if consume and res:
            self.next_token()
        return res

    def choose_NT(self, NT_list):
        for func in NT_list:
            res, err = func()
            if err:
                return res, err
            elif res != None:
                return res, False
        self.reportError("illegal syntax") # maybe this error could be made more helpful
        return None, True

    def recover_on_error(self, err):
        if err:
            # Error recovery (look for the next semicolon)
            while not self.token_is(tkn.EOF):
                if self.token_is(tkn.SEMICOLON, consume=True):
                    break
                self.next_token()
        else:
            # check for semicolon at end of statement
            if not self.token_is(tkn.SEMICOLON, consume=True):
                self.reportUnexpectedToken(expected=';')
                self.recover_on_error(True)

    #==========================================================================
    #  parser interface functions
    #==========================================================================

    def parse_top_level_declaration(self):
        # check for end of top level declerations
        if self.token_is(tkn.BEGIN, consume=True):
            return tkn.BEGIN
        elif self.token_is(tkn.EOF):
            return tkn.EOF

        res, ___ = self._parseNT_declaration()
        return res

    def parse_top_level_statement(self):

        # check for end of program and/or file
        if self.token_is(tkn.END, consume=True):
            if self.token_is(tkn.PROGRAM, consume=True):
                if self.token_is(tkn.PERIOD, consume=True):
                    if self.token_is(tkn.EOF):
                        return tkn.EOF # signal end of program
                    else:
                        self.reportError("tokens detected after program terminating symbol '.'")
                        return tkn.EOF # signal end of program (but with errors logged)
                else:
                    self.reportError("expected token '.' after end of program")
                    return tkn.EOF
            else:
                self.reportUnexpectedToken(expected='program')
                return tkn.EOF
        elif self.token_is(tkn.EOF):
            self.reportError("unexpected EOF")
            return tkn.EOF
        else:
            # parse statement
            res, ___ = self._parseNT_statement()
            return res


    def parse_program_header(self):
        """
        <program_header> --> PROGRAM <identifier> IS
        """

        # PROGRAM
        if not self.token_is(tkn.PROGRAM, consume=True):
            self.reportUnexpectedToken(expected='program')
            return None
        
        # <identifier>
        if not self.token_is(tkn.ID):
            self.reportError("token: {} is Not a valid Module name".format(self.token.value))
            return None

        program_name = self.token.value
        self.next_token()

        # IS
        if not self.token_is(tkn.IS, consume=True):
            self.reportUnexpectedToken(expected='is')
            return None

        return program_name

    #==========================================================================
    #  AST builder functions
    #==========================================================================
    # definitions

    def _parseNT_declaration(self):
        """
        <declaration> -->   [GLOBAL] <procedure_declaration> SEMICOLON
                        |   [GLOBAL] <variable_declaration> SEMICOLON
        """

        # handle optional global token
        has_global = False
        if self.token_is(tkn.GLOBAL, consume=True):
            has_global = True

        # check for type of declaration
        NT_list = [
            self._parseNT_procedure_declaration,
            self._parseNT_variable_declaration,
        ]
        res, err = self.choose_NT(NT_list)
        self.recover_on_error(err)
        if res != None:
            res.is_global = has_global
        return res, err


    def _parseNT_procedure_declaration(self):
        """
        <procedure_declaration> --> <procedure_header> <procedure_body>
        <procedure_header> --> PROCEDURE <identifier> COLON <type_mark> LEFT_PAREN [<parameter_list>] RIGHT_PAREN
        """

        ## Procedure Header

        if not self.token_is(tkn.PROCEDURE, consume=True):
            return None, False # not a procedure declaration
    
        # Parse Name
        if not self.token_is(tkn.ID):
            self.reportError("token '{}' is not a valid procedure name".format(self.token.value))
        procedure_name = self.token.value
        line = self.token.line
        self.next_token()

        if not self.token_is(tkn.COLON, consume=True):
            self.reportUnexpectedToken(expected=':')
            return None, True

        # Parse Type
        ret_type = self._parseNT_type_mark()
        if ret_type == None:
            return None, True

        if not self.token_is(tkn.LEFT_PAREN, consume=True):
            self.reportUnexpectedToken(expected='(')
            return None, True

        # Parse Parameters
        params = []
        err = False
        if not self.token_is(tkn.RIGHT_PAREN, consume=True):
            param, err = self._parseNT_variable_declaration()
            params.append(param)    
            while self.token_is(tkn.COMMA, consume=True):
                param, err = self._parseNT_variable_declaration()
                params.append(param)
                if err:
                    break

            if not self.token_is(tkn.RIGHT_PAREN, consume=True):
                self.reportUnexpectedToken(expected=')')
                return None, True

        func = functionNode(procedure_name, ret_type, params, line=line)        

        ## Procedure Body

        # declarations
        while not self.token_is(tkn.BEGIN, consume=True):
            if self.token_is(tkn.EOF):
                self.reportError("unexpected EOF")
                return func, True
            elif self.token_is(tkn.END):
                self.reportError("unexpected 'end' token")
                return func, True
            
            res, err = self._parseNT_declaration()
            func.body.append(res) # append result to function body

        # statements
        while not self.token_is(tkn.END, consume=True):
            if self.token_is(tkn.EOF):
                self.reportError("unexpected EOF")
                return func, True

            res, err = self._parseNT_statement()
            func.body.append(res)

        if not self.token_is(tkn.PROCEDURE, consume=True):
            self.reportUnexpectedToken(expected='procedure')
        
        return func, False

    def _parseNT_variable_declaration(self):
        """
        <variable_declaration> --> VARIABLE <identifier> COLON <type_mark> [ LEFT_BRACKET <bound> RIGHT_BRACKET ]
        """
        if not self.token_is(tkn.VARIABLE, consume=True):
            return None, False

        # Parse Name
        if not self.token_is(tkn.ID):
            self.reportError("Expected a valid identifier after token 'variable'")
            return None, True
        
        name = self.token.value
        line = self.token.line
        self.next_token()

        if not self.token_is(tkn.COLON, consume=True):
            self.reportUnexpectedToken(expected=':')
            return None, True

        # Parse Data Type
        data_type = self._parseNT_type_mark()
        if data_type == None:
            return None, True

        bound, err = self._parseNT_array_index()
        if err:
            return None, True
        elif bound != None:  
            # var is an array
            return declarationNode(name, data_type, line=line, array_size=bound), False
        else:
            # var is not an array
            return declarationNode(name, data_type, line=line), False

    def _parseNT_array_index(self, literal_only=True):
        if not self.token_is(tkn.LEFT_BRACKET, consume=True):
            # not an array
            return None, False
        else:   
            # handle array bounds            
            if literal_only:
                bound, err = self._parse_literal()
            else:
                bound, err = self._parseNT_expression()
            
            if bound != None:
                if self.token_is(tkn.RIGHT_BRACKET, consume=True):
                    return bound, err
                else:
                    self.reportUnexpectedToken(expected=']')
                    return None, True
            else:
                self.reportError("Array bounds must be given by a valid literal")
                return None, True

    def _parseNT_type_mark(self):
        """ gets valid type marking """
        type_list = [
            tkn.INT_TYPE,
            tkn.STRING_TYPE,
            tkn.FLOAT_TYPE,
            tkn.BOOL_TYPE,
            ]

        if not self.token.type in type_list:
            self.reportError("{} is not a valid data type".format(self.token))
            return None       

        res = self.token.type
        self.next_token()
        return res

    #==========================================================================
    # statements

    def _parseNT_statement(self):
        """
        <statement>   -->   <assignment_statement> SEMICOLON
                        |   <if_statement> SEMICOLON
                        |   <loop_statement> SEMICOLON
                        |   <return_statement> SEMICOLON
        """
        NT_list = [
            self._parseNT_assignment,
            self._parseNT_if,
            self._parseNT_loop,
            self._parseNT_return
        ]
        res, err = self.choose_NT(NT_list)
        self.recover_on_error(err)
        return res, err

    def _parseNT_assignment(self):
        """
        <assignment_statement> --> <destination> OP_ASSIGN <expression>
        """
        dest, err1 = self._parseNT_destination()
        if dest == None:
            return dest, err1

        line = self.token.line
        if not self.token_is(tkn.OP_ASSIGN, consume=True):
            self.reportUnexpectedToken(expected=':=')
            return None, True
        
        expr, err2 = self._parseNT_expression()

        return AssignmentNode(dest, expr, line), (err1 or err2)

    def _parseNT_destination(self):
        """
        <destination> --> <identifier> [LEFT_BRACKET <expression> RIGHT_BRACKET]
        """
        if not self.token_is(tkn.ID):
            # not an assignment statement
            return None, False
        
        name = self.token.value
        line = self.token.line
        self.next_token()

        # check for array index
        index, err = self._parseNT_array_index(literal_only=False)
        if err:
            return None, True
        elif index != None:
            # var is an array
            return VariableExpr(name=name, data_type=None, array_index=index, line=line), False
        else:
            # var is not an array
            return VariableExpr(name=name, data_type=None, line=line), False
    
    def _parseNT_if(self):
        """
        <if_statement> --> IF LEFT_PAREN <expression> RIGHT_PAREN THEN (<statement>)* [ ELSE (<statement>)* ] END IF
        """
        if not self.token_is(tkn.IF, consume=True):
            return None, False
        
        line = self.token.line
        if not self.token_is(tkn.LEFT_PAREN, consume=True):
            self.reportUnexpectedToken(expected='(')
            return None, True

        condition, err = self._parseNT_expression()
        if condition == None:
            self.reportError("invalid expression")
            return None, True

        if not self.token_is(tkn.RIGHT_PAREN, consume=True):
            self.reportUnexpectedToken(expected=')')
            return None, True

        if not self.token_is(tkn.THEN, consume=True):
            self.reportUnexpectedToken(expected='then')
            return None, True

        if_node = IfNode(condition, line)

        # parse then block
        while not self.token_is(tkn.ELSE, consume=True):
            if self.token_is(tkn.EOF):
                self.reportError("unexpected EOF")
                return if_node, True
            elif self.token_is(tkn.END, consume=True):
                # No else block, check for if token and return
                if not self.token_is(tkn.IF, consume=True):
                    self.reportUnexpectedToken(expected='if')
                    return if_node, True
                else:
                    return if_node, err

            else:
                res, err1 = self._parseNT_statement()
                err = err or err1
                if_node.thenBlock.append(res)

        # parse else block
        if_node.elseBlock = []
        while not self.token_is(tkn.END, consume=True):
            if self.token_is(tkn.EOF):
                self.reportError("unexpected EOF")
                return if_node, True
            
            res, err1 = self._parseNT_statement()
            err = err or err1
            if_node.elseBlock.append(res)

        if not self.token_is(tkn.IF, consume=True):
            self.reportUnexpectedToken(expected='if')
            return if_node, True
        else:
            return if_node, err

    def _parseNT_loop(self):
        """
        <loop_statement> --> FOR LEFT_PAREN <assignment_statement> SEMICOLON <expression> RIGHT_PAREN (<statement>)* END FOR
        """
        if not self.token_is(tkn.FOR, consume=True):
            return None, False
        
        if not self.token_is(tkn.LEFT_PAREN, consume=True):
            self.reportUnexpectedToken(expected='(')
            return None, True

        line = self.token.line
        start, err = self._parseNT_assignment()
        self.recover_on_error(err)
        
        end, err1 = self._parseNT_expression()
        if not self.token_is(tkn.RIGHT_PAREN, consume=True):
            self.reportUnexpectedToken(expected=')')
            return None, True

        loop = LoopNode(start, end, line=line)
        err = err or err1
        
        while not self.token_is(tkn.END, consume=True):
            if self.token_is(tkn.EOF):
                self.reportError("unexpected EOF")
                return loop, True
            
            res, err1 = self._parseNT_statement()
            err = err or err1
            loop.body.append(res)

        if not self.token_is(tkn.FOR, consume=True):
            self.reportUnexpectedToken(expected='for')

        return loop, err

    def _parseNT_return(self):
        """
        <return_statement> --> RETURN <expression>
        """
        if not self.token_is(tkn.RETURN, consume=True):
            return None, False
        
        line = self.token.line
        expr, err = self._parseNT_expression()
        if err:
            return None, True
        else:
            return returnExpr(expr=expr, line=line), False

    def _parse_literal(self):
        """
        <literal> --> <number>
                    | STRING
                    | TRUE
                    | FALSE
        """
        valid_literals = {
            tkn.INTEGER : tkn.INT_TYPE,
            tkn.FLOAT   : tkn.FLOAT_TYPE,
            tkn.STRING  : tkn.STRING_TYPE,
            tkn.TRUE    : tkn.BOOL_TYPE,
            tkn.FALSE   : tkn.BOOL_TYPE
        }
        if self.token.type in valid_literals.keys():
            value = self.token.value
            line = self.token.line
            data_type = valid_literals[self.token.type]
            self.next_token()
            return LiteralExpr(value, data_type, line=line), False
        
        return None, False

    def _parseNT_expression(self):
        """
         <expression>  -->  <arithOp> BOOL_AND <expression>
                        |   <arithOp> BOOL_OR <expression>
                        |   [ BOOL_NOT ] <arithOp>
        """
        # check for optional boolean NOT
        has_bool_not = False
        if self.token_is(tkn.BOOL_NOT,  consume=True):
            has_bool_not = True

        arithOp, err = self._parseNT_arithOp()
        if err:
            # pass error up
            return arithOp, err
        elif arithOp == None:
            # not an arithOp
            return None, has_bool_not # if BOOL_NOT is present then arithOp was expected, so flag err
        else:
            if self.token.type in [tkn.BOOL_AND, tkn.BOOL_OR]:
                Op = self.token.type
                line = self.token.line
                self.next_token()
                expr, err = self._parseNT_expression()
                return BinOpExpr(LHS=arithOp, RHS=expr, Op=Op, line=line), err
            else:
                return arithOp, False

    def _parseNT_arithOp(self):
        """
        <arithOp> -->   <relation> OP_ADD <arithOp>
                    |   <relation> OP_SUB <arithOp>
                    |   <relation>
        """
        relation, err = self._parseNT_relation()
        if err:
            return relation, err
        elif relation == None:
            return None, False
        else:
            if self.token.type in [tkn.OP_ADD, tkn.OP_SUB]:
                Op = self.token.type
                line = self.token.line
                self.next_token()
                arithOp, err = self._parseNT_arithOp()
                return BinOpExpr(LHS=relation, RHS=arithOp, Op=Op, line=line), err
            else:
                return relation, False

    def _parseNT_relation(self):
        """
        <relation> -->  <term> OP_LT <relation>
                     |  <term> OP_GE <relation>
                     |  <term> OP_LE <relation>
                     |  <term> OP_GT <relation>
                     |  <term> OP_EQ <relation> 
                     |  <term> OP_NE <relation>
                     |  <term>
        """
        term, err = self._parseNT_term()
        if err:
            return term, err
        elif term == None:
            return None, False
        else:
            relation_operators = [
                tkn.OP_LT,
                tkn.OP_GE,
                tkn.OP_LE,
                tkn.OP_GT,
                tkn.OP_EQ,
                tkn.OP_NE
            ]
            if self.token.type in relation_operators:
                Op = self.token.type
                line = self.token.line
                self.next_token()
                relation, err = self._parseNT_relation()
                return BinOpExpr(LHS=term, RHS=relation, Op=Op, line=line), err
            else:
                return term, False

    def _parseNT_term(self):
        """
        <term> -->  <factor> OP_MUL <term>
                 |  <factor> OP_DIV <term>
                 |  <factor>
        """
        factor, err = self._parseNT_factor()
        if err:
            return factor, err
        elif factor == None:
            return None, False
        else:
            term_operators = [
                tkn.OP_MUL,
                tkn.OP_DIV
            ]
            if self.token.type in term_operators:
                Op = self.token.type
                line = self.token.line
                self.next_token()
                term, err = self._parseNT_term()
                return BinOpExpr(LHS=factor, RHS=term, Op=Op, line=line), err
            else:
                return factor, False

    def _parseNT_factor(self):
        """
        <factor>  -->   LEFT_PAREN <expression> RIGHT_PAREN
                    |   <procedure_call>
                    |   [ OP_SUB ] <name>
                    |   [ OP_SUB ] <number>
                    |   STRING
                    |   TRUE
                    |   FALSE
        """

        if self.token_is(tkn.LEFT_PAREN, consume=True):
            return self._parseNT_expression()
        
        has_negative = False
        if self.token_is(tkn.OP_SUB, consume=True):
            has_negative = True

        if self.token_is(tkn.ID):
            call, err = self._parseNT_procedure_call()
            if err:
                return None, True
            elif call == None:
                # not a procedure call.
                # parse variable expression
                name = self.token.value
                line = self.token.line
                self.next_token()
                index, err = self._parseNT_array_index()
                if err:
                    return None, True
                else:
                    return VariableExpr(name, data_type=None, array_index=index, has_negative=has_negative, line=line), False
            else:
                return call, False
        else:
            return self._parse_literal()
            

    def _parseNT_procedure_call(self):

        if not self.token_is(tkn.ID):
            return None, False
        name = self.token.value
        line = self.token.line
        if not self._next_token.type == tkn.LEFT_PAREN:
            return None, False
        
        self.next_token()
        self.next_token()

        func = CallExpr(name, line=line)
        
        if self.token_is(tkn.RIGHT_PAREN, consume=True):
            return func, False
        else:
            p, err = self._parseNT_expression()
            func.params.append(p)
            while self.token_is(tkn.COMMA, consume=True):
                p, err1 = self._parseNT_expression()
                err = err or err1
                func.params.append(p)

            if not self.token_is(tkn.RIGHT_PAREN, consume=True):                
                self.reportUnexpectedToken(expected=')')
                return func, True
            else:
                return func, err


#=============================================================================
#  debuging test code
#=============================================================================

if __name__ == '__main__':

    #fName = "../test/correct/logicals.src"
    #fName = "../test/correct/iterativeFib.src"
    #fName = "../test/correct/math.src"
    #fName = "../test/correct/multipleProcs.src"
    #fName = "../test/correct/recursiveFib.src"
    #fName = "../test/correct/source.src"
    #fName = "../test/correct/test_heap.src"
    #fName = "../test/correct/test_program_minimal.src"
    #fName = "../test/correct/test1.src"
    fName = "../test/correct/test1b.src"
    #fName = "../test/correct/test2.src"


    parser = Parser(fName)

    # parse top level module info
    res = parser.parse_program_header()
    print("module name: {}".format(res))

    # parse top level declarations (variable or function)
    print("Parsing top Level Declarations")
    res = parser.parse_top_level_declaration()
    while res != tkn.BEGIN:
        print(res)
        res = parser.parse_top_level_declaration()

    print("==== found begin ====")
    print("Parsing Top Level Statements")
    res = parser.parse_top_level_statement()
    while res != tkn.EOF:
        print(res)
        res = parser.parse_top_level_statement()

    print("end of file")