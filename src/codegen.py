from llvmlite import ir, binding
import llvmlite.binding as llvm

from symbol_table import SymbolTable, Symbol
from token import tkn_type as tkn
# no name in module is a bug with pylint? Parser definitely exists.
from parser import Parser # pylint: disable=no-name-in-module

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

        # load builtin I/O functions
        self.load_builtins()

        # create main function
        func_type = ir.FunctionType(ir.VoidType(), [], False)
        base_func = ir.Function(self.module, func_type, name="main")
        block = base_func.append_basic_block(name="entry")

        # create llvm ir builder and set at start of the main block
        self.builder = ir.IRBuilder(block)


    def load_builtins(self):
        """ create builtin get and put functions (empty for now)"""
        # name returnType Param
        builtins = [
            ("putbool",    ir.VoidType(), [ir.IntType(1)]),
            ("putstring",  ir.VoidType(), [ir.IntType(8)]),
            ("putinteger", ir.VoidType(), [ir.IntType(32)]),
            ("putfloat",   ir.VoidType(), [ir.FloatType()]),
            ("getbool",    ir.IntType(1), []),
            ("getstring",  ir.IntType(8), []),
            ("getinteger", ir.IntType(32), []),
            ("getfloat",   ir.FloatType(), [])
        ]
        # TODO figure out how to do array passing between functions for strings

        for entry in builtins:
            fType = ir.FunctionType(entry[1], entry[2])
            func = ir.Function(self.module, fType, name=entry[0])
            symbol = Symbol(entry[0], func, fType, id_type='function')
            self.symbolTable.add(symbol)

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
        # parse and generate top level declarations (variable or function)
        res = self.parser.parse_top_level_declaration()
        while res != tkn.BEGIN:
            if res != None: # and (not self.has_errors()):
                ir = res.codegen(self.builder, self.symbolTable, self.module)
                if ir == None:
                    self._has_errors = True
                    print("\n".join(res.getErrors()))
            res = self.parser.parse_top_level_declaration()
        # parse and generate top level statements
        res = self.parser.parse_top_level_statement()
        while res != tkn.EOF:
            if res != None: #and (not self.has_errors()):
                ir = res.codegen(self.builder, self.symbolTable, self.module)
                if ir == None:
                    self._has_errors = True
                    print("\n".join(res.getErrors()))
            res = self.parser.parse_top_level_statement()

        if not self.has_errors():
            print("writing IR to LLVM assembly\n")
            self.output_ir()
        else:
            print("errors detected, compilation aborted")
            self.output_ir()

if __name__ == '__main__':

    # input_fName = "../test/correct/iterativeFib.src"
    # input_fName = "../test/correct/logicals.src" # TODO Fix string param passing
    # input_fName = "../test/correct/math.src"
    # input_fName = "../test/correct/multipleProcs.src" # TODO duplicate name err in function generation... rename?
    # input_fName = "../test/correct/recursiveFib.src"
    # input_fName = "../test/correct/source.src"
    # input_fName = "../test/correct/test_heap.src"
    # input_fName = "../test/correct/test_program_minimal.src"
    # input_fName = "../test/correct/test1.src"
    # input_fName = "../test/correct/test1b.src"
    # input_fName = "../test/correct/test2.src"

    #input_fName = "../test/incorrect/test1.src"
    # input_fName = "../test/incorrect/test1b.src"

    output_fName = "out.txt"
    codegen = Builder(input_fName, output_fName)
    codegen.generate_module_code()
    # GAAAAAHAHAHA
