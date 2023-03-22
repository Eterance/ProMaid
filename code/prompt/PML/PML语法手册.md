# Prompt Markup Language 语法手册

## 标签

### 标签的识别与结构

标签用大括号括起来，如：`{ASSIGN:index1 = 0}`。标签内部结构为 `{关键词:数据}`。

### 所有关键词

#### 赋值 `ASSIGN`

`{ASSIGN:变量名 赋值符号 计算式}`，如 `{ASSIGN:index1 = 0}` 是为变量 `index1` 赋值 `0`。如果被赋值的变量尚不存在会被创建（自增自减时除外）。

创建的变量可用于计算式中，也能用作访问数据的路径下标。 如果用作路径下标的变量不存在于上下文中，将会报错。

```python
{ASSIGN:var1 = 23}
{ASSIGN:var2 = var1 * 2}
{ASSIGN:var2 -= 6}
# 此时 var2 == 40
# 下面这句不可以，因为变量 var3 未声明
# {ASSIGN:var2 = var3}
# 下面这句不可以，因为变量 var4 未声明，不能自增自减
# {ASSIGN:var4 += 2}
{DATA:~.A.B.[var2].C} # 用作路径下标
```

**创建的变量在 template 的全局范围生效**。也就是说，即使变量定义在循环体内部，在循环体外也能访问该变量。**使用自增自减时要特别注意。**

赋值符号支持 `=`，`+=`，`-=`。

计算式可以使用 `int(计算式)` 或者 `float(计算式)` 将计算式的结果取整或者转为小数。

赋值是隐形标签，意味着计算式的值不会最终被合成到 Prompt 中，即 `{ASSIGN:变量名 赋值符号 计算式}` 会被空字符串 `''` 替换。

**请将 `{ASSIGN:变量名 赋值符号 计算式}` 放在单独的一行。**

#### 计算 `CALC`

`{CALC:计算式}`，计算式计算的结果会替换掉本标签。如：

```python
{ASSIGN:var1 = 23}
{CALC:var1 * 2}
# 标签 {CALC:var1 * 2} 会被 46 替换
```

#### 数据 `DATA`

`{DATA:路径}`，根据路径得到的数据将替换本标签。

例如，路径 `A.B` 有元素 `[1, 2, 7]`，而 template 为

```python
{DATA:A.B.[2]}
{DATA:A.B.[0]};{DATA:A.B.[1]}
```

处理后的 prompt 为

```python
7
1;2
```

#### 循环 `LOOP-START` `LOOP-END`

使用 `{LOOP-START:路径}` 标记循环体开始，`{LOOP-END}` 标记循环体的结束。如：

```python
{LOOP-START:路径}
循环体
{LOOP-END}
```

`{LOOP-START:路径}` 会把自己下属的循环体的上下文数据改为路径所指的数据。

循环体复制的次数等于路径对应的数据（列表）内的元素数量。换句话说，循环（或者说枚举）是自动的，想控制循环的次数，只能通过修改将被枚举的列表元素来实现。

比如路径 `~.A.B` 内有三个元素 `[1, 2, 7]`，而 template 为

```python
loop test
{LOOP-START:~.A.B}
data: {DATA:~.};
{LOOP-END}
over!
```

处理后为

```python
loop test
data 1;
data 2;
data 7;
over!
```

循环支持嵌套。

循环是隐形标签，即 `{LOOP-START:路径}` 和 `{LOOP-END}` 会被空字符串`''`替换。

**请将 `{LOOP-START:路径}` 和 `{LOOP-END}` 各自放在单独的一行。**

---

## 保留字

### `INDEX`

一个预定义的**局部变量**，用来在循环体中获取目前是第几个样本。目前能用在计算式中，也能用作访问数据的路径下标。

>**局部变量**的意思是，如果有多个循环嵌套，内层循环的 `INDEX` 不会干扰到外层循环，但是**外层循环的 `INDEX` 可以在内层循环被访问**。

在非循环体的上下文语境使用 `INDEX` 是错误行为。

比如路径 `~.A.B` 内有三个元素 `[1, 2, 7]`，而 template 为

```python
loop test
{LOOP-START:~.A.B}
data {CALC:INDEX+1}: {DATA:~.};
{LOOP-END}
over!
```

处理后为

```python
loop test
data 1: 1;
data 2: 2;
data 3: 7;
over!
```

### `len()`

用于计算给定路径的列表长度。只能用在计算式中。

比如路径 `~.A.B` 内有四个元素 `[1, 2, 7, 200]`，而 template 为

```python
length test
{ASSIGN:length = len(~.A.B)}
len(~.A.B) == {CALC:length*2}
over!
```

处理后为

```python
length test
len(~.A.B) == 4
over!
```

### `REVERSE`

用于反转数据的数组。详见 [数据的路径 - 数组的切片与反转](#数组的切片与反转)。

### 单行注释

以 `#` 开头。该行会被忽略，不会出现在最终 Prompt 中。

---

## 数据的路径

### 绝对路径

数据的路径用来在给定的字典结构中寻找对应的匹配。

首先要知道的是，`AdvancedPromptBuilder.build_prompt()` 方法使用 `**data` 收集具名形参，因此如果你的 python 代码为

```python
apb = AdvancedPromptBuilder(template)
prompt = apb.build_prompt(
    incontext_samples=is_data, 
    input_db=db, 
    input="Will it succeed?"
    )
```

那么你输入的数据将收集到一个叫 `data` 的字典中，它的内容为：

```json
{
    "incontext_samples": is_data,
    "input_db": db, 
    "input": "Will it succeed?"
}
```

它是最外层上下文的数据。

假设路径是 `incontext_samples.[0].question`，那么它等价于 Python 代码 `data["incontext_samples"][0]["question"]`。也就是说，两个点之间的文字会被当做字典的键或者列表的序号。

**请注意**，如果要在路径中包含纯数字（为了读取列表的第几个元素），要用中括号括起来，就像上例。如果不括起来，像  `incontext_samples.0.question`，那么 0 会被当作字符串处理： `data["incontext_samples"]["0"]["question"]`。

自定义的变量和内置变量 `INDEX` 可以用作下标，格式为 `[变量名]`。但是 `len()` 不行，**目前不支持在下标中使用计算式。**

列表元素下标不要像 Python 一样：`incontext_samples[2]`，而应该加上小数点分隔：`incontext_samples.[2]`

如果绝对路径为空，如 `{DATA:}`， 意味着使用整个 `data`。

### 相对路径

在路径前加上 `~.` 代表相对路径，获取当前上下文中的数据。例如下面的 Template

```python
loop test
{LOOP-START:A.B}
Question: {DATA:~.final.question};
{LOOP-END}
over!
```

当循环体枚举到第三个元素时，此时上下文中的数据为 `A.B.[2]`，等价于 Python `data["A"]["B"][2]`，`~.` 指的就是这个数据。此时，相对路径 `~.final.question` 就等价于绝对路径 `A.B.[2].final.question`。

如果用绝对路径，上面的循环为

```python
loop test
{ASSIGN:global_index = 0}
{LOOP-START:A.B}
# 可以使用自己定义的全局变量
Question: {DATA:A.B.[global_index].final.question};
{ASSIGN:global_index += 1}
# 也可以使用内置的 INDEX
Question: {DATA:A.B.[INDEX].final.question};
{LOOP-END}
over!
```

可以看到，在循环体内部使用相对路径比较方便。

在非循环体内部，相对路径和绝对路径是相等的。

如果相对路径为空，如 `{DATA:~.}`， 意味着使用整个当前上下文中的数据。

### 数组的切片与反转

和 Python 语法大多一致，但是不支持步进切片。

```python
~.A.B.[:2] # 序号 0~1，注意 2 不包括在内
~.A.B.[4:] # 序号 4 到 末尾
~.A.B.[2:10] # 序号 2~9，
~.A.B.[10:2] # 等价于序号 3~10 然后反转
~.A.B.[10:2].[REVERSE] # 等价于 ~.A.B.[10:2] 然后反转
```
