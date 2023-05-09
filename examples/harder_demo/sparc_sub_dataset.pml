-- This template will show you full potential of ProMaid Language.

@{index1 = 0}
@{total = 0}
total2 = @{print(total2 = 2)}
int((total2+7)/3) = @{print(int((total2+7)/3))}
{This is a fake code, with no @ at the first}
@@{Use a @ to escape @ (pretty like razor grammar)}
@{for index, item in incontext_samples[:int((total2+7)/3)]}
-- Question {print(index+1)}
-- Random {print(item[random_int])}
This is Print @@{print(item[random_int])}: @{print(item[random_int])}
-- Random + 20: @{print(int(data(~.random_int))+20)}
# 注释
#这也是注释
 #这照样是注释

Question (ABS): @{print(incontext_samples[index1]['interaction'][0]['utterance'])}
Question (REL): @{print(item["interaction"][0]["utterance"])}      # 这还是注释
Answer: Let's think step by step.
    @{for index2, item2 in interaction}
index == @{print(index2)}
index1 == @{print(index1)}
Step @{print(index2+index1)} Question: @{print(item2["utterance"])}
Step @{print(index2-index1)} SQL: @{print(item2["query"])}
    {end}
According the analysis above, the final SQL is: @{print(item["final"]["query"])}
@{index1 += 1}

{end}
-- Question @{print(index1+1)}     

Question: @{print(input)}     
Answer: Let's think step by step.
This is Print (total): @{print(total)}
