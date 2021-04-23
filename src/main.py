from argparse import ArgumentParser
from codegen import ProgramBuilder

def main():
    ap = ArgumentParser()
    ap.add_argument("inputFile")
    ap.add_argument("outputFile")
    args = ap.parse_args()
    codegen = ProgramBuilder(args.inputFile, args.outputFile)
    codegen.generate_module_code()

if __name__ == '__main__':
    main()