import os
import sys

import helpFile

work_dir = ''
scope = {}
stack = []
call_stack = []
return_stack = []
macro_map = {}


def stackpop(order):
    _, var = order.split(maxsplit=1)
    if len(stack) == 0:
        raise ValueError('stack is empty')
    global in_macro
    d = scope
    if in_macro:
        d = call_stack[-1]
    d[var] = stack.pop()


def stackpush(order):
    _, var = order.split(maxsplit=1)
    d = scope
    global in_macro
    if in_macro:
        for target in reversed(call_stack):
            if var in target:
                d = target
                break
    if var in d:
        stack.append(d[var])
    else:
        stack.append(var)


def stackout():
    if len(stack) > 0:
        stack.pop()


def stackpeek(order):
    _, var = order.split(maxsplit=1)
    if len(stack) == 0:
        raise ValueError('stack is empty')
    global in_macro
    d = scope
    if in_macro:
        d = call_stack[-1]
    d[var] = stack[-1]


stack_order = {'stackpop': stackpop, 'stackpush': stackpush, 'stackout': lambda x: stackout(), 'stackpeek': stackpeek}


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
            if n == 0:
                if left == 0:
                    v.append((left, i + 1))
                else:
                    sub = 1
                    while left - sub >= 0 and s[left - sub] == '\\':
                        sub += 1
                    if sub & 1:
                        v.append((left, i + 1))
    return v


in_macro = False


def parse_macro(s: str):
    v = get_variable(s, '<', '>')
    if not v:
        return []
    if len(v) > 1:
        return []
    if v[0][0] == 0 or v[0][1] != len(s):
        return []
    left = v[0][0]
    right = v[0][1]
    name = s[:left].strip()
    a = special_split(s[left + 1:right - 1], ',')
    return [name.strip(), a]


def replace_variable_only(s: str):
    v = parse_macro(s)
    if v:
        run_macro(v)
        res = ''
        global has_res_flag
        if has_res_flag:
            res = return_stack.pop()
            has_res_flag = False
        return str(res)
    left = 0
    right = 0
    for i, j in enumerate(s):
        if j == '[':
            left = i
        if j == ']':
            right = i
            break
    if left != right and left > 0:
        d = call_stack[-1][s[:left]] if (in_macro and s[:left] in call_stack[-1]) else (scope[s[:left]]
                                                                                        if s[:left] in scope else s[
                                                                                                                  :left])
        index = call_stack[-1][s[left + 1:right]] if (in_macro and s[left + 1:right] in call_stack[-1]) \
            else s[left + 1:right]
        try:
            res = d[index]
        except:
            try:
                res = d[int(index)]
            except:
                res = s
        res = str(res)
        return res
    if in_macro and s in call_stack[-1]:
        key = call_stack[-1][s]
        return str(key)
    if s in scope:
        r = str(scope[s])
        return '\\{' + transform(r) + '}' if isinstance(scope[s], dict) else (
            transform(r) if isinstance(scope[s], list) else r)
    return s


prior = {'(': 0, ')': 0, '+': 1, '-': 1, '*': 2, '/': 2, '%': 2, '^': 3, '~': 4, '>': 0.7, '<': 0.7, '==': 0.69,
         '<=': 0.7, '>=': 0.7, '&': 0.65, '|': 0.63, '!': 4, '&&': 0.6, '||': 0.5, '!=': 0.69}

lr = {'+': 'left', '-': 'left', '*': 'left', '/': 'left', '%': 'left', '^': 'right', '~': 'right', '>': 'left',
      '<': 'left', '==': 'left', '>=': 'left', '<=': 'left', '&': 'left', '|': 'left', '!': 'right',
      '=': 'this is not a bug', '&&': 'left', '||': 'left', '!=': 'left'}


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
    '^': lambda left, right: left ** right,
    '>': lambda left, right: left > right,
    '<': lambda left, right: left < right,
    '>=': lambda left, right: left >= right,
    '<=': lambda left, right: left <= right,
    '==': lambda left, right: left == right,
    '&&': lambda left, right: left and right,
    '||': lambda left, right: left or right,
    '|': lambda left, right: left | right,
    '&': lambda left, right: left & right,
    '!=': lambda left, right: left != right
}


def calc(s: str):
    if not check_couple('(', ')', s):
        raise ValueError('the counts of ( must equals with the counts of )')
    s = s.replace('True', '1').replace('False', '0')
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
            while index < size and (s[index] in operand or s[index] == ' '):
                if s[index] == ' ':
                    index += 1
                    continue
                num.append(s[index])
                index += 1
            while index < size and s[index] == ' ':
                index += 1
            if index < size and s[index] == '.':
                num.append(s[index])
                index += 1
            while index < size and s[index] == ' ':
                index += 1
            while index < size and (s[index] in operand or s[index] == ' '):
                if s[index] == ' ':
                    index += 1
                    continue
                num.append(s[index])
                index += 1
            output.append(float(''.join(num)))
            expect_operand = False
        elif s[index] in lr:
            operator_ch = s[index]
            if index + 1 < size:
                if operator_ch in {'<', '=', '>', '!'}:
                    while index + 1 < size and s[index + 1] == ' ':
                        index += 1
                    if index + 1 >= size:
                        raise ValueError(f'in front of {operator_ch} still need a new operator')
                    if s[index + 1] == '=':
                        index += 1
                        operator_ch += s[index]
                    elif operator_ch == '=':
                        raise ValueError('= must be ==')
                if operator_ch in {'&', '|'}:
                    while index + 1 < size and s[index + 1] == ' ':
                        index += 1
                    if s[index + 1] == '&' or s[index + 1] == '|':
                        index += 1
                        operator_ch += s[index]
            if len(operator) == 0:
                operator.append(operator_ch)
            else:
                op = operator[-1]
                if expect_operand and s[index] == '-':
                    ch = '~'
                else:
                    ch = operator_ch
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
            elif token == '!':
                cur = stack.pop()
                stack.append(float(not cur))
            else:
                right = stack.pop()
                left = stack.pop()
                try:
                    stack.append(func_operand[token](left, right))
                except Exception as e:
                    if left == int(left) and right == int(right):
                        stack.append(func_operand[token](int(left), int(right)))
                    else:
                        raise e
    c = int(stack[-1])
    return c if stack[-1] == c else stack[-1]


def calc_order(order):
    v = get_variable(order, '(', ')')
    if not v:
        if get_variable(order, '{', '}'):
            order = replace_variable(order, True)
        return order
    res = order
    for s, e in reversed(v):
        t = order[s:e]
        if get_variable(t, '{', '}'):
            t = replace_variable(t, True)
        res = res[:s] + str(calc(t)) + res[e:]
    return res


def replace_variable(order, get=False):
    v = get_variable(order, '{', '}')
    if not v:
        if get_variable(order, '(', ')'):
            order = calc_order(order)
        return replace_variable_only(order) if get else order
    res = order
    for s, e in reversed(v):
        t = order[s + 1:e - 1].strip()
        if get_variable(t, '(', ')'):
            t = calc_order(t)
        res = res[:s] + replace_variable_only(replace_variable(t, True)) + res[e:]
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


def special_split(s: str, ch: str, special: str = '\\') -> list:
    idx = []
    jmp = False
    size = len(s)
    for i, cur in enumerate(s):
        if jmp:
            jmp = False
            continue
        if cur == special:
            if i + 1 >= size:
                raise ValueError('in front of \\ be a operator')
            jmp = True
        if cur == ch:
            idx.append(i)
    t = []
    last = 0
    for i in idx:
        t.append(s[last:i])
        last = i + 1
    if last <= size:
        t.append(s[last:])
    return t


def get_dict(s: str):
    t = special_split(s, ',')
    arr = [special_split(i, ':') for i in t]
    return {i[0]: i[1] if len(i) > 1 else '' for i in arr}


def get_list(s: str):
    return special_split(s, ',')


def echo(order):
    print(transform(order[5:]))


def get_bool(s: str):
    try:
        s = int(s)
    except:
        return bool(s)
    return bool(s)


cast = {'int': int, 'float': float, 'str': str, 'dict': get_dict, 'list': get_list, 'bool': get_bool}


def parse_set(order: str):
    global scope
    global in_macro
    order = order.split(maxsplit=3)
    if not in_macro:
        scope[order[1]] = cast[order[2]](order[3])
    else:
        call_stack[-1][order[1]] = cast[order[2]](order[3])


def push(order):
    os.chdir(order[5:])


help = helpFile.help_str

files = []

orders = []

sample_order = {'exit': lambda: sys.exit(), 'scope': lambda: print(scope),
                'help': lambda: print(help), 'ls': lambda: print(os.listdir(os.getcwd())),
                'wds': lambda: print(files), 'stack': lambda: print(stack),
                'register': lambda: print(macro_map)}


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
        want = int(order[4:].strip())
        res = []
        while size and idx < want:
            res.append(f'{size - 1} -- {orders[size - 1]}')
            idx += 1
            size -= 1
        print(res)


record = True
break_flag = False
continue_flag = False
return_flag = False
has_res_flag = False


def reo(order):
    idx = int(order[3:].strip())
    run(orders[idx])


def run_if(work):
    global record
    arr = special_split(work, ';')
    ok = arr[0][2:].strip()
    arr = list(map(lambda x: x.strip(), arr))
    jmp = 0
    if replace_variable(ok) != '0':
        for i in range(1, len(arr) - 1):
            if jmp:
                jmp -= 1
                continue
            if arr[i] == 'break':
                global break_flag
                break_flag = True
                return
            elif arr[i] == 'continue':
                global continue_flag
                continue_flag = True
                return
            elif arr[i].startswith('return ') or arr[i] == 'return':
                global return_flag
                return_flag = True
                if arr[i] == 'return':
                    global has_res_flag
                    has_res_flag = False
                else:
                    run(arr[i])
                return
            record = False
            statement = arr[i]
            if statement.startswith('if'):
                count = 0
                inner_if = []
                success = False
                for j in range(i, len(arr) - 1):
                    if arr[j].startswith('if'):
                        count += 1
                    elif arr[j] == 'endif':
                        count -= 1
                    if not count:
                        success = True
                        for k in range(i, j + 1):
                            inner_if.append(arr[k])
                        jmp = j - i
                        break
                if not success:
                    record = True
                    raise ValueError('if and endif must equal')
                statement = ';'.join(inner_if)
            elif statement.startswith('while'):
                count = 0
                inner_while = []
                success = False
                for j in range(i, len(arr) - 1):
                    if arr[j].startswith('while'):
                        count += 1
                    elif arr[j] == 'endwhile':
                        count -= 1
                    if not count:
                        success = True
                        for k in range(i, j + 1):
                            inner_while.append(arr[k])
                        jmp = j - i
                        break
                if not success:
                    record = True
                    raise ValueError('if and endif must equal')
                statement = ';'.join(inner_while)
            run(statement)
        record = True


def get_if(order):
    arr = []
    if not order.endswith('endif'):
        arr.append(order)
        count = 0
        limit = 1
        while count != limit:
            cur = input().strip()
            arr.append(cur)
            count += cur == 'endif'
            limit += cur.startswith('if')
        work = ';'.join(arr)
        orders.append(work)
    else:
        work = order
    run_if(work)


def run_while(work):
    global continue_flag
    global break_flag
    continue_flag = False
    break_flag = False
    global record
    arr = special_split(work, ';')
    ok = arr[0][5:].strip()
    arr = list(map(lambda x: x.strip(), arr))
    while replace_variable(ok) != '0':
        jmp = 0
        for i in range(1, len(arr) - 1):
            if jmp:
                jmp -= 1
                continue
            if continue_flag:
                continue_flag = False
                break
            elif break_flag:
                break_flag = False
                return
            global return_flag
            if return_flag:
                return
            elif arr[i].startswith('return ') or arr[i] == 'return':
                return_flag = True
                if arr[i] == 'return':
                    global has_res_flag
                    has_res_flag = False
                else:
                    run(arr[i])
                return
            record = False
            statement = arr[i]
            if statement.startswith('while'):
                count = 0
                inner_while = []
                success = False
                for j in range(i, len(arr) - 1):
                    if arr[j].startswith('while'):
                        count += 1
                    elif arr[j] == 'endwhile':
                        count -= 1
                    if not count:
                        success = True
                        for k in range(i, j + 1):
                            inner_while.append(arr[k])
                        jmp = j - i
                        break
                if not success:
                    record = True
                    raise ValueError('while and endwhile must equal')
                statement = ';'.join(inner_while)
            elif statement.startswith('if'):
                count = 0
                inner_if = []
                success = False
                for j in range(i, len(arr) - 1):
                    if arr[j].startswith('if'):
                        count += 1
                    elif arr[j] == 'endif':
                        count -= 1
                    if not count:
                        success = True
                        for k in range(i, j + 1):
                            inner_if.append(arr[k])
                        jmp = j - i
                        break
                if not success:
                    record = True
                    raise ValueError('if and endif must equal')
                statement = ';'.join(inner_if)
            run(statement)
    record = True


def get_while(order):
    arr = []
    if not order.endswith('endwhile'):
        arr.append(order)
        count = 0
        limit = 1
        while count != limit:
            cur = input().strip()
            arr.append(cur)
            count += cur == 'endwhile'
            limit += cur.startswith('while')
        work = ';'.join(arr)
        orders.append(work)
    else:
        work = order
    run_while(work)


def inc(order, num: int):
    var = order[3:].strip()
    global in_macro
    if in_macro:
        for d in reversed(call_stack):
            if var in d:
                try:
                    d[var] += num
                except Exception as e:
                    raise e
                return
    if var not in scope:
        raise KeyError(f'{var} is not a variable')
    try:
        scope[var] += num
    except Exception as e:
        raise e


def inner_append(order, kind: str):
    global in_macro
    d: dict = scope
    s = order[10:].strip()
    name, content = s.split(maxsplit=1)
    if in_macro:
        for target in reversed(call_stack):
            if name in target:
                d = target
                break
    if kind == 'list':
        t = special_split(content, ',')
        if name in d and isinstance(d[name], list):
            d[name].extend(t)
        else:
            d[name] = t
    elif kind == 'dict':
        t = [special_split(i, ':') for i in special_split(content, ',')]
        if name in d and isinstance(d[name], dict):
            for i in t:
                d[name][i[0]] = i[1]
        else:
            d[name] = {i[0]: i[1] for i in t}


def get_len(order):
    s = order[3:].strip()
    origin, res = s.split(maxsplit=1)
    d: dict = scope
    global in_macro
    if in_macro:
        for target in reversed(call_stack):
            if origin in target:
                d = target
                break
    if origin not in d:
        raise ValueError(f'{origin} is not a variable')
    if isinstance(d[origin], list) or isinstance(d[origin], dict) or isinstance(d[origin], str):
        d[res] = len(d[origin])
    else:
        d[res] = 1


def declare_macro(work):
    arr = special_split(work, ';')
    ok = arr[0][5:].strip()
    end = -1
    if ok[end] != '>':
        raise ValueError('macro syntax is error , the form list marco func_name<var1,var2>')
    start = 0
    for i, ch in enumerate(ok):
        if ch == '<':
            start = i
            break
    if start == 0:
        raise ValueError('macro syntax is error , the form list marco func_name<var1,var2>')
    content = []
    jmp = 0
    content.append(arr[0])
    for i in range(1, len(arr) - 1):
        if jmp:
            jmp -= 1
            continue
        if arr[i].startswith('macro'):
            count = 0
            inner_macro = []
            success = False
            for j in range(i, len(arr) - 1):
                if arr[j].startswith('macro'):
                    count += 1
                elif arr[j] == 'endmacro':
                    count -= 1
                if not count:
                    success = True
                    for k in range(i, j + 1):
                        inner_macro.append(arr[k])
                    jmp = j - i
                    break
            if not success:
                raise ValueError('marco and endmacro must equal')
            statement = ';'.join(inner_macro)
            content.append(statement)
            continue
        v = get_variable(arr[i], '{', '}')
        res = arr[i]
        for s, e in reversed(v):
            res = res[:s + 1] + arr[i][s + 1:e - 1].strip() + res[e - 1:]
        content.append(res)
    content.append(arr[-1])
    macro_map[ok[:start].strip()] = content


def get_macro(order):
    arr = []
    if not order.endswith('endmacro'):
        arr.append(order)
        count = 0
        limit = 1
        while count != limit:
            cur = input().strip()
            arr.append(cur)
            count += cur == 'endmacro'
            limit += cur.startswith('macro')
        work = ';'.join(arr)
        orders.append(work)
    else:
        work = order
    declare_macro(work)


def run_macro(arr):
    name = arr[0]
    t = arr[1]
    for i in range(len(t)):
        t[i] = replace_variable(t[i])
    content = macro_map[name]
    end = -1
    start = 0
    origin = content[0]
    for i, ch in enumerate(origin):
        if ch == '<':
            start = i
            break
    origin = special_split(origin[start + 1:end], ',')
    if len(origin) != len(t):
        raise ValueError(f'{t} not equals with {origin}')
    cur_call_scope = {}
    for k, v in zip(origin, t):
        get = False
        for target in reversed(call_stack):
            if v in target:
                cur_call_scope[k] = target[v]
                get = True
                break
        if get:
            continue
        cur_call_scope[k] = scope[v] if v in scope else v
    call_stack.append(cur_call_scope)

    fact = {' ' + k + ' ': ' ' + v + ' ' for k, v in zip(origin, t)}
    global record
    global in_macro
    global return_flag
    global has_res_flag
    global break_flag
    global continue_flag
    has_res_flag = False
    jmp = 0
    for i in range(1, len(content) - 1):
        if jmp:
            jmp -= 1
            continue
        if return_flag:
            return_flag = False
            break
        statement = content[i]
        if statement.startswith('macro') and statement.endswith('endmacro'):
            run(statement)
        elif statement.startswith('return ') or statement == 'return':
            if statement == 'return':
                has_res_flag = False
                break
            record = False
            in_macro = True
            run(statement)
            break
        elif statement == 'break' or statement == 'continue':
            break_flag = False
            continue_flag = False
        elif statement.startswith('if'):
            count = 0
            inner_if = []
            success = False
            for j in range(i, len(content) - 1):
                if content[j].startswith('if'):
                    count += 1
                elif content[j] == 'endif':
                    count -= 1
                if not count:
                    success = True
                    for k in range(i, j + 1):
                        inner_if.append(content[k])
                    jmp = j - i
                    break
            if not success:
                record = True
                raise ValueError('if and endif must equal')
            statement = ';'.join(inner_if)
        elif statement.startswith('while'):
            count = 0
            inner_while = []
            success = False
            for j in range(i, len(content) - 1):
                if content[j].startswith('while'):
                    count += 1
                elif content[j] == 'endwhile':
                    count -= 1
                if not count:
                    success = True
                    for k in range(i, j + 1):
                        inner_while.append(content[k])
                    jmp = j - i
                    break
            if not success:
                record = True
                raise ValueError('while and endwhile must equal')
            statement = ';'.join(inner_while)
        for k, v in fact.items():
            statement = statement.replace(k, v)
        record = False
        in_macro = True
        run(statement)
    call_stack.pop()
    in_macro = False
    record = True


def parse_return(order):
    res = order[6:].strip()
    global has_res_flag
    has_res_flag = True
    return_stack.append(replace_variable(res))


def run(order):
    if order == '':
        return
    if record:
        orders.append(order)
    if order.startswith('if') or order.startswith('while') or order.startswith('macro '):
        pass
    else:
        try:
            order = replace_variable(order)
        except Exception as e:
            print('error')
            raise e
    if order == '':
        return
    if order in sample_order:
        sample_order[order]()
    elif order.startswith('set '):
        parse_set(order)
    elif order.startswith('echo '):
        echo(order)
    elif order.startswith('push '):
        push(order)
    elif order.startswith('pop'):
        pop()
    elif order.startswith('hist'):
        hist(order)
    elif order.startswith('reo'):
        if record:
            orders.pop()
        reo(order)
    elif order.startswith('if'):
        if not order.endswith('endif'):
            if record:
                orders.pop()
        get_if(order)
    elif order.startswith('while'):
        if not order.endswith('endwhile'):
            if record:
                orders.pop()
        get_while(order)
    elif order.startswith('inc '):
        inc(order, 1)
    elif order.startswith('dec '):
        inc(order, -1)
    elif order.startswith('appendlist '):
        inner_append(order, 'list')
    elif order.startswith('appenddict '):
        inner_append(order, 'dict')
    elif order.startswith('len '):
        get_len(order)
    elif order.startswith('stack') and order.split()[0] in stack_order:
        stack_order[order.split()[0]](order)
    elif order.startswith('macro '):
        if not order.endswith('endmacro'):
            if record:
                orders.pop()
        get_macro(order)
    elif order.startswith('return '):
        parse_return(order)
    else:
        if record:
            orders.pop()
        raise NameError(f'please enter right order,error:{order}')


while True:
    work_dir = os.getcwd()
    scope['_wd'] = work_dir
    if len(files) == 0 or files[-1] != work_dir:
        files.append(work_dir)
    print(work_dir, end='>')
    order = input().strip()
    if order == '':
        continue
    try:
        run(order)
    except Exception as e:
        print('please enter help to get using assistance')
        print(str(e))
