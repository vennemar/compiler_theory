from llvmlite import ir, binding
import llvmlite.binding as llvm

from symbol_table import SymbolTable
from token import tkn_type as tkn
from parser import Parser

# ========================= #
# IR Builder                #
# ========================= #

class Builder():
    """ manages the in memory IR for LLVM """ 
    
    def __init__(self, input_fName, output_fName):
        self.symbolTable = SymbolTable()
        self.parser = Parser(input_fName)
        self.output_fName = output_fName
        self._has_errors = False

        # llvm setup
        binding.initialize()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()
    
    def has_errors(self):
        """ checks the flags for scanner, parser or codegen errors"""
        return self._has_errors or self.parser._has_errors or self.parser.scanner._has_errors

    def initialize_module(self, name):
        # create module
        self.module = ir.Module(name=name)
        self.module.triple = binding.get_default_triple()

        # create main function
        func_type = ir.FunctionType(ir.VoidType(), [], False)
        base_func = ir.Function(self.module, func_type, name="main")
        block = base_func.append_basic_block(name="entry")

        # create llvm ir builder and set at start of the main block
        self.builder = ir.IRBuilder(block)

    def output_ir(self):
        # signal return from main function
        # self.builder.ret_void()
        output = str(self.module)
        print(output)
        with open(self.output_fName, "w") as fd:
            fd.write(output)
        
    def generate_module_code(self):
        """ runs the parse loop and calls codegen functions for the input program"""

        # parse top level module info
        moduleName = self.parser.parse_program_header()
        if not moduleName:
            print("could not parse module header")
            return None
        self.initialize_module(moduleName)
        print("generating module: {}".format(moduleName))

        # parse top level declarations (variable or function)
        print("generating Declarations")
        res = self.parser.parse_top_level_declaration()
        while res != tkn.BEGIN:
            if res != None and (not self.has_errors()):
                ir = res.codegen(self.builder, self.symbolTable, self.module)
                if ir == None:
                    self._has_errors = True
                    print("\n".join(res.getErrors()))
            res = self.parser.parse_top_level_declaration()

        print("generating main body")
        res = self.parser.parse_top_level_statement()
        while res != tkn.EOF:
            if res != None and (not self.has_errors()):
                ir = res.codegen(self.builder, self.symbolTable, self.module)
                if ir == None:
                    self._has_errors = True
                    print("\n".join(res.getErrors()))
            res = self.parser.parse_top_level_statement()

        print("writing IR to LLVM assembly\n") 
        self.output_ir()


if __name__ == '__main__':

    input_fName = "../test/correct/math.src"
    output_fName = "out.txt"
    codegen = Builder(input_fName, output_fName)
    codegen.generate_module_code()
    # GAAAAAHAHAHA
