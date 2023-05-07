from enum import Enum

class KeywordEnum(Enum):
    Data:str = "data"
    LoopStart:str = "loop"
    LoopEnd:str = "end"
    PlainText:str = "text"
    Calculation:str = "calc"
    Assignment:str = "var"
    Comment:str = "#"
    Print:str = "print"
    
class ReservedWordEnum(Enum):
    Index:str = "index"
    Reverse:str = "reverse"
    Len:str = "len"

class TagPatternsEnum(Enum):
    LeftBrace:str = '{'
    RightBrace:str = '}'
    
    TagWithPath:str = f'\{LeftBrace}(.*?):(.*?)\{RightBrace}'
    Data:str = f'\{LeftBrace}{KeywordEnum.Data.value}[:.*?]?\{RightBrace}'
    LoopStart:str = f'\{LeftBrace}({KeywordEnum.LoopStart.value}):(.*?)\{RightBrace}'
    Calculation:str = f'\{LeftBrace}{KeywordEnum.Calculation.value}:.*?\{RightBrace}'
    Assign:str = f'\{LeftBrace}{KeywordEnum.Assignment.value}:.*?\{RightBrace}[\n]?'
    Print:str = f'\{LeftBrace}{KeywordEnum.Print.value}:.*?\{RightBrace}'    
    
    TagWithoutPath:str = f'\{LeftBrace}(.*?)\{RightBrace}'
    LoopEnd:str = f'\{LeftBrace}{KeywordEnum.LoopEnd.value}\{RightBrace}[\n]?'
    
class FunctionPatternsEnum(Enum):
    Length:str = f"{ReservedWordEnum.Len.value}\(.*?\)"
    Data:str = f"{KeywordEnum.Data.value}\(.*?\)"