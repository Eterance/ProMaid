import json
import os
import random
import sys
ROOT_DIR = os.path.join(os.path.dirname(__file__), "../../")
sys.path.append(ROOT_DIR)
from pml_parser import PmlParser

template_file  = os.path.join(ROOT_DIR, "demos\harder_demo\sparc_sub_dataset.pml")
template:str = open(template_file, 'r', encoding='utf-8').read()
with open('demos\harder_demo\sparc_dev_[389, 19, 141, 329, 344, 126, 59, 46, 199, 147].json') as file:
    test_data = json.load(file)
apb = PmlParser(template, is_clean_whitespace_at_the_end_of_lines=True)

for data in test_data:
    data['random_int'] = str(random.randint(0, 100))
prompt = apb.build_prompt(incontext_samples=test_data, question_index=666, input="Will it succeed?")
print(prompt)
