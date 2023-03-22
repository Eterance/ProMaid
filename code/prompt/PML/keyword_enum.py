from enum import Enum
import os
import sys
ROOT_DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)


class TagTypeEnum(Enum):
    Data:str = "DATA"
    LoopStart:str = "LOOP-START"
    LoopEnd:str = "LOOP-END"
    PlainText:str = "PLAIN-TEXT"
    Calculation:str = "CALC"
    Assignment:str = "ASSIGN"