from typing import Optional, Union

from .keyword_enum import KeywordEnum
from .Errors import LoopKeywordUnpairedError


DEFAULT_ERROR_VALUE = 2333

class BaseNode:
    LEFT_BRACE:str = '{'
    RIGHT_BRACE:str = '}'
    def __init__(self, father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        self.father:Optional[BaseNode] = father
        self.current_data = None
        self.index:Optional[int] = None # Only used for loop
        self.line_number:int = line_number
        self.is_processed:bool = False # Is already filled with data
        
    @property
    def Index(self):
        return self.index
    
    @Index.setter
    def Index(self, value):
        self.index = value
        
    @property
    def PromptString(self):
        return ""
    
    @property
    def DebugString(self):
        return f"{self.__class__.__name__}"
        
    def __repr__(self) -> str:
        return self.DebugString
    
    def __str__(self) -> str:
        return self.PromptString
    
class NonTerminalNode(BaseNode):
    def __init__(self, text_or_path:str, father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        super().__init__(father, line_number)
        self.path:str = text_or_path
        self.children:list[BaseNode] = []
    
    # Non-Terminal Node will not output own path
    @property
    def PromptString(self):
        description = ""
        for child in self.children:
            description = f"{description}{child.PromptString}"
        return description
    
    @property
    def DebugString(self):        
        description = f"{BaseNode.LEFT_BRACE}{self.__class__.__name__}:{self.path}{BaseNode.LEFT_BRACE}"
        for child in self.children:
            description = f"{description}{child.DebugString}"
        description = f"{description}{BaseNode.RIGHT_BRACE}{BaseNode.RIGHT_BRACE}"
        return description

class TerminalNode(BaseNode):
    def __init__(self, raw_text:str, father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        super().__init__(father, line_number)
        self.raw_text:str = raw_text
    
    @property
    def PromptString(self):
        return self.raw_text
    
    @property
    def DebugString(self):        
        return f"{BaseNode.LEFT_BRACE}{self.__class__.__name__}:{self.raw_text}{BaseNode.RIGHT_BRACE}"
        
class EmptyNode(NonTerminalNode): # Used for empty Non-Terminal Node
    def __init__(self, text_or_path:str="", father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        super().__init__(text_or_path, father, line_number)
        
class DataNode(TerminalNode):
    def __init__(self, text_or_path:str, father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        super().__init__(text_or_path, father, line_number)
        
class PlainTextNode(TerminalNode):
    def __init__(self, text_or_path:str, father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        super().__init__(text_or_path, father, line_number)

class CalculationNode(TerminalNode):
    def __init__(self, expression:str, father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        super().__init__(expression, father, line_number)
        self.expression = expression
    
    def evaluate(self):
        result:Union[int, float] = eval(self.expression)
        return result
    
    @property
    def PromptString(self):
        try:
            return str(self.evaluate())
        except ValueError as ve:
            return str(DEFAULT_ERROR_VALUE)
    
    @property
    def Index(self):
        if self.index is None:
            return DEFAULT_ERROR_VALUE
        return self.index
    
    @Index.setter
    def Index(self, value):
        self.index = value
    
    @property
    def DebugString(self):
        return f"{BaseNode.LEFT_BRACE}{self.__class__.__name__}:={self.expression}={self.PromptString}:{BaseNode.RIGHT_BRACE}"
    
class AssignmentNode(CalculationNode):
    def __init__(self, raw_text:str, father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        super().__init__(raw_text, father, line_number)
        self.split = raw_text.split("+=")
        if len(self.split) == 2:
            # is "+=", add variable name and '+' to the front of expression to change it from "+=" to "="
            self.split[1] = f"{self.split[0].strip()} + {self.split[1].strip()}"
        else:
            self.split = raw_text.split("-=")
            if len(self.split) == 2:
                # is "-=", add variable name and '-' to the front of expression to change it from "-=" to "="
                self.split[1] = f"{self.split[0].strip()} - {self.split[1].strip()}"
            else:
                self.split = raw_text.split("=")
        assert len(self.split) == 2, f"Assignment expression should be in format of 'variable_name [=, +=, -=] value', but got {raw_text}"
        self.variable_name = self.split[0].strip()
        self.expression = self.split[1].strip()
    
    # AssignmentNode will not output calculation result at prompt
    @property
    def PromptString(self):
        return ""
    
    @property
    def DebugString(self):        
        return f"{BaseNode.LEFT_BRACE}{self.__class__.__name__} {self.variable_name}:={self.expression}={self.PromptString}:{BaseNode.RIGHT_BRACE}"
    
class PrintNode(TerminalNode):
    # Warning: Although PrintNode has DataNode, CalculationNode and AssignmentNode 's properties, it is not a subclass of them
    # Cause multiple inheritance is confusing
    # And unlike those Node, PrintNode's properties are not set in parsing stage
    # Instead, they are set in data-filling stage
    def __init__(self, raw_text:str, father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        super().__init__(raw_text, father, line_number)
        self.data_path:Optional[str] = None
        self.expression:Optional[str] = None
        self.split:Optional[str] = None
        self.variable_name:Optional[str] = None
        self.final_value:Optional[str] = None
    
    def evaluate(self):
        if self.expression is not None:
            result:Union[int, float] = eval(self.expression)
        else:
            result = DEFAULT_ERROR_VALUE
        return result
    
    @property
    def PromptString(self):
        try:
            return self.final_value
        except ValueError as ve:
            return str(DEFAULT_ERROR_VALUE)
    
    @property
    def Index(self):
        if self.index is None:
            return DEFAULT_ERROR_VALUE
        return self.index
    
    @Index.setter
    def Index(self, value):
        self.index = value
    
    @property
    def DebugString(self):        
        return f"{BaseNode.LEFT_BRACE}{self.__class__.__name__} (processed:{self.is_processed}):={self.raw_text}={self.PromptString}:{BaseNode.RIGHT_BRACE}"
    
class LoopNode(NonTerminalNode):
    def __init__(self, text_or_path:str, father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        super().__init__(text_or_path, father, line_number)
        self.start_index:Optional[int] = None
        self.end_index:Optional[int] = None
        
class CommentNode(TerminalNode):
    def __init__(self, comment:str, father:Optional['BaseNode']=None, line_number:int=-1) -> None:
        super().__init__(comment, father, line_number)
    
    @property
    def PromptString(self):
        return ""
    
def find_outer_paired_loop_end_index(decomposed_lst:list[tuple[int, tuple[KeywordEnum, str]]]):
    loop_start_stack:list[tuple[int, tuple[KeywordEnum, str]]] = []
    found_index = -1
    for index, element in enumerate(decomposed_lst):
        (line_number, (keyword_type, text)) = element
        if keyword_type == KeywordEnum.LoopStart:
            loop_start_stack.append(element)
        elif keyword_type == KeywordEnum.LoopEnd:
            if len(loop_start_stack) == 0:
                raise LoopKeywordUnpairedError(line_number, '{'+KeywordEnum.LoopEnd.value+'}')
            else:
                loop_start_stack.pop()
            if len(loop_start_stack) == 0:
                found_index = index
    if len(loop_start_stack) != 0:
        line_number = loop_start_stack[0][0]
        text = loop_start_stack[0][1][1]
        raise LoopKeywordUnpairedError(line_number, '{'+f"{KeywordEnum.LoopStart.value}:{text}"+'}')
    return found_index
    
def parse_children(node:BaseNode, children_list:list[tuple[int, tuple[KeywordEnum, str]]]):
    if not isinstance(node, NonTerminalNode):
        return
    # Only NonTerminalNode can have children
    skips_index:list = []
    for index, (line_number, (keyword_type, text)) in enumerate(children_list):
        if index in skips_index:
            continue
        # Skip the loop end keyword, it will not appear in the tree
        if keyword_type == KeywordEnum.LoopEnd:
            continue
        elif keyword_type == KeywordEnum.Data:
            child_node:BaseNode = DataNode(father=node, text_or_path=text, line_number=line_number)
        elif keyword_type == KeywordEnum.PlainText:
            child_node = PlainTextNode(father=node, text_or_path=text, line_number=line_number)
        elif keyword_type == KeywordEnum.Calculation:
            child_node = CalculationNode(father=node, expression=text, line_number=line_number)
        elif keyword_type == KeywordEnum.Assignment:
            child_node = AssignmentNode(father=node, raw_text=text, line_number=line_number)
        elif keyword_type == KeywordEnum.Print:
            child_node = PrintNode(father=node, raw_text=text, line_number=line_number)
        elif keyword_type == KeywordEnum.LoopStart:
            child_node = LoopNode(father=node, text_or_path=text, line_number=line_number)
        elif keyword_type == KeywordEnum.Comment:
            child_node = CommentNode(father=node, comment=text, line_number=line_number)
        node.children.append(child_node)
        if keyword_type == KeywordEnum.LoopStart:
            loop_end_index = find_outer_paired_loop_end_index(children_list)
            skips_index.extend(range(index, loop_end_index+1))
            parse_children(child_node, children_list[index+1:loop_end_index])