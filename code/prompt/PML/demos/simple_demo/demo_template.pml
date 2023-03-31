-- Answer the following questions about the code snippet below.

{var:count=1}
{loop:incontext_samples}
-- Question {print:index+1}

Question: Write a {print:data(~.lang)} program that prints "Hello World!" to the console.
Code: {print:data(~.code)}

{var:count+=1}
{end}
-- Question {print:count}

Question: Write a {print:data(query_samples.lang)} program that prints "Hello World!" to the console.
Code: