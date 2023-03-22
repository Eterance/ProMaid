import copy
from enum import Enum
import re
from typing import Optional, Union
import os
import sys
ROOT_DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)
from keyword_enum import TagTypeEnum
from prompt_tree_node import AssignmentNode, BaseNode, DataNode, EmptyNode, CalculationNode, LoopNode, NonTerminalNode, parse_children

class PmlParser():     
    LEFT_BRACE:str = '{'
    RIGHT_BRACE:str = '}'
    DATA_PATTERN:str = f'\{LEFT_BRACE}{TagTypeEnum.Data.value}[:.*?]?\{RIGHT_BRACE}'
    LOOP_START_PATTERN:str = f'\{LEFT_BRACE}({TagTypeEnum.LoopStart.value}):(.*?)\{RIGHT_BRACE}'
    LOOP_END_PATTERN:str = f'\{LEFT_BRACE}{TagTypeEnum.LoopEnd.value}\{RIGHT_BRACE}[\n]?'
    CALCULATION_PATTERN:str = f'\{LEFT_BRACE}{TagTypeEnum.Calculation.value}:.*?\{RIGHT_BRACE}'
    ASSIGN_PATTERN:str = f'\{LEFT_BRACE}{TagTypeEnum.Assignment.value}:.*?\{RIGHT_BRACE}[\n]?'
    
    KEYWORD_WITH_PATH_PATTERN:str = f'\{LEFT_BRACE}(.*?):(.*?)\{RIGHT_BRACE}'
    SINGLE_KEYWORD_PATTERN:str = f'\{LEFT_BRACE}(.*?)\{RIGHT_BRACE}'
    
    LENGTH_KEYWORD:str = "len"
    LENGTH_PATTERN:str = f"{LENGTH_KEYWORD}\(.*?\)"
    REVERSE_KEYWORD:str = "REVERSE"
    INDEX_KEYWORD:str = 'INDEX'
    
    def __init__(self, template:str) -> None:
        self._original_template:str = template
        self._template:str = self._remove_comments(template)
        self.template_tree = self._parse_syntax_tree()
        self._global_variable_dict:dict[str, Union[int, float]] = {}
        
    @property
    def template(self):
        return self._template
    
    @property
    def original_template(self):
        return self._original_template
    
    def _decompose_tag_as_keyword_and_path(self, tag:str): 
        """
        Given a tag, return the keyword and the path of the tag. If not a tag, return the tag itself.

        Args:
            tag (str): tag, e.g. [KEYWORDS:attribute1.attribute2.attribute3]

        Returns:
            KeywordEnum: Indicate the type of the tag.
            str: The path of the tag. If the tag is a single keyword, the path will be None. If it is a plain text rather a tag, the path will be the plain text.
        """
        if (match := re.match(self.KEYWORD_WITH_PATH_PATTERN, tag)) is not None:
            keyword = match.group(1)
            path = match.group(2)
            if keyword == TagTypeEnum.Data.value:
                return TagTypeEnum.Data, path
            elif keyword == TagTypeEnum.LoopStart.value:
                return TagTypeEnum.LoopStart, path
            elif keyword == TagTypeEnum.Calculation.value:
                return TagTypeEnum.Calculation, path
            elif keyword == TagTypeEnum.Assignment.value:
                return TagTypeEnum.Assignment, path
            else:
                return TagTypeEnum.PlainText, tag
        elif (match := re.match(self.SINGLE_KEYWORD_PATTERN, tag)) is not None:
            keyword = match.group(1)
            if keyword == TagTypeEnum.LoopEnd.value:
                return TagTypeEnum.LoopEnd, None
            else:
                return TagTypeEnum.PlainText, tag
        else:
            return TagTypeEnum.PlainText, tag
        
    def _remove_comments(self, template: str) -> str:
        lines = template.split("\n")
        new_lines = []
        for line in lines:
            if line.lstrip().startswith("#"):
                continue
            new_lines.append(line)
        return "\n".join(new_lines)
    
    def _template_tokenize(self, template:str):
        # 匹配所有的标签，以及它们前后的文本
        pattern = f'\{PmlParser.LEFT_BRACE}.*?\{PmlParser.RIGHT_BRACE}'
        processing = template
        result:list[str] = []
        while(True):
            # 使用正则表达式匹配所有的标签和文本
            matches = re.findall(pattern, processing)
            if len(matches) == 0:
                result.append(processing)
                break
            split_tag = matches[0]
            
            splits = processing.split(split_tag, 1)
            result.append(splits[0])
            result.append(split_tag)
            processing = splits[1]
        return result
    
    def _preprocess_invisible_keywords(self, words_list:list[str]):
        for index, word in enumerate(words_list):
            word_type, _ = self._decompose_tag_as_keyword_and_path(word)
            # loop-start, TagTypeEnum.LoopEnd, assignment will not appear in the prompt, called invisible keywords
            # They always appear as single line, so we need to remove the \n after them
            if word_type in [TagTypeEnum.LoopStart, TagTypeEnum.LoopEnd, TagTypeEnum.Assignment]: 
                # If it is the last word, we don't need to remove the \n
                if index == len(words_list)-1:
                    continue
                else:
                    if words_list[index+1][0] == '\n':
                        words_list[index+1] = words_list[index+1][1:]
                        
    def _get_data_via_path(self, path:str, data, index:int):
        path_list = path.split('.')
        for path in path_list:
            # Number-like
            if path.startswith('[') and path.endswith(']'):
                number_like = path[1:-1]
                if number_like == PmlParser.INDEX_KEYWORD:
                    assert index is not None, f"INDEX keyword can only be used in loop. Path: {path}"
                    number_like = str(index)
                elif number_like in self._global_variable_dict.keys(): 
                    number_like = str(self._global_variable_dict[number_like])
                try:
                    # Pure single number, like [20]
                    number = int(number_like)
                    data = data[number]
                except ValueError as ve:
                    is_reverse:bool = False
                    # reverse all list, like [REVERSE_KEYWORD]
                    if number_like == PmlParser.REVERSE_KEYWORD:                        
                        is_reverse = True
                    # list slice
                    else:
                        if ':' not in number_like:
                            raise ValueError(f"Invalid list index: [{number_like}]")
                        _split = number_like.split(":")
                        start_index_str = _split[0]
                        end_index_str = _split[1]
                        # left is empty, like [:3]
                        if start_index_str == '':
                            end_index = int(end_index_str)
                            data = data[:end_index]
                        # right is empty, like [2:]
                        elif end_index_str == '': 
                            start_index = int(start_index_str)
                            data = data[start_index:]
                        # Range, like [2:3]
                        else:
                            start_index = int(start_index_str)
                            end_index = int(end_index_str)
                            # if start_index > end_index, will reverse the list
                            if start_index > end_index:
                                start_index, end_index = end_index+1, start_index+1
                                is_reverse = True
                            data = data[start_index:end_index]
                    if is_reverse:                       
                        data = list(reversed(data))
            # just text, means the path is a dict
            else:
                # Empty path, meaning use the entire data
                if path == "":
                    pass
                # 
                else:
                    assert isinstance(data, dict), f"""path "{path}" is not dict"""
                    data = data[path]
        return data
    
    # Pre-order fill data to tree
    def _fill_data_to_sub_trees(self, tree:BaseNode, current_data, root_data, index:int=None):
        tree.current_data = current_data
        if isinstance(tree, NonTerminalNode):
            child_index = 0
            while child_index < len(tree.children):
                current_child = tree.children[child_index]        
                if isinstance(current_child, LoopNode):
                    # Relative path
                    if current_child.path.startswith('~.'):
                        loop_list = self._get_data_via_path(current_child.path[2:], current_data, index)
                    # Absolute path
                    else:
                        loop_list = self._get_data_via_path(current_child.path, root_data, index)
                    assert isinstance(loop_list, list), f"Loop path {current_child.path} is not a list"
                    tree.children.pop(child_index)
                    # Copy len(loop_list) times, and insert them into the tree to replace the loop_start node
                    for loop_index, loop_item in enumerate(loop_list):
                        _empty_node = EmptyNode()
                        _empty_node.children = copy.deepcopy(current_child.children)
                        _empty_node.father = tree
                        # Give a new father to all children
                        for _empty_node_child in _empty_node.children:
                            _empty_node_child.father = _empty_node
                        _empty_node.index = loop_index # index in loop, will be used in IndexNode
                        tree.children.insert(child_index, _empty_node)
                        child_index += 1
                        # fill sub tree data
                        self._fill_data_to_sub_trees(_empty_node, loop_item, root_data, loop_index)
                elif isinstance(current_child, DataNode):
                    # Relative path
                    if current_child.text_or_path.startswith('~.'):
                        data = self._get_data_via_path(current_child.text_or_path[2:], current_data, index)
                    # Absolute path
                    else:
                        data = self._get_data_via_path(current_child.text_or_path, root_data, index)
                    current_child.text_or_path = str(data)
                elif isinstance(current_child, EmptyNode):
                    self._fill_data_to_sub_trees(current_child, current_data, root_data, index)
                elif type(current_child) is CalculationNode:
                    self._fill_calculation_node(current_child, current_data, root_data)
                elif type(current_child) is AssignmentNode:
                    self._fill_calculation_node(current_child, current_data, root_data)
                    # update global variable dict
                    try:
                        self._global_variable_dict[current_child.variable_name] = current_child.evaluate()
                    except Exception as e:
                        raise Exception(f"""Assign Fail, maybe you use a variable which is not defined yet? Current expression: "{current_child.expression}" """)
                child_index += 1
                
    def _fill_calculation_node(self, node:CalculationNode, current_data, root_data):
        # If expression has a "INDEX", Find a nearest ancestor node which has index
        if PmlParser.INDEX_KEYWORD in node.expression:
            _nearest_ancient_index:Optional[int] = None
            _current_ancient_node:BaseNode = node.father
            while(_current_ancient_node is not None):
                if _current_ancient_node.index is not None:
                    _nearest_ancient_index = _current_ancient_node.index
                    break
                _current_ancient_node = _current_ancient_node.father
            assert _nearest_ancient_index is not None, r"Can't find index in ancestors. Maybe you use a INDEX keyword outside of a loop?"
            node.Index = _nearest_ancient_index
        node.expression = self._process_expression(node.expression, current_data, root_data)
                
    def _process_expression(self, expression:str, current_data, root_data):
        expression_copy = copy.deepcopy(expression)
        # Replace Global Variable
        for var_key in self._global_variable_dict.keys():
            if var_key in expression_copy:
                var_value = self._global_variable_dict[var_key]
                expression_copy = expression_copy.replace(var_key, str(var_value))
        # Replace length
        matches:list[str] = re.findall(self.LENGTH_PATTERN, expression_copy)
        for match in matches:
            path = match.replace(PmlParser.LENGTH_KEYWORD, '')[1:-1]
            # Relative path
            if path.startswith('~.'):
                _list = self._get_data_via_path(path[2:], current_data)
            # Absolute path
            else:
                _list = self._get_data_via_path(path, root_data)
            length = len(_list)
            expression_copy = expression_copy.replace(match, str(length))
        return expression_copy
    
    def _parse_syntax_tree(self):
        word_list = self._template_tokenize(self._template)
        self._preprocess_invisible_keywords(word_list)
        decomposed_word_list:list[tuple[TagTypeEnum, str|None]] = [self._decompose_tag_as_keyword_and_path(word) for word in word_list]
        root_node = EmptyNode()
        parse_children(root_node, decomposed_word_list)        
        return root_node
        
    def build_prompt(self, **data):
        tree = copy.deepcopy(self.template_tree)
        self._fill_data_to_sub_trees(tree, data, data, None)
        return tree.PromptString
