import os
import sys

work_dir = ''
scope = {}


def get_variable(s: str, left_ch: str, right_ch: str):
    v = []
    n = 0
    left = 0
    for i, ch in enumerate(s):
        if ch == left_ch:
            if n == 0:
                left = i
            n += 1
        elif ch == right_ch:
            n -= 1
            if n == 0 and (left == 0 or (s[left - 1] != '\\')):
                v.append((left, i + 1))
    return v


def replace_variable_only(s: str):
    left = 0
    right = 0
    for i, j in enumerate(s):
        if j == '[':
            left = i
        if j == ']':
            right = i
            break
    if left != right and left > 0:
        index = s[left + 1:right]
        try:
            res = scope[s[:left]][index]
        except:
            res = scope[s[:left]][int(index)]
        res = str(res)
        return res
    if s in scope:
        r = str(scope[s])
        return '\\{' + r + '}' if isinstance(scope[s], dict) else r
    return s


prior = {'(': 0, ')': 0, '+': 1, '-': 1, '*': 2, '/': 2, '%': 2, '^': 3, '~': 4}

lr = {'+': 'left', '-': 'left', '*': 'left', '/': 'left', '%': 'left', '^': 'right', '~': 'right'}


def check_couple(left: str, right: str, s: str):
    num = 0
    for i in s:
        if i == left:
            num += 1
        elif i == right:
            if num == 0:
                return False
            num -= 1
    return num == 0


operand = set('0123456789')

func_operand = {
    '+': lambda left, right: left + right,
    '-': lambda left, right: left - right,
    '*': lambda left, right: left * right,
    '/': lambda left, right: left / right if right != 0 else float('nan'),
    '%': lambda left, right: left % right,
    '^': lambda left, right: left ** right
}


def calc(s: str):
    if not check_couple('(', ')', s):
        raise ValueError('the counts of ( must equals with the counts of )')
    output = []
    operator = []
    expect_operand = True
    index = 0
    size = len(s)
    while index < size:
        if s[index] == '(':
            expect_operand = True
            operator.append(s[index])
            index += 1
        elif s[index] == ')':
            while operator[-1] != '(':
                output.append(operator[-1])
                operator.pop()
            operator.pop()
            expect_operand = False
            index += 1
        elif s[index] in operand:
            num = []
            while index < size and s[index] in operand:
                num.append(s[index])
                index += 1
            if index < size and s[index] == '.':
                num.append(s[index])
                index += 1
            while index < size and s[index] in operand:
                num.append(s[index])
                index += 1
            output.append(float(''.join(num)))
            expect_operand = False
        elif s[index] in lr:
            if len(operator) == 0:
                operator.append(s[index])
            else:
                op = operator[-1]
                if expect_operand and s[index] == '-':
                    ch = '~'
                else:
                    ch = s[index]
                    expect_operand = True
                while prior[op] > prior[ch] or (prior[op] == prior[ch] and lr[ch] == 'left'):
                    output.append(op)
                    operator.pop()
                    if len(operator) == 0:
                        break
                    op = operator[-1]
                operator.append(ch)
            index += 1
        else:
            index += 1
    while len(operator) > 0:
        output.append(operator.pop())
    stack = []
    for token in output:
        if isinstance(token, float):
            stack.append(token)
        else:
            if token == '~':
                cur = stack.pop()
                stack.append(-cur)
            else:
                right = stack.pop()
                left = stack.pop()
                stack.append(func_operand[token](left, right))
    c = int(stack[-1])
    return c if stack[-1] == c else stack[-1]


def calc_order(order):
    v = get_variable(order, '(', ')')
    if not v:
        if get_variable(order, '{', '}'):
            order = replace_variable(order)
        return order
    res = order
    for s, e in reversed(v):
        t = order[s:e]
        if get_variable(t, '{', '}'):
            t = replace_variable(t)
        res = res[:s] + str(calc(t)) + res[e:]
    return res


def replace_variable(order):
    v = get_variable(order, '{', '}')
    if not v:
        if get_variable(order, '(', ')'):
            order = calc_order(order)
        return replace_variable_only(order)
    res = order
    for s, e in reversed(v):
        t = order[s + 1:e - 1].strip()
        if get_variable(t, '(', ')'):
            t = calc_order(t)
        res = res[:s] + replace_variable_only(replace_variable(t)) + res[e:]
    return calc_order(res)


def transform(s: str, target: str = None):
    res = []
    jmp = False
    size = len(s)
    for i, ch in enumerate(s):
        if jmp:
            jmp = False
            continue
        if ch == '\\':
            jmp = True
            if i + 1 < size:
                if s[i + 1] == target or target is None:
                    res.append(s[i + 1])
                else:
                    res.append('\\')
                    res.append(s[i + 1])
            else:
                raise ValueError(rf'the position that beyond \ must be a operator index:{i} char:{s[i]} object:{s}')
        else:
            res.append(ch)
    return ''.join(res)


def get_dict(s: str):
    idx = []
    for i, ch in enumerate(s):
        if ch == ',':
            if i == 0:
                idx.append(i)
            elif s[i - 1] != '\\':
                idx.append(i)
    t = []
    last = 0
    for i in idx:
        t.append(s[last:i])
        last = i + 1
    if last <= len(s):
        t.append(s[last:])
    idx = []
    for i in t:
        size = len(i)
        j = 0
        idx.append([])
        while j < size:
            if i[j] == ':':
                if j == 0:
                    idx[-1].append(j)
                elif i[j - 1] != '\\':
                    idx[-1].append(j)
            j += 1
    arr = []
    for i, j in enumerate(idx):
        arr.append([])
        last = 0
        for k in j:
            arr[-1].append(t[i][last:k])
            last = k + 1
        if last <= len(t[i]):
            arr[-1].append(t[i][last:])
    return {i[0]: i[1] if len(i) > 1 else '' for i in arr}


def get_list(s: str):
    idx = []
    size = len(s)
    jmp = False
    for i, ch in enumerate(s):
        if jmp:
            jmp = False
            continue
        if ch == '\\':
            if i + 1 >= size:
                raise ValueError('in front of \\ must be a operator')
            jmp = True
        if ch == ',':
            idx.append(i)

    t = []
    last = 0
    for i in idx:
        t.append(s[last:i])
        last = i + 1
    if last <= len(s):
        t.append(s[last:])
    return t


def echo(order):
    print(transform(order[5:]))


cast = {'int': int, 'float': float, 'str': str, 'dict': get_dict, 'list': get_list}


def parse_set(order: str):
    global scope
    order = order.split(maxsplit=3)
    scope[order[1]] = cast[order[2]](order[3])


def push(order):
    os.chdir(order[5:])


help = (
    'sample_order: exit->turn off this program\tscope->see all variable\thelp->get help\tls->show files\twds->show work_dir\n'
    'other_order: echo <content>->print something\t'
    'set <name> <type> <value>->create new variable\tpush <address>->enter a new work_dir\tpop->return last work_dir\t'
    'hist [num]->show all orders that has entered or only nearest num counts\t'
    'reo <num>-> re call order that index is num in hist (negative num is ok,as python list)\n'
    'introduction_of_variable: int , float ,str , dict , list is OK.\t'
    'You can vis variable by the form like {var}.\t'
    'If you want to calc , please use the form list ({var1} + {var2}).\t'
    '+ - * / % ^ is OK.\t'
    '- could be sub or negative.\t'
    'If you want to calc expression like -2^2 , you would get 4 instead of -4.\t'
    'To get -4 , you have to enter -(2^2).\t'
    'Dict and List ONLY HAVE one Dimension.\t'
    'You can vis it\'s element by [].\t'
    'The form list {arr[{var1}]} or {arr[({num1}+{num2})]} is OK.\t'
    'What I cannot but emphasize is that if you want to use reo <negative num> to recall something,you must notice that '
    'the sentence you just entered also will be record in hist. For example , if you want to recall the last sentence that you '
    'used , don\'t enter reo -1 but reo -2. Otherwise , the program won\'t  stop recursive until stack overflow!\t'
    'Hoping you have a lucky experience!\n')

files = []

orders = []

sample_order = {'exit': lambda: sys.exit(), 'scope': lambda: print(scope),
                'help': lambda: print(help), 'ls': lambda: print(os.listdir(os.getcwd())),
                'wds': lambda: print(files)}


def pop():
    files.pop()
    if len(files) > 0:
        os.chdir(files[-1])


def hist(order):
    if order == 'hist':
        print([f'{i} -- {o}' for i, o in enumerate(orders)])
    else:
        size = len(orders)
        idx = 0
        want = int(order[5:])
        res = []
        while size and idx < want:
            res.append(f'{size - 1} -- {orders[size - 1]}')
            idx += 1
            size -= 1
        print(res)


def reo(order):
    idx = int(order[4:])
    run(orders[idx])


def run(order):
    try:
        order = replace_variable(order)
    except Exception as e:
        print('error')
        print(str(e))
    if order in sample_order:
        sample_order[order]()
    elif order.startswith('set'):
        parse_set(order)
    elif order.startswith('echo'):
        echo(order)
    elif order.startswith('push'):
        push(order)
    elif order.startswith('pop'):
        pop()
    elif order.startswith('hist'):
        hist(order)
    elif order.startswith('reo'):
        reo(order)
    else:
        orders.pop()
        raise NameError('please enter right order')


while True:
    work_dir = os.getcwd()
    scope['wd'] = work_dir
    if len(files) == 0 or files[-1] != work_dir:
        files.append(work_dir)
    print(work_dir, end='>')
    order = input().strip()
    orders.append(order)
    if order == '':
        continue
    try:
        run(order)
    except Exception as e:
        print('please enter help to get using assistance')
        print(str(e))
