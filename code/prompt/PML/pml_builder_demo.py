import json
import os
import sys
from pml_parser import PmlParser


incontext_samples = \
[
    {
        "lang": "C#",
        "code": "public class Test { public static void Main() { Console.WriteLine(\"Hello World!\"); } }"
    },
    {
        "lang": "C",
        "code": "int main() { printf(\"Hello World!\"); return 0; }"
    },
    {
        "lang": "Visual Basic",
        "code": "Module Module1 Sub Main() Console.WriteLine(\"Hello World!\") End Sub End Module"
    }
]

query_samples = \
{
    "lang": "Python",
    "code": "print(\"Hello World!\")"
}

prompt = "-- Answer the following questions about the code snippet below.\n\n"
count = 1
for index, sample in enumerate(incontext_samples):
    prompt += f"-- Question {count}\n\n"
    prompt += f"Question: Write a {sample['lang']} program that prints \"Hello World!\" to the console.\n"
    prompt += f"Code: {sample['code']}\n\n"
    count += 1
prompt += f"-- Question {count}\n\n"
prompt += f"Question: Write a {query_samples['lang']} program that prints \"Hello World!\" to the console.\n"
prompt += f"Code:"
#print(prompt)

template:str = open(r"demo_template.txt", 'r', encoding='utf-8').read()
apb = PmlParser(template, is_clean_whitespace_at_the_end_of_lines=True)
prompt = apb.build_prompt(incontext_samples=incontext_samples, query_samples=query_samples)
print(prompt)
