from enum import Enum
import os
import sys
ROOT_DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)


class KeywordEnum(Enum):
    Data:str = "data"
    LoopStart:str = "loop"
    LoopEnd:str = "end"
    PlainText:str = "text"
    Calculation:str = "calc"
    Assignment:str = "var"
    Comment:str = "#"
    
class ReservedWordEnum(Enum):
    Index:str = "index"
    Reverse:str = "reverse"
    Len:str = "len"