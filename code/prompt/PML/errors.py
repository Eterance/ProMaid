

from pyparsing import Optional


class PMLBaseException(Exception):
    """Base class for all PML exceptions."""
    def __init__(self, line_number:int):
        self.line_number = line_number
        self._message:str = ""
    
    @property
    def Message(self):
        return f"{self.__class__.__name__} at Line {self.line_number}: {self._message}"
    
    def __repr__(self) -> str:
        return self.Message
    
    def __str__(self) -> str:
        return self.Message

class UnknownError(PMLBaseException):
    """Syntax error in PML file."""
    def __init__(self, line_number:int, original_exception:Exception):
        super().__init__(line_number)
        self.original_exception = original_exception
        
    @property
    def Message(self):
        return f"{self.__class__.__name__} at Line {self.line_number}: {self.original_exception}"

class SyntaxError(PMLBaseException):
    """Syntax error in PML file."""
    def __init__(self, line_number:int):
        super().__init__(line_number)
        
class SematicError(PMLBaseException):
    """Sematic error in PML file."""
    def __init__(self, line_number:int):
        super().__init__(line_number)
        
class LoopKeywordUnpairedError(SyntaxError):
    def __init__(self, line_number:int, unpaired_loop:str):
        super().__init__(line_number)
        self._message = unpaired_loop
        
class AssignReadOnlyError(SyntaxError):
    def __init__(self, line_number:int, variable_name:str):
        super().__init__(line_number)
        self._variable_name = variable_name
        
    @property
    def Message(self):
        return f'{self.__class__.__name__} at Line {self.line_number}: "{self._variable_name}" is read-only, cannot be assigned'
        
class VariableReferenceError(SematicError):
    def __init__(self, line_number:int, variable_name:str, extra_info:str=""):
        super().__init__(line_number)
        self._variable_name = variable_name
        self._extra_info = extra_info
        
    @property
    def Message(self):
        info = f'{self.__class__.__name__} at Line {self.line_number}: Undefined variable "{self._variable_name}"'
        if self._extra_info != "":
            info += f", {self._extra_info}"
        return info
    
class ExpressionEvaluationUnknownExceptionError(SematicError):
    def __init__(self, line_number:int, expression:str, original_exception:Exception):
        super().__init__(line_number)
        self._expression = expression
        self._original_exception = original_exception
        
    @property
    def Message(self):
        return f'{self.__class__.__name__} at Line {self.line_number}: Expression "{self._expression}", {self._original_exception}'
    
class PathNotFoundError(SematicError):
    def __init__(self, line_number:int, total_path:str, error_path:str, already_found_path:str):
        super().__init__(line_number)
        self._total_path = total_path
        self._error_path = error_path
        self._already_found_path = already_found_path
        
    @property
    def Message(self):
        return f'{self.__class__.__name__} at Line {self.line_number}: Path "{self._total_path}" not found, error path "{self._error_path}", already found path "{self._already_found_path}"'
    
class InvalidListIndexOrSlice(PathNotFoundError):
    pass
    
class ListOutOfIndexError(SematicError):
    def __init__(self, line_number:int, total_path:str, error_index:int, total_length:int, already_found_path:str):
        super().__init__(line_number)
        self._total_path = total_path
        self._error_index = error_index
        self._already_found_path = already_found_path
        self._total_length = total_length
        
    @property
    def Message(self):
        return f'{self.__class__.__name__} at Line {self.line_number}: Path "{self._total_path}" not found, {self._error_index} out of the index (total length {self._total_length}), already found path "{self._already_found_path}"'