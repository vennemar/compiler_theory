from llvmlite import ir
from ctypes import *
import llvmlite.binding as llvm

#================================
from token.py import tkn_type as tkn

class Builder():
    def __init__(self, parser):
        self.parser = parser
        module_name = parser.scanner.fName
        self.module = ir.Module(name=module_name)

    def reportError(self, message):
        """ ir builder level error reporting"""
        self.parser.reportError(message)

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
                self.reportError("array bounds must be greater than 0")
                return None
            return ir.ArrayType(self.get_ir_type(tkn_type), length)
        else:
            return type_map[tkn_type]