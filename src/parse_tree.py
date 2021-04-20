## this module builds a parse tree from the token stream

## llvm codegen utils
from llvmlite import ir

## scanner and token code
from token import tkn_type as tkn
from token import Token
from scanner import Scanner
from symbol_table import Symbol
# ===========================================================================
# define parse tree nodes
class parseTreeNode():
    def __init__(self, line):
        self.line = line
        self.errList = []

    def getErrors(self):
        """ returns error string for this node and its children"""
        return ["Error L{}: {}".format(line, error) for line, error in self.errList]

class exprNode(parseTreeNode):
    def __init__(self):
        self.data_type = None

class BinOpExpr(exprNode):
    def __init__(self, LHS, RHS, Op, line):
        self.LHS = LHS
        self.RHS = RHS
        self.Op = Op
        self.line = line
        self.errList = []
        self.data_type = None

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "BinOpExpr({})".format(self.Op)
        out += "\n" + level * (7*" ") + "Left > "
        out += self.LHS.toString(level=level+1) if self.LHS else "None"
        out += "\n" + level * (7*" ") + "Right> "
        out += self.RHS.toString(level=level+1) if self.RHS else "None"
        return out

    def _check_operand_types(self):
        """ type check operands """
        return True

    def codegen(self, builder, symbolTable, module=None):
        # codegen each operand and check for errors
        LHS_val = self.LHS.codegen(builder, symbolTable)
        if not LHS_val:
            self.errList += self.LHS.errList
            return None

        RHS_val = self.RHS.codegen(builder, symbolTable)
        if not RHS_val:
            self.errList += self.LHS.errList
            return None

        # check operands for type compatability
        if not self._check_operand_types():
            err = "type {} and {} are not compatible under the operation {}".format(
                self.LHS.data_type,
                self.RHS.data_type,
                self.Op.type
            )
            self.errList.append((self.line, err))
            return None

        # call llvm codegen for given operator and types
        numeric_types = [tkn.INT_TYPE, tkn.FLOAT_TYPE]
        relation_ops = {
                tkn.OP_LT : "<",
                tkn.OP_GE : ">=",
                tkn.OP_LE : "<=",
                tkn.OP_GT : ">",
                tkn.OP_EQ : "==",
                tkn.OP_NE : "!="
        }

        if self.LHS.data_type == self.RHS.data_type:
            if self.LHS.data_type == tkn.INT_TYPE:
                # INTEGER operations
                self.data_type = tkn.INT_TYPE
                if self.Op == tkn.OP_ADD:
                    res = builder.add(LHS_val, RHS_val, name="addTmp")
                    return res
                elif self.Op == tkn.OP_SUB:
                    res = builder.sub(LHS_val, RHS_val, name="subTmp")
                    return res
                elif self.Op == tkn.OP_MUL:
                    res = builder.mul(LHS_val, RHS_val, name="mulTmp")
                    return res
                elif self.Op == tkn.OP_DIV:
                    res = builder.sdiv(LHS_val, RHS_val, name="divTmp")
                elif self.Op in relation_ops.keys():
                    # compare and set data_type to bool
                    res = builder.icmp_signed(relation_ops[self.Op], LHS_val, RHS_val, name="boolTmp")
                    self.data_type = tkn.BOOL_TYPE
                    return res

        elif self.LHS.data_type in numeric_types and \
             self.RHS.data_type in numeric_types:
            # promote to float
            if self.LHS.data_type == tkn.INT_TYPE:
                ir_type = symbolTable.get_ir_type(tkn.FLOAT_TYPE)  
                LHS_val = builder.sitofp(LHS_val, ir_type, name="floatTmp")

            if self.RHS.data_type == tkn.INT_TYPE:
                ir_type = symbolTable.get_ir_type(tkn.FLOAT_TYPE)  
                RHS_val = builder.sitofp(LHS_val, ir_type, name="floatTmp")
            # FLOAT Operations
            self.data_type = tkn.FLOAT_TYPE
            if self.Op == tkn.OP_ADD:
                return builder.fadd(LHS_val, RHS_val, name="floatTmp")
            elif self.Op == tkn.OP_SUB:
                return builder.fsub(LHS_val, RHS_val, name="floatTmp")
            elif self.Op == tkn.OP_MUL:
                return builder.fMul(LHS_val, RHS_val, name="floatTmp")
            elif self.Op == tkn.OP_DIV:
                return builder.fdiv(LHS_val, RHS_val, name="floatTmp")
            elif self.Op in relation_ops.keys():
                # compare and set data_type to bool
                res = builder.fcmp_unordered(relation_ops[self.Op], LHS_val, RHS_val, name="boolTmp")
                self.data_type = tkn.BOOL_TYPE
                return res

        elif self.LHS.data_type == tkn.STRING_TYPE:
            # STRING operations
            # scary... lets come back to this one
            pass
        elif self.LHS.data_type == tkn.BOOL_TYPE and \
             self.RHS.data_type == tkn.BOOL_TYPE:
            # BOOL Operations
            self.data_type = tkn.BOOL_TYPE
            if self.Op == tkn.BOOL_AND:
                res = builder.and_(LHS_val, RHS_val, name="boolTmp")
                return res
            elif self.Op == tkn.BOOL_OR:
                res = builder.or_(LHS_val, RHS_val, name="boolTmp")
                return res

        # handle any undefined operations
        err = "operation {} is not defined for types {} and {}".format(
            self.Op, 
            self.LHS.data_type, 
            self.RHS.data_type)
        self.errList.append((self.line, err))
        return None

            
class UnaryOpExpr(exprNode):
    def __init__(self, Op, expr, line):
        self.Op = Op
        self.expr = expr
        self.line = line
        self.errList = []
        self.data_type = None

    def toString(self, level=0):
        out = "UnaryOpExpr({})".format(self.Op)
        out += "\n" + level * (7*" ") + "expr > "
        out += self.expr.toString(level=level+1) if self.expr else "None"
        return out

    def codegen(self, builder, symbolTable, module=None):
        pass

class VariableExpr(exprNode):
    def __init__(self, name, data_type, line, array_index=None, has_negative=False):
        self.name = name
        self.array_index = array_index
        self.has_negative = has_negative
        self.line = line
        self.errList = []
        self.data_type = None

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "variable ('{}', {}, negative={})".format(self.name, self.data_type, self.has_negative)
        if self.array_index:
            out += " index={}".format(self.array_index)
        return out

    def codegen(self, builder, symbolTable, module=None):
        
        if self.array_index != None:
            pass
            # TODO: handle arrays
            # TODO: also handle has_negative ... may move to a UnaryOpExpr class
        res = symbolTable.get(self.name)
        if res == None:
            self.errList.append((self.line, "variable {} is undefined".format(self.name)))
            return None
        self.data_type = res.type
        return res.value

class LiteralExpr(exprNode):
    def __init__(self, value, data_type, line):
        self.value = value
        self.line = line
        self.errList = []
        self.data_type = data_type

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        return "Literal {}: value={}".format(self.data_type, self.value)

    def codegen(self, builder, symbolTable, module=None):

        ir_type = symbolTable.get_ir_type(self.data_type)
        if self.data_type == tkn.INT_TYPE:
            val = int(self.value)
        elif self.data_type == tkn.FLOAT_TYPE:
            val = float(self.value)
        elif self.data_type == tkn.BOOL_TYPE:
            val = 0 if self.value == "false" else 1
        elif self.data_type == tkn.STRING_TYPE:
            val = self.value
        else:
            self.errList.append((self.line, "literal value has an undefined type"))
            return None
        return ir.Constant(ir_type, val)
        
class CallExpr(exprNode):
    def __init__(self, name, line):
        self.name = name
        self.params = []
        self.line = line
        self.errList = []
        self.data_type = None

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "function call (name: {})".format(self.name)
        for expr in self.params:
            out += "\n" + level * (7*" ") + "param> "
            out += expr.toString(level=level+1) if expr else "None"
        return out

    def codegen(self, builder, symbolTable, module=None):
        
        # get function ref
        func = symbolTable.get(self.name)
        if func == None or func.value == None:
            self.errList.append((self.line, "function {} is undefined".format(self.name)))
            return None
        func = func.value
        args = []
        for param in self.params:
            # check type of arg matches expected type
            p_val = param.codegen(builder, symbolTable)
            if p_val == None:
                self.errList += param.errList
                return None
            args.append(p_val)

        return builder.call(func, args, name="res")

class returnExpr(exprNode):
    def __init__(self, expr, line):
        self.expr = expr
        self.line = line
        self.errList = []

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "return statement"
        out += "\n" + level * (7*" ") + "expr > "
        out += self.expr.toString(level=level+1) if self.expr else "None"
        return out

    def codegen(self, builder, symbolTable, module=None):
        expr_val = self.expr.codegen(builder, symbolTable)
        if expr_val == None:
            self.errList += self.expr.errList
            return None
        
        if builder.block.is_terminated:
            self.errList.append(self.line, "return after termination of code block")
            return None

        return builder.ret(expr_val)

class AssignmentNode(parseTreeNode):
    def __init__(self, destination, expression, line):
        self.expr = expression
        self.dest = destination
        self.line = line
        self.errList = []

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "assignment"
        out += "\n" + level * (7*" ") + "dest > "
        out += self.dest.toString(level=level+1) if self.dest else "None"
        out += "\n" + level * (7*" ") + "expr > " 
        out += self.expr.toString(level=level+1) if self.expr else "None"
        return out

    def codegen(self, builder, symbolTable, module=None):
        # check that dest is defined
        dest_val = self.dest.codegen(builder, symbolTable)
        dest_name = self.dest.name
        if dest_val == None:
            self.errList += self.dest.errList
            return None

        expr_val = self.expr.codegen(builder, symbolTable)
        if expr_val == None:
            self.errList += self.expr.errList
            return None

        symbol = Symbol(dest_name, expr_val, self.dest.data_type)
        if not symbolTable.update(symbol):
            self.errList.append((self.line, "could not update symbol {}".format(dest_name)))
            return None
        else:
            return expr_val

class declarationNode(parseTreeNode):
    def __init__(self, name, data_type, line, is_global=False, array_size=None):
        self.name = name
        self.type = data_type
        self.is_global = is_global
        self.array_size = array_size # None if var is not an array
        self.line = line
        self.errList = []

    def __str__(self):
        return self.toString()

    def toString(self, level=0):
        out = "declaration of {} as {} global={}".format(self.name, self.type, self.is_global)
        if self.array_size != None:
            out += " array_size= {}".format(self.array_size)
        return out

    def codegen(self, builder, symbolTable, module=None):
        ir_type = symbolTable.get_ir_type(self.type)
        if self.type == tkn.STRING_TYPE:
            val = ""
        else:
            val = 0
        initial_val = ir.Constant(ir_type, val)
        symbol = Symbol(self.name, initial_val, self.type)
        
        if symbolTable.add(symbol, is_global=self.is_global):
            return initial_val
        else:
            self.errList.append(self.line, "duplicate declaration")
            return None

class IfNode(parseTreeNode):
    def __init__(self, condition, line):
        self.condition = condition
        self.thenBlock = []
        self.elseBlock = None
        self.line = line
        self.errList = []

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

    def codegen(self, builder, symbolTable, module=None):
        
        cond_val = self.condition.codegen(builder, symbolTable)
        if cond_val == None:
            self.errList += self.condition.errList
            return None

        thenBB = builder.append_basic_block(name="thenBlock")
        mergeBB = builder.append_basic_block(name="mergeBlock")
        if self.elseBlock != None:
            # create else block and add branch
            elseBB = builder.append_basic_block(name="elseblock")
            builder.cbranch(cond_val, thenBB, elseBB)
            # codegen else block
            builder.position_at_start(elseBB)
            for statement in self.elseBlock: # pylint: disable=not-an-iterable
                res = statement.codegen(builder, symbolTable)
                if res == None:
                    self.errList += statement.errList
            # branch to merge block at end of else
            if not builder.block.is_terminated: 
                builder.branch(mergeBB)
        else:
            # add branch that without else block
            builder.cbranch(cond_val, thenBB, mergeBB)
        # codegen for then block
        builder.position_at_start(thenBB)
        for statement in self.thenBlock: # pylint: disable=not-an-iterable
            res = statement.codegen(builder, symbolTable)
            if res == None:
                self.errList += statement.errList
        # branch to merge block at end of then block
        # check in case a return statement terminates the block
        if not builder.block.is_terminated: 
            builder.branch(mergeBB)
        builder.position_at_start(mergeBB)
        return cond_val

class LoopNode(parseTreeNode):
    def __init__(self, start, end, line):
        self.start = start
        self.end = end
        self.body = []
        self.line = line
        self.errList = []

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

    def codegen(self, builder, symbolTable, module=None):
        # evaluate start and end statements
        start_val = self.start.codegen(builder, symbolTable)
        if start_val == None:
            self.errList += self.start.errList
            return None
        
        end_val = self.end.codegen(builder, symbolTable)
        if end_val == None:
            self.errList += self.end.errList
            return None

        # create loop blocks  
        loopBB = builder.append_basic_block(name="loopBody")
        mergeBB = builder.append_basic_block(name="loopMerge")

        # add initial loop condition
        builder.cbranch(end_val, loopBB, mergeBB)

        # codegen for loop block
        builder.position_at_start(loopBB)

        for statement in self.body:
            res = statement.codegen(builder, symbolTable)
            if res == None:
                self.errList += statement.errList

        # add branch and move to block outside of loop
        builder.cbranch(end_val, loopBB, mergeBB)
        builder.position_at_start(mergeBB)

        return start_val


class functionNode(parseTreeNode):
    def __init__(self, name, retType, params, line):
        self.name = name
        self.retType = retType
        self.params = params
        self.body = []
        self.line = line
        self.errList = []

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

    def codegen(self, builder, symbolTable, module):

        params_ir = [symbolTable.get_ir_type(param.type) for param in self.params]
        fType = ir.FunctionType(symbolTable.get_ir_type(self.retType), params_ir)
        func = ir.Function(module, fType, name=self.name)
        for i in range(len(self.params)):
            func.args[i].name = self.params[i].name
        
        # add func to symboltable
        symbol = Symbol(self.name, func, fType, id_type='function')
        if not symbolTable.add(symbol):
            self.errList.append(self.line, "duplicate declaration")
            return None

        # add local scope and populate with params
        symbolTable.pushLocal()
        for i, var in enumerate(func.args):
            symbol = Symbol(self.params[i].name, var, self.params[i].type)
            if not symbolTable.add(symbol):
                self.errList.append(self.line, "duplicate parameter declaration")
                return None

        # make new function builder and add entry
        entryBB = func.append_basic_block(name="funcEntry")
        func_builder = ir.IRBuilder(entryBB) 
        has_errors = False
        for statement in self.body:
            res = statement.codegen(func_builder, symbolTable)
            if res == None:
                has_errors = True
            else:
                last_stmt = res
            
        # remove local scope and handle errors
        symbolTable.popLocal()
        if has_errors:
            self.errList += statement.errList
            return None
        elif not func_builder.block.is_terminated:
            func_builder.ret(last_stmt) 
            # not sure if this is defined anywhere in the language spec,
            # but sample correct programs return values with no explicit return statement
            # Im assuming then that an implicit return is allowed
        return func