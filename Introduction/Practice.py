Instancce atrributes: unique per object, live in obj.__dict__
Class attrinutes: shared across instances, live in Class.__dict__
Modifying via instace creates shadowning instance attribute


Check instance __dict__
Check class __dict__ and MRO
Call __getattr__ or raise AttributeError

Class vs Instance Variable: Understanding shared vs Unique attributes
Class vs Instance Variable: Understanding shared vs Unique attributes
Behavioral: Command, Itrator, Observer, Strategy
Creational: Abstract Factory, Factory, Builder, Singleton



Command Pattern

from __future__ import annotations
from dataclass import dataaclass
from typing import List



# Receiver
class TextDocument:
    def __init__(self):
        self.text = ""

    def insert(self, s: str):
        self.text += s

    def delete_last(self, n: int):
        self.text = self.text[:-n] if n <= len(self.text) else ""

class TextDocument:
    def __init__(self):
        self.text=""
    
    def insert(self,s):
        self.text+=s

    def delete_last(self,n):
        self.text=self.text[:-n] if n<=len(self.text) else ""
    
class Command:
    def execute(self):
        raise NotImplementedError
    
    def undo(self):
        raise NotImplementedError

@dataclass
def InsertCommand(Command):
    doc: TextDocument
    s: str

    def execute(self):
        self.doc.insert(self.s)
    
    def undo(self):
        self.doc.delete_last(len(self.s))

@dataclass
def DeleteCommand(Command):
    doc: TextDocument
    s:str
    deleted_text:str=""

    def execute(self):
        self.deleted_text = self.doc.text[-self.n:] if self.n <= len(self.doc.text) else self.doc.text
        self.doc.delete_last(self.n)

        self.deleted_text=self.doc.text[-self.n:] if self.n<=len(self.doc.text) else self.doc.text
        self.deleted_text=self.doc.text[-self.n:] if self.n<=len(self.doc.text) else self.doc.text

        self.doc.delete_last(self.n)
        

    def undo(self):
        self.doc.insert(self.deleted_text)


class Editor:
    def __init__(self):
        self._undo_stack: List[Command]=[]
        self._redo_stack: List[Command]=[]

    def execute(self,cmd: Command):
        cmd.execute()
        self._undo_stack.append(cmd)
        self._redo_stack.clear()
    
    def undo(self):
        if not self._undo_stack:
            print("Nothing to undo")
            return
        cmd=self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)

    def redo(self):
        if not self._redo_stack:
            print("Nothing to redo")
            return
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
    
    def redo(self):
        if not self._redo_stack:
            print("Nothing to redo")
            return
        cmd=self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)

    def show_state(self):
        print(f"Document: '{self._undo_stack[-1].doc.text if self._undo_stack else 'empty'}'")


if __name__=="__main__":
    doc=TextDocument()
    editor=Editor()


    editor.execute(InsertCommand(doc,"Hello"))
    