# 我自制的一个简单shell

- 已实现变量系统和计算功能和初步的if与while功能
- 初次开发时间是2026年的4月18和19号的两个晚上
- 2026年4月20日晚上传github。

## 源码更新但exe尚未更新的功能:

- import对被引号包裹的地址解析支持

## 下一步准备在源码中做的改动:

- 尝试合并部分重复代码

## 基本语法介绍

### 变量系统：

- 变量类型：
    - int,float,str,list,dict,bool
- 变量特点：
    - int底层受益于python的大数，也拥有大数特点
    - float只支持小数形式
    - str 可以 用来存储int 和 float ， 并且这样不会有赋值类型检查
    - list 和 dict 可以相互嵌套
    - 存储bool时，使用 0 、 False 、 空list 、 空dict 是假，其他都是真
- 变量取值：
    - 所有变量取值都应该用{}包裹:`{arr[{a[{b[{c[({num0}+{num1})]}]}]}]}`
    - 函数调用时，原则上不用{}传参
    - 部分内置命令使用时，不适用{}
    - 区别可以理解为传值和传名

### 表达式计算和变量

- 运算符支持（按优先级从小到大排序）：
    - 左右括号：(,)
    - 逻辑或：||
    - 逻辑与：&&
    - 按位或：|
    - 按位异或：^
    - 按位与：&
    - 相等，不等：==,!=
    - 大于，小于，大于等于，小于等于：>,<,>=,<=
    - 加，减：+,-
    - 乘，除，取模：*,/,%
    - 幂乘：**
    - 逻辑非，负号，按位取反：!,-,~
- 特殊运算符和行为说明：
    - && 和 || 未支持短路求值
    - 负号的优先级比幂乘高，所以-2\**2 == 4;-(2**2)==-4
    - {,<,[,\,(在特殊语义时，正常使用需要转义
    - \对于非可转义字符，会保留原字符，同时\会被去掉
    - 所有表达式必须用()包裹，支持嵌套
        - 如：({a}+{b}) , ({a}-{b})

### 变量的赋值、删除与修改

- 相关指令
    - set <name> <type> <value> 支持类似`set a[idx_1][key_1][key_2]` list/dict/int/bool/str/float 嵌套赋值，局部作用域
    - appendlist/appenddict <name> ele1,ele2/key1:val1,key2:val2 支持嵌套赋值，支持创建元素，支持一次追加多个，动态作用域
        - 有特殊切片追加语义，`appendlist arr[a:b] ele1,ele2 ` 意为对从`arr[a]` 到 `arr[b-1]` 每一个都是list，且广播追加
        - 若有非list，会报错
    - len arr l 将arr的长度存储进l，可创建变量，支持嵌套查询，非list/dict/str默认长度为1，动态作用域
    - inc/dec a 将a自增/自减1，支持嵌套修改 动态作用域，非可加减对象会报错
    - haskey di key outcome 将key in di 的结果存在outcome中，之后嵌套查询，动态作用域
    - `del [global] element` 从作用域删除element ， 由global 与否决定是局部还是动态作用域，支持嵌套，不存在变量不报错
    - `delkey [global] di key` 从di中删除键key，global同上，支持嵌套，不存在变量报错
    - `delindex [global] arr idx` 从arr中删除索引idx，global同上，支持嵌套，不存在变量报错
    - stackpush->调用全局栈，stackpush name ，把{name}压入栈，没有name变量则压入name字面量
    - stackpop->调用全局栈，stackpop name，把栈顶元素弹入name，本层无变量则直接创建，若栈为空会报错
    - stackout->调用全局栈，丢弃栈顶元素，栈为空不报错
    - stackpeek->调用全局栈，stackpeek name，把栈顶元素赋值给name，不弹栈，引用变量会共享内存，栈为空会报错，本层无变量则创建
    - iter d 用来遍历dict d ，如果遍历对象不存在，报错，支持嵌套，在当前作用域生成_key和_val用来访问当前键值对，用next推进，_
      hasnext说明是否还可以推进
        - iter一次只能在当前作用域持有一个字典的迭代器

### 控制流

主要有条件判断和循环

这是条件判断

`if(condition) <body> endif`

它不支持elseif 和 else

可以写在一行，也可以写在多行

condition中，任何bool为True的都可以进入

set a int 4

单行语法

`if({a});echo I get here!\;我打印了\;;echo a is {a};endif`

多行语法

```text
if({a})

echo I get here!\;我打印了\;

echo a is {a}

endif
```

多行也可以写;结尾(endif除外)

在if中想表达;必须转义

endif后禁止有; 否则报错

while差不多

endwhile后禁止有; 否则报错

`while(condition) <body> endwhile`

if 可以写在 while 里， if 和 while 可以任意嵌套，break会结束最近的while，continue 中止本次，开始下一次

```text
set a int 1

while({a})

inc a

if ({a}>20)

while ({a})

dec a

echo 减少a

if ({a} == 10)

echo a == 10

echo 退出内层嵌套while

break

endif

if ({a}<=15)

continue

endif

echo 到这里了！

endwhile

echo 直接让 a 为 0

set a int 0

endif

if ({a}>10)

echo a > 10 , a is {a}

endif

endwhile 
```

### macro系统

```text
宏系统花了我最多功夫
其实可以视为函数
必须用{}包裹才能调用
可以递归调用
宏内可以定义宏
宏内可以嵌套调用宏
形式是macro name<element1,element2>; body ; endmacro
endmacro后禁止有;
传参时一般不用{},不过如果你有特殊需求，也可以{}，如果你理解在这里使用{}会发生什么的话
这样会发生一些很有意思的事情，也许等会可以演示一下
如果传递的是另一个macro，而且你是想在那里调用，{}还是必要的
看例子吧
```

以下内容可以保存成txt后用import 文件地址运行看效果

```text

echo 递归计算斐波那契数列

macro fib<n>
if({n}<=1)
return {n}
endif
return ({fib<({n}-1)>}+{fib<({n}-2)>})
endmacro

echo {fib<6>}
echo {fib<10>}
echo {fib<20>}

echo 递归计算阶乘

macro f<n>
if({n}<=0)
return 1
endif
return ({n}*{f<({n}-1)>})
endmacro

echo {f<6>}
echo {f<10>}
echo {f<30>}

echo 用记忆化优化斐波那契数列

set arr dict 0:0,1:1

macro f<n,arr>
haskey arr {n} res
if({res})
return {arr[{n}]}
endif
set a int {f<({n}-1),arr>}
set b int {f<({n}-2),arr>}
appenddict arr {n}:({a}+{b})
return {arr[{n}]}
endmacro

echo {f<10,arr>}

echo {f<20,arr>}

echo {f<30,arr>}

echo {f<100,arr>}

echo 阿克曼函数

macro ack<m,n>
if({m}==0)
return ({n}+1)
endif
if({n}==0)
return {ack<({m}-1),1>}
endif
return {ack<({m}-1),{ack<{m},({n}-1)>}>}
endmacro

echo {ack<0,3>}

echo {ack<3,2>}

echo 在macro中嵌套定义并调用macro

macro outer<content,key>
macro first<content,key>
macro second<content,key>
macro last<second,key>
return {content[{key}]}
endmacro
return {last<content,key>}
endmacro
return {second<content,key>}
endmacro
return {first<content,key>}
endmacro

set map dict apple:I eat it,cat:This is an animal,fox:It looks like a dog!,dog:You can taste it

echo {outer<map,fox>}

echo 把一个macro的结果传递给另一个macro

macro add<a,b>
return ({a}+{b})
endmacro

echo {add<15,{add<14,27>}>}

echo 通过组合macro降低任务难度

macro max<a,b>
if ({a}>{b})
return {a}
endif
return {b}
endmacro

macro getMaxByRecursive<arr>
len arr l
if ({l}==1)
return {arr[0]}
endif
return {max<{arr[0]},{getMaxByRecursive<arr[1:{l}]>}>}
endmacro

set arr list 0,1,2,3,4,5,6,7,8,20,10,11,12
echo {getMaxByRecursive<arr>}


# 关于macro的作用域机制

# 只有传递的参数和在macro局部用set声明的算其局部变量

# 如果在macro中操作了未声明变量，沿作用域逐级寻找

# 找不到报错

echo 作用域演示

macro f1<a>
echo {a}
inc a
echo {a}
endmacro

set num int 10
echo {num}
{f1<num>}
echo {num}

macro f2<>
echo {num}
inc num
echo {num}
endmacro

set num int 10
echo {num}
{f2<>}
echo {num}


# return你可以无返回值，也可以返回一个值，如果想返回多个值，请注意

echo return 返回多个值

macro getManyVal<>
return 1,2,3,4,5
endmacro

set arr list {getManyVal<>}

echo {arr}

macro show<>
set arr list 0,1,2,3,4,5
return {arr}
endmacro

echo {show<>}

# 如果你要让某些值能够跨作用域保留和传递，return 很多时候可能不够好用
# 建议这么做

macro t<arr>
appendlist arr 我要这个,这个也要,还有那个,100,150,300
endmacro

set arr list 0

{t<arr>}

echo {arr}

# 你还可以这么做
# 关于appendlist 和 appenddict ，后面还会有详细介绍

macro t<arr>
set aBigList list 0,1,2,3,100,200,500
len aBigList l
set i int 0
while ({i}<{l})
appendlist arr {aBigList[{i}]}
inc i
endwhile
endmacro

set arr list 0

{t<arr>}

echo {arr}

# 记得不要把创建arr时不得不用的那个数（比如0）给当成返回的了

echo 演示那个比较有趣的行为\(以及利用macro的副作用工作)

set var str abc
set abc str xyz

macro print<x>
echo {x}
endmacro

{print<{var}>}

# 看，打印的是xyz而不是abc
# 我认为这个特性利用好了可以写出很精巧的东西
# 实际上是因为macro期待你传递一个变量，而{}表示取值，这样你传入的{var}就会被认为是变量abc，自然打印了xyz

# 再展示一个冒泡排序

macro sort<arr>
len arr l
set i int 0
while({i}<{l}-1)
set j int 0
while({j}<{l}-{i}-1)
if({arr[{j}]}>{arr[({j}+1)]})
set temp int {arr[{j}]}
set arr[{j}] int {arr[({j}+1)]}
set arr[({j}+1)] int {temp}
endif
inc j
endwhile
inc i
endwhile
endmacro

set arr list 21
set i int 0
while ({i} < 21)
appendlist arr {i}
inc i
endwhile

echo {arr}

{sort<arr>}

echo {arr}
```

### 命令行交互语句

```text
push->用于切换工作目录\(这里不演示，因为需要输入本地真实存在的地址)
pop->用于返回上一级工作目录
ls->显示当前目录下的文件和目录名
hist->显示所有历史命令\(通过import 命令导入的.txt文件运行不予记录，if、while、macro作为整体记录，每条指令有自己的编号，从0开始)
hist还可以通过 hist <num> 来看最近的num条历史命令，如果不够num次，显示全部
hist 2:\(hist会把自己本身加入再打印，这点要注意，当然在import期间你还是看不到)
histc->清空历史记录 ，histc <num> 是清除前num条记录，如果num足够大，也会清除所有记录
reo->重新执行某条指令,结合hist使用, reo <num> ,num可以是正数或负数，不要越界，reo不会在hist中，而是把实际运行的计入hist
reo-1 或 reo -1 都合法，但不是所有指令都可以紧贴着的。之后会给出不同情况表。
reo后面接负数时，不会考虑reo本条带来的影响，即如果要运行刚刚那条，使用reo -1 而非 reo -2
在import的文件中reo指令会被无视，因为hist不会记录内容，如果你直接reo-1，会重新立刻引入同一文件，这会进入危险的无限递归
echo 用来打印，必须空一个空格，多余的空格会被作为前导空格
import address 可以用来引入.txt的解释器可执行文件
```