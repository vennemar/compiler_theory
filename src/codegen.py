from llvmlite import ir
# from ctypes import *
import llvmlite.binding as llvm

#================================
from token import tkn_type as tkn
from symbol_table import SymbolTable, Symbol

class Builder():
    def __init__(self):
        self.symbol_table = SymbolTable()

    def get_ir_type(self, tkn_type, is_array=False, length=None):
        type_map = {
            tkn.INT_TYPE    : ir.IntType(32),
            tkn.FLOAT_TYPE  : ir.FloatType, # TODO: research how this works
            tkn.BOOL_TYPE   : ir.IntType(1),
            tkn.STRING_TYPE : ir.IntType(8) 
            # a char is an 8 bit int, so strings must have is_array=True and length set
        }

        if is_array:
            if length <= 0:
                return (None, "array bounds must be greater than 0")
            return ir.ArrayType(self.get_ir_type(tkn_type), length)
        else:
            return type_map[tkn_type]


    def initialize_module(self, name):
        self.module = ir.Module(name=name)
        self.builder = ir.IRBuilder()

    def create_function_prototype(self, name, retType, params):
        for i in range(len(params)):
            params_ir += self.get_ir_type(params[0])
            
        fType = ir.FunctionType(self.get_ir_type(retType), params_ir)
        func = ir.Function(self.module, fType, name=name)
        for i in range(len(params)):
            func.args[i].name = params[i][1]
        
        # add func to symbol table?
        self.symbol_table.add_id(name, func, fType, id_type='function')

        # set code insertion point to the start of the function
        entryBlock = func.append_basic_block('entry')
        self.builder.goto_block(entryBlock)

        
    def create_binOp():
        
