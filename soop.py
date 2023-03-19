#!/usr/bin/env/python3
import string
import sys
from libs.Lexer import *

errorno = None
lerr = None

def help():
  print("python3 sl.py FLAGS FILENAME")
  print("FLAGS:-")
  print("        help        - prints this help screen, and exists with error code 0")

def read_program(fd : str) -> str:
  with open(fd, 'r') as prog:
    program = prog.read()
  return program 

class SymbolTable:
  def __init__(self):
    self.symbols = {}
    self.parent = None

  def get(self, name):
    value = self.symbols.get(name, None)
    if value == None and self.parent:
      return self.parent.get(name)
    return value

  def set(self, name, value):
    self.symbols[name] = value

  def remove(self, name):
    del self.symbols[name]

class Interpreter:
  def __init__(self, fd, program, global_symbol_table):
    self.fd = fd
    self.tokens = program
    self.Gsym = global_symbol_table
    self.sym = SymbolTable()

    self.prepro_words = [
      TT_DUKE
    ]

  def run_program(self):
    self.pre_run()
    self.post_run()
    
# if self.tokens[ip].value in mac_names:
#   cfname = self.tokens[ip].value
#   preip = ip
#   cfblock = macs.get(cfname)

#   for i in range(len(cfblock)):
#     self.tokens.insert(i+ip, cfblock[i])
#   self.tokens.pop(len(cfblock)+ip)

#   ip = preip-len(cfblock)
    
  def pre_run(self):
    ip = 0
    while len(self.tokens) > ip:
      if self.tokens[ip].type in self.prepro_words:
        if self.tokens[ip].type == TT_DUKE:
          dname = self.tokens[ip+1].value
          if dname == "include":
            inc_path   = self.tokens[ip+2].value
            preip = ip
            if inc_path == None:
              print("ERROR: `include` does not have a reference to the include path")
              print("                                                       - prepro")
              exit(-1)
            inc_prog   = read_program(inc_path)
            tmp_lexer  = Lexer(inc_path, inc_prog)
            inc_tokens, err = tmp_lexer.make_tokens()
            inc_tokens.pop(-1)
            if err:
              print(Error.as_string(err))
              exit(-1)
            for i in range(len(inc_tokens)):
              self.tokens.insert(i+ip, inc_tokens[i])
            self.tokens.pop(len(inc_tokens)+ip)
            self.tokens.pop(len(inc_tokens)+ip)
            self.tokens.pop(len(inc_tokens)+ip)
            ip=preip-1
          elif dname == None:
            print("ERROR: DUKE `@` needs a following instruction")
            print("                                           - prepro")
            exit(-1)
          else:
            print("ERROR: Unknown instruction following the DUKE `@`")
            print("                                           - prepro")
            exit(-1)
      else:
        pass
      ip += 1
    
  def post_run(self):
    ip = 0
    stack = {}
    std_buffer = []
    macs = {}
    mac_names = []
    while len(self.tokens) > ip:
      if self.tokens[ip].type == TT_STRING:
        stack[ip] = self.tokens[ip].value
      elif self.tokens[ip].type == TT_INT:
        stack[ip] = self.tokens[ip].value        
      elif self.tokens[ip].type == TT_KEYWORD:
        if self.tokens[ip].value == "set":
          prev = stack.get(ip-1)
          std_buffer.append(prev)
        elif self.tokens[ip].value == "return":
          code = self.tokens[ip+1].value
          exit(int(code))
        elif self.tokens[ip].value == "stdout":
          for i in std_buffer:
            nl = False
            if "\\" in str(i):
              nl = True
              i = i[:-2]
            self.stdout(i, nl)
          std_buffer.clear()
        elif self.tokens[ip].value == "rem":
          std_buffer.popitem()
        elif self.tokens[ip].value == "func":
          ignored_types = [
            "NEWLINE",
            "EOF"
          ]
          fname = self.tokens[ip+1].value
          mac_names.append(fname)
          fblock = []
          tmp = ip+2
          while (self.tokens[tmp].value != "end" and self.tokens[tmp] != None):
            if self.tokens[tmp] != None and self.tokens[tmp].type not in ignored_types:
              fblock.append(self.tokens[tmp])
            tmp += 1
          macs[fname] = fblock
          ip = tmp
        elif self.tokens[ip].value == "end":
          pass
        else:
          print(f"unknown keyword/instruction: {self.tokens[ip].type}:{self.tokens[ip].value}")
          exit(-1)
      elif self.tokens[ip].type == TT_IDENTIFIER:
        if self.tokens[ip].value in mac_names:
          cfname = self.tokens[ip].value
          preip = ip
          cfblock = macs.get(cfname)
          for i in range(len(cfblock)):
            self.tokens.insert(i+ip, cfblock[i])
          self.tokens.pop(len(cfblock)+ip)
          ip = preip-len(cfblock)
      elif self.tokens[ip].type == TT_EOF:
        pass
      elif self.tokens[ip].type == TT_NEWLINE:
        pass
      elif self.tokens[ip].type in self.prepro_words:
        pass
      else:
        print(f"unknown word/instruction: {self.tokens[ip].type}:{self.tokens[ip].value}")
        exit(-1)
      ip += 1

  def stdout(self, string, newline=False):
    if newline:
      print(string)
    else:
      print(string, end='')
    
global_symbol_table = SymbolTable()

def main():
  global errorno
  global lerr
  lerr = False
  if (not len(sys.argv) > 1):
    help()
    errorno = "ERROR: no file descriptor given, please input file path"
    return 1, errorno
  fd = sys.argv[1]
  program = read_program(fd)

  lexer = Lexer(fd, program)
  tokens, err = lexer.make_tokens()
  if err:
    errorno = err
    lerr = True
    return 1, errorno

  interpreter = Interpreter(fd, tokens, global_symbol_table)
  interpreter.run_program()

  return 0, errorno


if __name__ == '__main__':
  code, errn = main()
  if errn:
    if lerr:
      print(Error.as_string(errn))
    else:
      print(errn)
    exit(code)
