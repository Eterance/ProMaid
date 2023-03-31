-- This template will show you full potential of PML.

{var:index1 = 0}
{var:total = 0}
total2 = {print:total2 = 2}
int((total2+7)/3) = {print:int((total2+7)/3)}
{loop:incontext_samples.[:int((total2+7)/3)]}
-- Question {calc:index+1}
-- Random {calc:data(~.random_int)}
This is Print (total += data(~.random_int)): {print:total += data(~.random_int)}
-- Random + 20: {calc:int(data(~.random_int))+20}
# 注释
#这也是注释
 #这照样是注释

Question (ABS): {data:incontext_samples.[index1].interaction.[0].utterance}
Question (REL): {print:data(~.interaction.[0].utterance)}      # 这还是注释
Question (REL)2: {data:~.interaction.[0].utterance}
Answer: Let's think step by step.
{loop:~.interaction}
index == {calc:index}
index1 == {calc:index1}
Step {print:index+index1} Question: {data:~.utterance}
Step {calc:index-index1} SQL: {data:~.query}
{end}
According the analysis above, the final SQL is: {data:~.final.query}
{var:index1 += 1}

{end}
-- Question {calc:index1+1}     

Question: {data:input}     
Answer: Let's think step by step.
This is Print (total): {print:total}
