import copy
from enum import Enum
import re
from typing import Optional, Union
import os
import sys

ROOT_DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)
from keyword_enum import KeywordEnum, ReservedWordEnum
from prompt_tree_node import AssignmentNode, BaseNode, DataNode, EmptyNode, CalculationNode, LoopNode, NonTerminalNode, parse_children
from errors import AssignReadOnlyError, ExpressionEvaluationUnknownExceptionError, InvalidListIndexOrSlice, ListOutOfIndexError, PathNotFoundError, UnknownError, VariableReferenceError

class PmlParser():     
    LEFT_BRACE:str = '{'
    RIGHT_BRACE:str = '}'
    DATA_PATTERN:str = f'\{LEFT_BRACE}{KeywordEnum.Data.value}[:.*?]?\{RIGHT_BRACE}'
    LOOP_START_PATTERN:str = f'\{LEFT_BRACE}({KeywordEnum.LoopStart.value}):(.*?)\{RIGHT_BRACE}'
    LOOP_END_PATTERN:str = f'\{LEFT_BRACE}{KeywordEnum.LoopEnd.value}\{RIGHT_BRACE}[\n]?'
    CALCULATION_PATTERN:str = f'\{LEFT_BRACE}{KeywordEnum.Calculation.value}:.*?\{RIGHT_BRACE}'
    ASSIGN_PATTERN:str = f'\{LEFT_BRACE}{KeywordEnum.Assignment.value}:.*?\{RIGHT_BRACE}[\n]?'
    
    KEYWORD_WITH_PATH_PATTERN:str = f'\{LEFT_BRACE}(.*?):(.*?)\{RIGHT_BRACE}'
    SINGLE_KEYWORD_PATTERN:str = f'\{LEFT_BRACE}(.*?)\{RIGHT_BRACE}'
    
    LENGTH_PATTERN:str = f"{ReservedWordEnum.Len.value}\(.*?\)"
    
    def __init__(self, template:str, is_clean_whitespace_at_the_end_of_lines:bool=False) -> None:
        self._original_template:str = template
        #self._template:str = self._remove_comments(template)
        self._template:str = template
        self._global_variable_dict:dict[str, Union[int, float]] = {}
        self._is_clean_whitespace = is_clean_whitespace_at_the_end_of_lines
        self.template_tree = self._parse_syntax_tree()
        
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
        if tag.strip().startswith(KeywordEnum.Comment.value):
            return KeywordEnum.Comment, tag
        elif (match := re.match(self.KEYWORD_WITH_PATH_PATTERN, tag)) is not None:
            keyword = match.group(1)
            path = match.group(2)
            if keyword == KeywordEnum.Data.value:
                return KeywordEnum.Data, path
            elif keyword == KeywordEnum.LoopStart.value:
                return KeywordEnum.LoopStart, path
            elif keyword == KeywordEnum.Calculation.value:
                return KeywordEnum.Calculation, path
            elif keyword == KeywordEnum.Assignment.value:
                return KeywordEnum.Assignment, path
            else:
                return KeywordEnum.PlainText, tag
        elif (match := re.match(self.SINGLE_KEYWORD_PATTERN, tag)) is not None:
            keyword = match.group(1)
            if keyword == KeywordEnum.LoopEnd.value:
                return KeywordEnum.LoopEnd, ""
            else:
                return KeywordEnum.PlainText, tag
        else:
            return KeywordEnum.PlainText, tag
        
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
        pattern = f'\{PmlParser.LEFT_BRACE}.*?\{PmlParser.RIGHT_BRACE}|[ \f\r\t\v]*#.*?$\n'
        processing = template
        result:list[str] = []
        while(True):
            # 使用正则表达式匹配所有的标签和文本
            matches = re.findall(pattern, processing, flags=re.MULTILINE)
            if len(matches) == 0:
                result.append(processing)
                break
            split_tag = matches[0]
            
            splits = processing.split(split_tag, 1)
            if splits[0] != '':
                result.append(splits[0])
            result.append(split_tag)
            processing = splits[1]
        return result
    
    def _preprocess_invisible_keywords(self, words_list:list[dict[str, int|str]]):
        for index, pack_dict in enumerate(words_list):
            line_number = pack_dict['line']
            word_type, _ = self._decompose_tag_as_keyword_and_path(pack_dict['word'])
            # loop-start, TagTypeEnum.LoopEnd, assignment will not appear in the prompt, called invisible keywords
            # They always appear as single line, so we need to remove the \n after them
            if word_type in [KeywordEnum.LoopStart, KeywordEnum.LoopEnd, KeywordEnum.Assignment]: 
                # If it is the last word, we don't need to remove the \n
                if index == len(words_list)-1:
                    continue
                else:
                    if words_list[index+1]['word'][0] == '\n':
                        words_list[index+1]['word'] = words_list[index+1]['word'][1:]
            elif word_type == KeywordEnum.Comment:
                if index == len(words_list)-1 or index == 0:
                    continue
                else:
                    # Comment behinds a sentence rather than stay at a single line alone
                    # Give the white space before the comment to the previous word
                    # and give the \n after the comment back to the previous word
                    if words_list[index-1]['word'][-1] != '\n':
                        if not words_list[index]['word'].startswith(KeywordEnum.Comment.value):
                            words_list[index-1]['word'] = words_list[index-1]['word'] + words_list[index]['word'].split(KeywordEnum.Comment.value)[0]
                        words_list[index-1]['word'] = words_list[index-1]['word'] + '\n'
                        words_list[index]['word'] = words_list[index]['word'].strip()
    
    def _clean_whitespace_at_the_end_of_lines(self, template:str):
        result:str = ''
        whitespace_cache:str = ''
        while len(template) > 0:
            char = template[0]
            template = template[1:]
            if char in [' ', '\f', '\t', '\v']:
                whitespace_cache += char
            elif char == '\n' or char == KeywordEnum.Comment.value:
                whitespace_cache = ''
                result += char
            else: # char is not whitespace
                result += whitespace_cache + char
                whitespace_cache = ''
        return result
    
    def _clean_empty_tokens(self, word_list_with_line_number:list[dict[str, int|str]]):
        new_list = []
        for word_dict in word_list_with_line_number:
            if word_dict['word'] != '':
                new_list.append(word_dict)
        return new_list
    
    def _get_data_via_path(self, path:str, data, index:int, line_number:int):
        total_path = path
        already_found_path:list[str] = []
        path_list = path.split('.')
        for path in path_list:
            _original_sub_path = path
            # Number-like
            if path.startswith('[') and path.endswith(']'):
                number_like = path[1:-1]
                if number_like == ReservedWordEnum.Index.value:
                    if index is None:
                        raise VariableReferenceError(line_number, ReservedWordEnum.Index.value, ", maybe you used it out of the loop")
                    number_like = str(index)
                # global variable
                elif number_like in self._global_variable_dict.keys(): 
                    number_like = str(self._global_variable_dict[number_like])
                try:
                    # Pure single number, like [20]
                    number = int(number_like)
                    data = data[number]
                except IndexError as ie:
                    raise ListOutOfIndexError(line_number, total_path, int(number_like), len(data), ".".join(already_found_path))
                except ValueError as ve:
                    is_reverse:bool = False
                    # reverse all list, like [REVERSE_KEYWORD]
                    if number_like == ReservedWordEnum.Reverse.value:                        
                        is_reverse = True
                    # list slice
                    else:
                        if ':' not in number_like:
                            raise InvalidListIndexOrSlice(line_number, total_path, _original_sub_path, ".".join(already_found_path))
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
                    try:
                        data = data[path]
                    except KeyError as ke:
                        raise PathNotFoundError(line_number, total_path, _original_sub_path, ".".join(already_found_path))
            already_found_path.append(_original_sub_path)
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
                        loop_list = self._get_data_via_path(current_child.path[2:], current_data, index, current_child.line_number)
                    # Absolute path
                    else:
                        loop_list = self._get_data_via_path(current_child.path, root_data, index, current_child.line_number)
                    assert isinstance(loop_list, list), f"Loop path {current_child.path} is not a list"
                    tree.children.pop(child_index)
                    # Copy len(loop_list) times, and insert them into the tree to replace the loop_start node
                    for loop_index, loop_item in enumerate(loop_list):
                        _empty_node = EmptyNode(line_number=current_child.line_number)
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
                        data = self._get_data_via_path(current_child.text_or_path[2:], current_data, index, current_child.line_number)
                    # Absolute path
                    else:
                        data = self._get_data_via_path(current_child.text_or_path, root_data, index, current_child.line_number)
                    current_child.text_or_path = str(data)
                elif isinstance(current_child, EmptyNode):
                    self._fill_data_to_sub_trees(current_child, current_data, root_data, index)
                elif type(current_child) is CalculationNode:
                    original_expression = current_child.expression
                    self._fill_calculation_node(current_child, current_data, root_data)
                    try:
                        current_child.evaluate()
                    except NameError as ne:
                        raise VariableReferenceError(current_child.line_number, ne.name)
                    except Exception as e:
                        raise ExpressionEvaluationUnknownExceptionError(current_child.line_number, original_expression, e)
                elif type(current_child) is AssignmentNode:
                    original_expression = current_child.expression
                    if current_child.variable_name == ReservedWordEnum.Index.value:
                        raise AssignReadOnlyError(current_child.line_number, ReservedWordEnum.Index.value)
                    self._fill_calculation_node(current_child, current_data, root_data)
                    # update global variable dict
                    try:
                        self._global_variable_dict[current_child.variable_name] = current_child.evaluate()
                    except NameError as ne:
                        raise VariableReferenceError(current_child.line_number, ne.name)
                    except Exception as e:
                        raise ExpressionEvaluationUnknownExceptionError(current_child.line_number, original_expression, e)
                child_index += 1
                
    def _fill_calculation_node(self, node:CalculationNode, current_data, root_data):
        # If expression has a "INDEX", Find a nearest ancestor node which has index
        node.expression = self._process_len_in_expression(node.expression, current_data, root_data, node.line_number)
        _tokens = self._split_expression_by_operators(node.expression)
        for token in _tokens:
            if ReservedWordEnum.Index.value == token:
                _nearest_ancient_index:Optional[int] = None
                _current_ancient_node:BaseNode = node.father
                while(_current_ancient_node is not None):
                    if _current_ancient_node.index is not None:
                        _nearest_ancient_index = _current_ancient_node.index
                        break
                    _current_ancient_node = _current_ancient_node.father
                assert _nearest_ancient_index is not None, r"Can't find index in ancestors. Maybe you use a INDEX keyword outside of a loop?"
                node.Index = _nearest_ancient_index
        # Now we got the value of index, replace the index in expression with value
        _replaced_tokens = []
        for token in _tokens:
            if token == ReservedWordEnum.Index.value:
                _replaced_tokens.append(str(node.Index))
                continue
            _replaced = self._replace_token_with_global_variables(token)
            _replaced_tokens.append(_replaced)
        node.expression = "".join(_replaced_tokens)
        
    def _split_expression_by_operators(self, expression:str): 
        pattern:str = r"\w+|\+|-|\*|/|%|//|\(|\)|\*\*"
        matches:list[str] = re.findall(pattern, expression)
        return matches
        
    def _replace_token_with_global_variables(self, token:str):
        # Replace Global Variable
        for var_key in self._global_variable_dict.keys():
            if var_key == token:
                var_value = self._global_variable_dict[var_key]
                return str(var_value)
        return token
    
    def _process_len_in_expression(self, expression:str, current_data, root_data, line_number:int):
        expression_copy = copy.deepcopy(expression)
        # Replace length
        matches:list[str] = re.findall(self.LENGTH_PATTERN, expression_copy)
        for match in matches:
            path = match.replace(ReservedWordEnum.Len.value, '')[1:-1]
            # Relative path
            if path.startswith('~.'):
                _list = self._get_data_via_path(path[2:], current_data, line_number)
            # Absolute path
            else:
                _list = self._get_data_via_path(path, root_data, line_number)
            length = len(_list)
            expression_copy = expression_copy.replace(match, str(length))
        return expression_copy
    
    def _mark_line_number(self, word_list:list[str]):
        line_number = 1
        result:list[dict[str, int|str]] = []
        for index, word in enumerate(word_list):
            word_copy = copy.deepcopy(word)
            old_line_number = line_number
            # if a word starts with '\n', its line number should be counted after these '\n'
            while (word_copy.startswith('\n')):
                line_number += 1
                word_copy = word_copy[1:]
                # if this word is all '\n', we go back to the old line number, equal to the previous word
                if word_copy == '':
                    line_number = old_line_number
                    word_copy = word
                    break
            result.append({"line": line_number, "word": word})
            line_number += word_copy.count('\n')
        return result
    
    def _parse_syntax_tree(self):
        if self._is_clean_whitespace:
            self._template = self._clean_whitespace_at_the_end_of_lines(self._template)
        word_list:list[str] = self._template_tokenize(self._template)
        word_list_with_line_number:list[dict[str, int|str]] = self._mark_line_number(word_list)
        self._preprocess_invisible_keywords(word_list_with_line_number)
        word_list_with_line_number = self._clean_empty_tokens(word_list_with_line_number)
        decomposed_word_list:list[tuple[int, tuple[KeywordEnum, str|None]]] = \
            [(pack['line'], self._decompose_tag_as_keyword_and_path(pack['word'])) for pack in word_list_with_line_number]
        root_node = EmptyNode()
        parse_children(root_node, decomposed_word_list)        
        return root_node
        
    def build_prompt(self, **data):
        tree = copy.deepcopy(self.template_tree)
        self._fill_data_to_sub_trees(tree, data, data, None)
        return tree.PromptString
