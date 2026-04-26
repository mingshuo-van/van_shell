help_str = r"""
# 放在这里主要是用来做帮助文档
# 或者，复制内容到一个txt后尝试import运行，这样也许会更容易理解语法和规则
echo 本文件用于展示本解释器特性和语法
echo 主要分为变量系统与操作、表达式系统、控制流、宏系统四个部分，此外还有一部分是介绍解释器的命令行语法与部分关键字
echo 那部分会放在最后
echo 解释器仅使用python的os和sys两个库
echo 无其他库依赖
echo 采用自实现运算核心，未使用eval，因而有一些区别于python的特点和行为，将在表达式系统部分说明
echo 可以使用解释器运行本文件，观察输入，理解解释器
echo 变量系统:
# 让我弄一个容器，是的，我有注释系统
# 但是要注意，只有单行注释，而且#必须要在句首
set a int 5
while({a})
appendlist arr 0
dec a
endwhile
# int
set arr[0] int 10
# float
set arr[1] float 13.5
# str
set arr[2] str hello,world! This is my language!
# list
set arr[3] list 0,1,2,apple,banana,cat,fox
# dict
set arr[4] dict apple:1,banana:2,cat:3,ege:4,fox:5
# 展示它们
set a int 0
while({a}<5)
echo {arr[{a}]}
# inc 使变量增加一 dec 可以是其减少一
inc a
endwhile
# list是可以嵌套其他东西的，dict也一样，多层嵌套也支持
set arr[0] dict apple:1,banana:2
set arr[0][apple] list 14,16,18,19
set arr[0][apple][2] str 这是一句话
# 分别打印一下看看
echo 嵌套dict存在时，深层打印会出现一些反斜杠，这是为了转义某些特殊字符
echo {arr}
echo {arr[0]}
echo {arr[0][apple]}
echo {arr[0][apple][2]}
# 多层嵌套
set a list 0,1,2
set b list 0,1,2
set c list 0,1,2
set d list 0,1,2
set num1 int 0
set num2 int 0
set arr list apple,banana,cat,fox
# 这里提前出现了计算，所有可以计算的表达式是要用()包裹的
echo {arr[{a[{b[{c[{d[({a[{num1}]}+{b[({num2}+1)]})]}]}]}]}]}
# 字符串是可以下标访问的
set a str hello
echo {a[0]}
# 负数索引也可以，可以索引访问的都支持负数索引
echo {a[-1]}
# 切片语法也支持，诸如[a:b],[:b],[a:],[:]都可以
echo {a[1:10]}
echo {a[:]}
# 用切片赋值也是可以的
set arr list 0,1,2
set arr[0:2] list 11,12,13,14,15,16
echo {arr}
# 看看bool吧
set a bool 0
echo {a}
set a bool 1
echo {a}
set a bool 你好
echo {a}
set b int -3
set a bool {b}
echo {a}
# 变量系统结束了，接下来是表达式系统

echo 表达式系统:
# 说实话，表达式不难理解，就是写起来可能会觉得有点费劲
# 所有要计算的式子都得用()包裹，否则就不会计算
# 接下来的所有例子都可以用来感受和理解
echo 支持的运算符如下：
echo + - * / % ** > < == >= <= != & | ^ ! && ||
# 它们分别是
echo 加 减 乘 除\(负) 取模 幂 大于 小于 等于 大于等于 小于等于 不等于 按位与 按位或 按位异或 逻辑非 逻辑与 逻辑或
echo - 可以是一元负号或减号
# 先拿几个变量
set a int 10
set b int 12
# 接下来分别演示
echo ({a}+{b})
echo ({a}-{b})
echo ({a}*{b})
echo ({a}/{b})
echo ({a}%{b})
echo ({a}**{b})
echo ({a}>{b})
echo ({a}<{b})
echo ({a}=={b})
echo ({a}>={b})
echo ({a}<={b})
echo ({a}!={b})
echo ({a}&{b})
echo ({a}|{b})
echo (!{a})
echo ({a}^{b})
echo ({a}&&{b})
echo ({a}||{b})
# ()也可以用来改变运算优先级,这一点和其他语言一样
# 特殊情况，这一点和数学上的规定不一样
echo -2**2 != -4
echo -2**2 == (-2**2)
echo -\(2**2) == (-(2**2))
# bool True为1，False为0
set c bool True
echo {c}
echo ({c})
echo (!{c})
echo 此外，&&和||未实现短路效果，这点须注意
# 到现在为止，应该注意到代码中偶尔会出现一些特殊的\符号
# 这是用来转义特殊字符的，\本身也是特殊字符
echo 特殊字符有：\{ \( \< \\ \, \:
echo 不是在所有句子中它们都是特殊字符的,如果在某部分语法中没有特殊含义，它不会被视为特殊字符
echo 换句话说，必须要转义的有\{ \( \\
echo \< \, 和 \: 只在具备特殊含义时才需要转义
echo \\ 如果在非特殊字符前使用，不会报错，而是保留原字符，无视\\，但是\\后面不能为空
# 值得一提的是
# 如果set a str 10
# 也是能正确运算的
# int 和 float 声明可以帮助在创建变量时检查，但你不这么做也可以
# 表达式系统大概就这些

echo 控制流:
# 主要有条件判断和循环
# 这是条件判断
echo if\(condition) <body> endif
# 它不支持elseif 和 else
# 可以写在一行，也可以写在多行
# condition中，任何bool为True的都可以进入
set a int 4
# 单行语法
if({a});echo I get here!\;我打印了\;;echo a is {a};endif
# 多行语法
if({a})
echo I get here!\;我打印了\;
echo a is {a}
endif
# 多行也可以写;
# 在if中想表达;必须转义
# endif后禁止有; 否则报错
# while差不多
# endwhile后禁止有; 否则报错
echo while\(condition) <body> endwhile
# if 可以写在 while 里， if 和 while 可以任意嵌套，break会结束最近的while，continue 中止本次，开始下一次
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
# 控制流主要就是这两个

echo 宏系统:
# 宏系统花了我最多功夫
# 其实可以视为函数
# 必须用{}包裹才能调用
# 可以递归调用
# 宏内可以定义宏
# 宏内可以嵌套调用宏
# 形式是macro name<element1,element2>; body ; endmacro
# endmacro后禁止有;
# 传参时一般不用{},不过如果你有特殊需求，也可以{}，如果你理解在这里使用{}会发生什么的话
# 这样会发生一些很有意思的事情，也许等会可以演示一下
# 如果传递的是另一个macro，而且你是想在那里调用，{}还是必要的
# 看例子吧

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

# 宏系统大概说完了

echo 命令行指令和部分关键字

echo scope->用于打印当前变量区域

echo 演示用scope显示局部作用域

macro test<>
set arr list 0,1,2
set n int 14
set b float 14.6
scope
endmacro

{test<>}

echo 可以发现局部作用域第一个是 "":""
echo 这是因为macro test 没有参数，否则这里会显示形参和传入值的绑定


echo push->用于切换工作目录\(这里不演示，因为需要输入本地真实存在的地址)
echo pop->用于返回上一级工作目录
echo ls->显示当前目录下的文件和目录名
echo hist->显示所有历史命令\(通过import 命令导入的.txt文件运行不予记录，if、while、macro作为整体记录，每条指令有自己的编号，从0开始)
hist
echo 我刚刚hist了一次，你应该只能看到一个import记录\(如果你在import前没有执行其他指令)，因为import期间指令不记录
echo hist还可以通过 hist <num> 来看最近的num条历史命令，如果不够num次，显示全部
echo hist 2:\(hist会把自己本身加入再打印，这点要注意，当然在import期间你还是看不到)
hist 1
echo 你应该只能看到一个import的记录
echo histc->清空历史记录 ，histc <num> 是清除前num条记录，如果num足够大，也会清除所有记录
echo reo->重新执行某条指令,结合hist使用, reo <num> ,num可以是正数或负数，不要越界，reo不会在hist中，而是把实际运行的计入hist
echo reo-1 或 reo -1 都合法，但不是所有指令都可以紧贴着的。之后会给出不同情况表。
echo reo后面接负数时，不会考虑reo本条带来的影响，即如果要运行刚刚那条，使用reo -1 而非 reo -2
echo 在import的文件中reo指令会被无视，因为hist不会记录内容，如果你直接reo-1，会重新立刻引入同一文件，这会进入危险的无限递归
reo -1
# 上面的reo-1被无视了
echo inc->自增变量
echo dec->自减变量
echo inc 和 dec 可以用嵌套的方式调用，如下
set arr list 0,1,2
set arr[0] dict apple:1,banana:2
echo {arr}
inc arr[0][apple]
echo {arr}
echo appendlist->追加元素进列表,appendlist <name> element1,element2
echo appenddict->追加键值对进字典,appenddict <name> key1:val1,key2:val2
echo 这两个功能值得详细介绍
echo appendlist arr[0]   appendlist arr[:] appendlist arr[a][b][:]都支持
echo 其中切片语法表示从arr[a] 到 arr[b-1]的所有 list \(或dict) 都会被增加对应的量
echo 比如
set arr list 0,1,2
set arr[0] list 11,12,13,14
set arr[1] list 11,12,13,14
set arr[-1] list 11,12,13,14
echo {arr}
appendlist arr[:] 999,888,777
echo {arr}
echo appenddict差不多
echo 需要和set arr[:] list 0,1,2的切片语义予以区分
echo len->计算长度,len source length,存储source的长度进length,没有该变量会创建，有则直接覆盖，除list,dict,str外，长度都为1
echo stackpush->调用全局栈，stackpush name ，把{name}压入栈，没有name变量则压入name字面量
echo stackpop->调用全局栈，stackpop name，把栈顶元素弹入name，本层无变量则直接创建，若栈为空会报错
echo stackout->调用全局栈，丢弃栈顶元素，栈为空不报错
echo stackpeek->调用全局栈，stackpeek name，把栈顶元素赋值给name，不弹栈，引用变量会共享内存，栈为空会报错，本层无变量则创建
echo 演示stack相关指令
set arr list 0,1,2
stackpush arr
stackpeek notThisVar
echo {notThisVar}
set notThisVar[0] int 100
echo {notThisVar}
echo {arr}
stackout
stackpush arr[0]
stackpop notThisVar
echo {notThisVar}
echo iter->这是用来遍历dict的，iter dict_name
echo 演示iter用法
set d dict apple:1,banana:2,cat:3,fox:4,dog:5
iter d
while({_hasnext})
echo {_key}=={_val}
next
endwhile
echo iter会生成几个内置变量，保存在当前作用域，可以用next推动迭代器前进，无法返回
echo 如果需要返回，iter name 会重置一切
echo 同时只能持有一个迭代器
echo import->用来引入可执行文件，import <地址> 引入的会立刻运行
echo del->用来清理变量，只能清理变量名，类似del name[apple]这类写法也支持
echo del实际上就像一个不报错更全能的delkey和delindex，后两个命令会在下面介绍
echo del 默认只处理本层变量，没有变量不报错
echo del global name在全局清理距离调用处最近作用域的同名变量
echo 示例
set d dict a:1,b:2
set d[a] dict c:3,d:4
echo {d}
del d[a]
echo {d}
set d dict a:1,b:2
set d[a] dict c:3,d:4
macro t<>
del d[a]
endmacro
{t<>}
echo {d}
macro t<>
del global d[a]
endmacro
{t<>}
echo {d}
echo haskey->判断dict中是否有某个key，haskey dict_name,key_name,var
echo 结果存储在var中
echo 示例
set d dict a:1,b:2,c:3
set d[a] dict one:1,two:2
set d[a][one] dict ing:1,ong:2
haskey d[a][one] ing res
echo {res}
haskey d[a][one] notThis res
echo {res}
echo delkey dict_name key_name 用来在dict中删除key，删除行为固定在本层作用域
echo 示例
set d dict a:1,b:2,c:3
set d[a] dict one:1,two:2
set d[a][one] dict ing:1,ong:2
delkey d[a][one] ing
echo {d}
set d dict a:1,b:2,c:3
set d[a] dict one:1,two:2
set d[a][one] dict ing:1,ong:2
echo macro t<>
echo delkey d[a][one] int
echo endmacro
echo {t<>}
echo 上述会报错，为保证脚本文件执行的完整性，不在此演示了

echo delkey global dict_name key_name ，用于全局删除最近作用域的对应dict的key

set d dict a:1,b:2,c:3
set d[a] dict one:1,two:2
set d[a][one] dict ing:1,ong:2
echo {d}
macro t<>
delkey global d[a] one
endmacro
{t<>}
echo {d}

echo delindex list_name index 和 delindex global list_name index 可以参考上面的delkey
echo index 支持负数
# 关于哪些命令后不需要空格
echo 命令后不用跟空格的命令：pop,hist,reo,histc
echo 其他必须跟空格
# 特别地
echo echo后面必须跟一个空格，如果空格太多，则打印出来的东西也会有空格
echo            比如这样
# 一些特殊内置变量
echo _wd 当前工作目录
echo _hasnext 当使用iter后出现，是否还有下一个键值对
echo _key 当前键
echo _val 当前值

"""