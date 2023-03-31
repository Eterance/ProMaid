import json
import os
import random
import sys
CODE_DIR = os.path.join(os.path.dirname(__file__), "../../")
ROOT_DIR = os.path.join(CODE_DIR, "../")
sys.path.append(CODE_DIR)
sys.path.append(ROOT_DIR)
from prompt.PML.pml_parser import PmlParser
from utils.file_operations import load_variable_from_json_file, save_variable_to_json_file

template_file  = os.path.join(ROOT_DIR, "code/templates/advanced_template_sparc_test.txt")
#template_file  = os.path.join(ROOT_DIR, "code/templates/advanced_template_test2.txt")
template:str = open(template_file, 'r', encoding='utf-8').read()
test_data = load_variable_from_json_file(r'F:\Programs3\Deep_Learning_Repo\text2sql\code\unit_test\prompt\sparc_dev_[389, 19, 141, 329, 344, 126, 59, 46, 199, 147].json')
apb = PmlParser(template, is_clean_whitespace_at_the_end_of_lines=True)
#print(apb.template_tree)

sss = apb._split_expression_by_operators("2 + 3 + 6 / 20 + index + ( 5 + 9 )")
ssr = "".join(sss)
#print(sss)

for data in test_data:
    data['random_int'] = str(random.randint(0, 100))
prompt = apb.build_prompt(incontext_samples=test_data, question_index=666, input="Will it succeed?")
#test_data = [1,2,3]
#prompt = apb.build_prompt(incontext_samples=test_data, input="Will it succeed?")
print(prompt)
