from typing import Optional, Union
import os
import sys
ROOT_DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)
from keyword_enum import TagTypeEnum


DEFAULT_ERROR_VALUE = 2333

class BaseNode:
    LEFT_BRACE:str = '{'
    RIGHT_BRACE:str = '}'
    def __init__(self, father:'BaseNode'=None) -> None:
        self.father:Optional[BaseNode] = father
        self.current_data = None
        self.index:Optional[int] = None # Only used for loop
    
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
    def __init__(self, text_or_path:str, father:'BaseNode'=None) -> None:
        super().__init__(father)
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
    def __init__(self, text_or_path:str, father:'BaseNode'=None) -> None:
        super().__init__(father)
        self.text_or_path:str = text_or_path
    
    @property
    def PromptString(self):
        return self.text_or_path
    
    @property
    def DebugString(self):        
        return f"{BaseNode.LEFT_BRACE}{self.__class__.__name__}:{self.text_or_path}{BaseNode.RIGHT_BRACE}"
        
class EmptyNode(NonTerminalNode): # Used for empty Non-Terminal Node
    def __init__(self, text_or_path:str="", father:'BaseNode'=None) -> None:
        super().__init__(text_or_path, father)
        
class DataNode(TerminalNode):
    def __init__(self, text_or_path:str, father:'BaseNode'=None) -> None:
        super().__init__(text_or_path, father)
        
class PlainTextNode(TerminalNode):
    def __init__(self, text_or_path:str, father:'BaseNode'=None) -> None:
        super().__init__(text_or_path, father)

class CalculationNode(TerminalNode):
    def __init__(self, expression:str, father:'BaseNode'=None) -> None:
        super().__init__(expression, father)
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
    
    # For CalculationNode, use property "Index" , not field "index"
    # Will replace "INDEX" in expression with "Index" when "Index" is set
    @Index.setter
    def Index(self, value):
        self.index = value
        self.expression = self.expression.replace("INDEX", str(value))
    
    @property
    def DebugString(self):        
        return f"{BaseNode.LEFT_BRACE}{self.__class__.__name__}:={self.expression}={self.PromptString}:{BaseNode.RIGHT_BRACE}"
    
class AssignmentNode(CalculationNode):
    def __init__(self, assignment_expression:str, father:'BaseNode'=None) -> None:
        super().__init__(assignment_expression, father)
        self.split = assignment_expression.split("+=")
        if len(self.split) == 2:
            # is "+=", add variable name and '+' to the front of expression to change it from "+=" to "="
            self.split[1] = f"{self.split[0].strip()} + {self.split[1].strip()}"
        else:
            self.split = assignment_expression.split("-=")
            if len(self.split) == 2:
                # is "-=", add variable name and '-' to the front of expression to change it from "-=" to "="
                self.split[1] = f"{self.split[0].strip()} - {self.split[1].strip()}"
            else:
                self.split = assignment_expression.split("=")
        assert len(self.split) == 2, f"Assignment expression should be in format of 'variable_name [=, +=, -=] value', but got {assignment_expression}"
        self.variable_name = self.split[0].strip()
        self.expression = self.split[1].strip()
    
    # AssignmentNode will not output calculation result at prompt
    @property
    def PromptString(self):
        return ""
    
    @property
    def DebugString(self):        
        return f"{BaseNode.LEFT_BRACE}{self.__class__.__name__} {self.variable_name}:={self.expression}={self.PromptString}:{BaseNode.RIGHT_BRACE}"
    
class LoopNode(NonTerminalNode):
    def __init__(self, text_or_path:str, father:'BaseNode'=None) -> None:
        super().__init__(text_or_path, father)
        self.start_index:Optional[int] = None
        self.end_index:Optional[int] = None


def find_outer_paired_loop_end_index(decomposed_lst:list[tuple[TagTypeEnum, str]]):
    loop_stack = []
    for index, (keyword_type, text) in enumerate(decomposed_lst):
        if keyword_type == TagTypeEnum.LoopStart:
            loop_stack.append(text)
        elif keyword_type == TagTypeEnum.LoopEnd:
            loop_stack.pop()
            if len(loop_stack) == 0:
                return index
    return -1
    
def parse_children(node:NonTerminalNode, children_list:list[tuple[TagTypeEnum, str]]):
    if not isinstance(node, NonTerminalNode):
        return
    skips_index:list = []
    for index, (keyword_type, text) in enumerate(children_list):
        if index in skips_index:
            continue
        # Skip the loop end keyword
        if keyword_type == TagTypeEnum.LoopEnd:
            continue
        elif keyword_type == TagTypeEnum.Data:
            child_node = DataNode(father=node, text_or_path=text)
        elif keyword_type == TagTypeEnum.PlainText:
            child_node = PlainTextNode(father=node, text_or_path=text)
        elif keyword_type == TagTypeEnum.Calculation:
            child_node = CalculationNode(father=node, expression=text)
        elif keyword_type == TagTypeEnum.Assignment:
            child_node = AssignmentNode(father=node, assignment_expression=text)
        elif keyword_type == TagTypeEnum.LoopStart:
            child_node = LoopNode(father=node, text_or_path=text)
        node.children.append(child_node)
        if keyword_type == TagTypeEnum.LoopStart:
            loop_end_index = find_outer_paired_loop_end_index(children_list)
            skips_index.extend(range(index, loop_end_index+1))
            parse_children(child_node, children_list[index+1:loop_end_index])