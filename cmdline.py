"""Command line application that remove pages from pdf"""
import cmd2
from page_remover import PageRemover as simplePageRemover


class PageRemoverCli(cmd2.Cmd):

  #parsers
  del_parser = cmd2.Cmd2ArgumentParser()
  del_parser.add_argument('page',help=
  'Page number of page to be removed,or type page a-b to remove from page a-b (inclusive)')

  set_file_parser = cmd2.Cmd2ArgumentParser()
  set_file_parser.add_argument('fileName',help = 'Name of file to be modified')

  save_parser = cmd2.Cmd2ArgumentParser()
  save_parser.add_argument('fileName',help = 'Name of file to be saved')

  def __init__(self):
    cmd2.Cmd.__init__(self, startup_script='.cmd2rc', silence_startup_script=True)
    self.page_remover = None

  def do_num_pages(self,line):
    """Displays number of pages of current file set.
       Can type np as shortcut for same functionality
    """
    if self.page_remover is None:
      self.poutput('Set file before deleting pages')
      return
    self.poutput(self.page_remover.get_page_num())

  @cmd2.with_argparser(del_parser)
  def do_delete(self,args):
    """Deletes page as first and only argument.
       Can also delete a range by typing a-b
       Can type d as shortcut for same functionality
    """
    if self.page_remover is None:
      self.poutput('Set file by typing sf or set_file before deleting pages')
      return

    page_num1 = 0
    page_num2 = 0
    two_pages = False

    if args.page.count('-') > 1:
      self.poutput('invalid page numbers')
      return

    if args.page.count('-') != 0:
      two_pages = True
      split_nums = args.page.split('-')
      for i in split_nums:
        if i.isdigit() is False:
          self.poutput('invalid page numbers')
          return


        page_num1 = int(split_nums[0])
        page_num2 = int(split_nums[1])

    else:
      if args.page.isdigit() is False:
          self.poutput('invalid page numbers')
          return
      page_num1 = int(args.page)

    def invalid_page(n):
      return (n < 0 or n > self.page_remover.get_page_num())

    if two_pages:
      if page_num1 > page_num2:
        page_num2,page_num1 = page_num1,page_num2
      if invalid_page(page_num1) or invalid_page(page_num2):
        self.poutput(f'Cannot delete pages {page_num1}-{page_num2} from book with {self.page_remover.get_page_num()} pages')
        return
      for i in range(page_num2 - page_num1+1):
        self.page_remover.delete_page(page_num1)
    else:
      if invalid_page(page_num1) is True:
        self.poutput(f'Cannot delete page {page_num1} from book with {self.page_remover.get_page_num()} pages')
        return
      self.page_remover.delete_page(page_num1)


  @cmd2.with_argparser(set_file_parser)
  def do_set_file(self,args):
    """Sets pdf specified as first and only argument as current file.
       Can also type sf as shortcut for same functionality
    """
    try:
        self.page_remover = simplePageRemover(args.fileName)
    except FileNotFoundError as e:
        self.poutput(e)
        return

    self.file_set = True


  @cmd2.with_argparser(save_parser)
  def do_save_changes(self,args):
    """Saves current pdf being edited to location specified as first and only argument.
       Can also type s as shortcut for same functionality
    """
    if self.page_remover is None:
      self.poutput('File not set')
      return

    name = args.fileName
    if name[0].isalpha() is False:
      self.poutput('invalid file name')
      return
    if len(name) < 4  or name[len(name) -4:] != '.pdf':
      name += '.pdf'
    self.page_remover.save_file(name)


if __name__ == '__main__':
  import sys
  c = PageRemoverCli()
  sys.exit(c.cmdloop())
