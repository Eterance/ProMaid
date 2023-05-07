# ProMaid Language

## 这有什么用？

Prompt 的构建一般使用代码（如 Python） 的字符串拼接。

这样的缺点是：

- 构建时不够直观，不能直接看到 Template / Prompt 长什么样；
- 换行的处理非常麻烦；
- 想要修改 Template 就要修改代码，一不小心容易改错。

使用 **ProMaid Language**（以下简称 **PML** ），你可以将 Template 的构建与主代码分离，并且能直观地构建它———事实上，写 PML 就是在写一个文本文件，而不是费力地做字符串拼接。

---

## 一个例子

> 以下示例可以在文件 [pml_builder_demo.py](demos\simple_demo\pml_builder_demo.py) 中找到。

现在你手头有这样一份数据：

```python
# 3 个上下文样本
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
# 1 个输入，这里的 code 是 Ground-Truth
query_samples = \
{
    "lang": "Python",
    "code": "print(\"Hello World!\")"
}
```

请注意，虽然这份数据有 3 个上下文样本，但是应该假定你不知道 `incontext_samples` 数组里有多少个元素，你只知道单个元素里面有 `"lang"` 和 `"code"`。

你想构造出下面的 Prompt：

>-- Answer the following questions about the code snippet below.
>
>-- Question 1  
>
>Question: Write a C# program that prints "Hello World!" to the console.  
Code: public class Test { public static void Main() { Console.WriteLine("Hello World!"); } }  
>
>-- Question 2  
>
>Question: Write a C program that prints "Hello World!" to the console.  
Code: int main() { printf("Hello World!"); return 0; }  
>
>-- Question 3  
>
>Question: Write a Visual Basic program that prints "Hello World!" to the console.  
Code: Module Module1 Sub Main() Console.WriteLine("Hello World!") End Sub End Module  
>
>-- Question 4  
>
>Question: Write a Python program that prints "Hello World!" to the console.  
Code:

如果使用 Python ，代码会是这样的：

```python
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
```

看起来并不是很直观。那么怎么改成使用 PML 呢？

首先，构造 PML 文件。假设你将其保存到了 [demo_template.pml](demos\simple_demo\demo_template.pml) 中。

我们先弄一个上下文样本的枚举/循环：

```python
-- Answer the following questions about the code snippet below.

# 枚举 incontext_samples 里面的元素
{loop:incontext_samples}
-- Question {print:index+1}

Question: Write a {print:data(~.lang)} program that prints "Hello World!" to the console.
Code: {print:data(~.code)}

# 结束循环体
{end}
```

然后添加其他部分：

```python
-- Answer the following questions about the code snippet below.

# 定义一个全局变量 count
{var:count=1}
# 枚举 incontext_samples 里面的元素
{loop:incontext_samples}
-- Question {print:index+1}

Question: Write a {print:data(~.lang)} program that prints "Hello World!" to the console.
Code: {print:data(~.code)}

# 全局变量 count 自增 1
{var:count+=1}
# 结束循环体
{end}
-- Question {print:count}

Question: Write a {print:data(query_samples.lang)} program that prints "Hello World!" to the console.
Code:
```

>有关 PML 的语法，请参阅 [PML 语法手册](PML语法手册.md)。

最后，运行 [pml_builder_demo.py](demos\simple_demo\pml_builder_demo.py)：

得到的 Prompt 应该和使用 Python 字符串拼接的一致。

---

## 错误处理

PML Parser 拥有完善的错误提示系统。

为了演示如何处理错误，我们将上一步的 demo 中的 template 第 7 行的 `{print:data(~.lang)}` 改为 `{print:data(~.language)}`。

```python
-- Answer the following questions about the code snippet below.

{var:count=1}
{loop:incontext_samples}
-- Question {print:index+1}

Question: Write a {print:data(~.language)} program that prints "Hello World!" to the console.
Code: {print:data(~.code)}

{var:count+=1}
{end}
-- Question {print:count}

Question: Write a {print:data(query_samples.lang)} program that prints "Hello World!" to the console.
Code:
```

运行 [pml_builder_demo.py](demos\simple_demo\pml_builder_demo.py) ，Python 控制台会提示类似下面的错误：

```python
PathNotFoundError at Line 7: Path "language" not found, error path "language", already found path ""
```

错误提示告诉我们，template 的第 7 行有误：找不到叫 `language` 的数据名称————实际上，正确的名称是 `lang`。

---

## PML Parser 怎么把 template 构建为 prompt 的？

1. 构造函数 `PmlParser()` 输入 PML ，分词并判断每一块片段的类型。
2. 构造语法树。
3. `PmlParser.build_prompt()` 输入数据，前序遍历语法树，为每个非空结点填充对应的数据。
4. 数据填充完成后，前序遍历所有非终结符，得到 Prompt。
