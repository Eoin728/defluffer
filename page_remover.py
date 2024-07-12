'''Parses a pdf for necessary information and removes pages from its
document structure
'''

import os
import shutil
import re
from file_reader import FileReader


class PageRemover:
  def __init__(self, file_name):

    #xref table
    self.xref_table = []
    self.xref_table_size = 0

    self.number_of_pages = 0

    #pages to object numbers
    self.pages = []
    #object numbers to pages
    self.objects = {}

    #create temporary file for editing
    if len(file_name) < 5 or file_name[len(file_name) - 4:] != '.pdf':
      raise ValueError(f'{file_name} is not a pdf')
    self.curr_file_loc = '/tmp/' + file_name[:len(file_name) - 4] + 'tmp.pdf'
    shutil.copyfile(file_name, self.curr_file_loc)
    self.f = open(self.curr_file_loc, 'r+b')
    self.fr = FileReader(self.f)

    #check for pdf header
    if self.pdf_header_check() is False:
      raise TypeError('invalid pdf file')

    #get necessary pdf information
    self._build_xref_table()
    page_table_root = self._get_page_table_root()
    self.pages = [0] * self.xref_table_size
    self._get_pages(page_table_root, None)

  class Node:
    '''Contains information about a page object in pdf page tree'''
    def __init__(self, children, typ, kids_loc,num,num_pos):
      self.children = children
      self.type = typ
      self.kids_loc = kids_loc
      self.par = None
      self.count = num
      self.num_pos = num_pos

    def set_par(self, p):
      self.par = p
    def set_obj_num(self,obj_num):
      self.obj_num = obj_num

  def _find_target_from_end(self, target):
    target = target[::-1]
    self.f.seek(0, os.SEEK_END)
    end = self.f.tell()
    i = 1
    s = ''
    while end -i > 0:
      self.f.seek(end - i)
      a = self.fr.read_byte_as_int()
      if a < 128:
        if a == ord('\n'):
          if s.find(target) != -1:
            break
          s = ''
        else:
          s += chr(a)
        i += 1
    if end - i <= 0:
      raise TypeError(f'file does not contain {target}')
    return end - (i -1 )

  def pdf_header_check(self):
    self.f.seek(0)
    return re.search(r'%PDF-\d+.\d+',self.fr.read_string()) is not None

  def save_file(self,name):
    shutil.copyfile(self.curr_file_loc,name)

  def _build_xref_table(self):
    x_ref_start = self._find_target_from_end('startxref')
    self.fr.go_to_next_whitespace()
    x_ref_start = self.fr.read_num()
    self.f.seek(x_ref_start)
    while self.fr.read_string() != 'xref':
      pass
    gennumber = self.fr.read_num()
    self.xref_table_size = self.fr.read_num()
    self.xref_table = [0] * self.xref_table_size
    index = 0
    for k in range(self.xref_table_size):
      offset = self.fr.read_num()
      gennum = self.fr.read_num()
      ch = self.fr.read_string()
      self.xref_table[index] = offset
      index += 1

  def _get_page_table_root(self):
    trailer_start = self._find_target_from_end('trail')
    self.f.seek(trailer_start)
    rootobjnum = None
    while (s := self.fr.read_string()) != '>>?':
      if s[1:] == 'Root':
        rootobjnum = self.fr.read_num()
        break
    if rootobjnum is None:
      raise TypeError(f'file trailer did not contain root')
    self.f.seek(self.xref_table[rootobjnum])
    s = self.fr.read_string()
    while s.find('Pages') == -1:
      s = self.fr.read_string()
    return self.fr.read_num()

  def get_page_num(self):
    return self.number_of_pages


  def _parse_object_for_page_info(self):
    children = []
    parent = None
    typ = ''
    kid_loc = 0
    num = None
    num_pos = None
    while (s := self.fr.read_string()) != 'obj':
      pass
    while s != 'endobj':
      if s[1:] == 'Page':
        typ = 'Page'
      elif s[1:] == 'Pages':
        typ = 'Pages'
      elif s[1:] == 'Parent':
        parent = self.fr.read_num()
      elif s[1:] == 'Kids':
        kid_loc = self.f.tell()
        children = self.fr.read_arr()
      elif s[1:] == 'Count':
        while not self.fr.read_byte_as_char().isdigit():
          pass
        num_pos= self.f.tell() - 1
        self.f.seek(num_pos-1)

        num = self.fr.read_num()
      s = self.fr.read_string()
    return self.Node(children, typ, kid_loc,num,num_pos)

  def _get_pages(self, i, par):
    self.f.seek(self.xref_table[i])
    n = self._parse_object_for_page_info()
    n.set_par(par)
    n.set_obj_num(i)
    self.objects[i] = n
    if n.type == 'Pages':
      for k in n.children:
        self._get_pages(k, n)
    else:
      self.number_of_pages += 1
      self.pages[self.number_of_pages] = i

  def _delete_child(self, par_kids_loc, child):
    self.f.seek(par_kids_loc)
    while self.fr.read_byte_as_char() != '[':
      pass
    while self.fr.read_string() != str(child):
      pass
    self.f.seek(self.f.tell() - (len(str(child)) + 1))
    for i in range(3):
      a = self.fr.read_string()
      self.f.seek(self.f.tell() - (len(str(a)) + 1))
      if a.find(']') != -1:
        a = a[:a.find(']')]
      for k in range(len(str(a))):
        self.f.write((' ').encode('utf-8'))

  def _reduce_count(self,n):
    newnum = n.count - 1
    if len(str(newnum)) < len(str(n.count)):
      k= len(str(newnum))
      self.f.seek(n.num_pos +  k)
      self.f.write((' ').encode('utf-8'))
    k= len(str(newnum))
    for i in range(len(str(newnum)) - 1,-1,-1):
      self.f.seek(n.num_pos  + i )
      towrite = str(newnum % 10)
      towrite = ord(towrite).to_bytes(1, 'big')
      self.f.write(towrite)
      newnum //= 10
    n.count -= 1

  def delete_page(self, i):
    if i < 1 or i > self.number_of_pages:
      raise ValueError(
          f'Tried to remove page {i} from book with {self.number_of_pages} pages')
    objnum = self.pages[i]
    n = self.objects[objnum]
    self._delete_child(n.par.kids_loc, objnum)
    n= n.par
    while n is not None:
      self._reduce_count(n)
      if n.count == 0:
        self._delete_child(n.par.kids_loc, n.obj_num)
      n= n.par
    self.number_of_pages -= 1
    self.pages = self.pages[:i] + self.pages[i + 1:]

    #force file update
    self.f.flush()
    os.fsync(self.f.fileno())
