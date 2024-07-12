"""Extracts bytes from pdf files"""

import re
class FileReader:
  def __init__(self,file):
    self.f = file
  def read_byte_as_int(self):
    byte = self.f.read(1)
    a = int.from_bytes(byte)
    return a

  def read_byte_as_char(self):
    return chr(self.read_byte_as_int())

  def set_file(self,file):
    self.f = file

  def go_to_next_whitespace(self):
    while (a := self.read_byte_as_char()) != '\n' and a != ' ':
      pass

  def read_string(self):
    s = ''
    a = self.read_byte_as_int()

    while chr(a) == '\n' or chr(a) == ' ':
      a = self.read_byte_as_int()

    while True:
      if a < 128:
        if chr(a) == '\n' or chr(a) == ' ':
          break
        s += chr(a)
      a = self.read_byte_as_int()

    return s

  def read_num(self):
    n = self.read_string()
    return int(n)

  def read_arr(self):
    while self.read_byte_as_char() != '[':
      pass

    s = ''
    while (a:= self.read_byte_as_char()) != ']':
      s += a

    nums = s.split('R')
    nums.pop()
    arr = []
    for i in nums:
      arr.append(int(re.findall(r'\d+',i)[0]))

    return arr
