import os
import sys

sys.setrecursionlimit(10000)
import helpFile

work_dir = ''
scope = {}
stack = []
call_stack = []
return_stack = []
macro_map = {}


def get_inner_index(d, index):
    try:
        res = d[index]
    except:
        try:
            res = d[int(index)]
        except:
            try:
                a, b = special_split(index, ':')
                a = None if a == '' else int(a)
                b = None if b == '' else int(b)
                res = d[a:b]
            except:
                return None
    return res


def strip_quotes(address: str):
    if address.startswith('\"') and address.endswith('\"'):
        return address[1:-1].strip()
    if address.startswith('\'') and address.endswith('\''):
        return address[1:-1].strip()
    return address


def my_str(object, inner=0):
    if isinstance(object, dict):
        res = {str(k): my_str(v, 1) for k, v in object.items()}
        return ('\\\\' + str(res)) if inner == 0 else ('\\' + str(res) if inner == 2 else str(res))
    elif isinstance(object, list):
        res = [my_str(i, 2) for i in object]
        return str(res)
    return str(object)


def stackpop(order):
    _, var = order.split(maxsplit=1)
    if len(stack) == 0:
        raise ValueError('stack is empty')
    parse_set(f'set {var} int 0', origin=True, val=stack.pop())


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
        stack.append(replace_variable(var, get=True, keep=True))


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


def replace_variable_only(s: str, keep=False):
    v = parse_macro(s)
    if v:
        run_macro(v)
        res = ''
        global has_res_flag
        if has_res_flag:
            res = return_stack.pop()
            has_res_flag = False
        return my_str(res) if not keep else res
    left = []
    right = []
    for i, j in enumerate(s):
        if j == '[':
            left.append(i)
        elif j == ']':
            right.append(i)

    if left and len(left) == len(right) and left[0] > 0:
        left_arr = left
        right_arr = right
        left = left_arr[0]
        right = right_arr[0]
        d: dict = scope[s[:left]] if s[:left] in scope else s[:left]
        if in_macro:
            for target in reversed(call_stack):
                if s[:left] in target:
                    d = target[s[:left]]
                    break
        index = s[left + 1:right]
        res = get_inner_index(d, index)
        if not res:
            return s
        left_arr = left_arr[1:]
        right_arr = right_arr[1:]
        for left, right in zip(left_arr, right_arr):
            index = s[left + 1:right]
            res = get_inner_index(res, index)
            if not res:
                return s
        if keep:
            return res
        return transform(my_str(res)) if (isinstance(res, dict) or isinstance(res, list)) else my_str(res)

    if in_macro:
        for target in reversed(call_stack):
            if s in target:
                key = target[s]
                if keep:
                    return key
                r = my_str(key)
                return transform(r) if (isinstance(target[s], dict) or isinstance(target[s], list)) else r
    if s in scope:
        if keep:
            return scope[s]
        r = my_str(scope[s])
        return transform(r) if (isinstance(scope[s], dict) or isinstance(scope[s], list)) else r
    return s


prior = {'(': 0, ')': 0, '+': 1, '-': 1, '*': 2, '/': 2, '%': 2, '^': 0.64, '_': 4, '>': 0.7, '<': 0.7, '==': 0.69,
         '<=': 0.7, '>=': 0.7, '&': 0.65, '|': 0.63, '!': 4, '&&': 0.6, '||': 0.5, '!=': 0.69, '**': 3, '~': 4}

lr = {'+': 'left', '-': 'left', '*': 'left', '/': 'left', '%': 'left', '^': 'left', '~': 'right', '>': 'left',
      '<': 'left', '==': 'left', '>=': 'left', '<=': 'left', '&': 'left', '|': 'left', '!': 'right',
      '=': 'this is not a bug', '&&': 'left', '||': 'left', '!=': 'left', '**': 'right', '_': 'right'}


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
    '**': lambda left, right: left ** right,
    '>': lambda left, right: left > right,
    '<': lambda left, right: left < right,
    '>=': lambda left, right: left >= right,
    '<=': lambda left, right: left <= right,
    '==': lambda left, right: left == right,
    '&&': lambda left, right: left and right,
    '||': lambda left, right: left or right,
    '|': lambda left, right: left | right,
    '&': lambda left, right: left & right,
    '!=': lambda left, right: left != right,
    '^': lambda left, right: left ^ right
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
            line = ''.join(num)
            try:
                output.append(int(line))
            except ValueError:
                output.append(float(line))
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
                if operator_ch == '*':
                    while index + 1 < size and s[index + 1] == ' ':
                        index += 1
                    if s[index + 1] == '*':
                        index += 1
                        operator_ch += s[index]
            if len(operator) == 0:
                operator.append(operator_ch)
            else:
                op = operator[-1]
                if expect_operand and s[index] == '-':
                    ch = '_'
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
        if isinstance(token, float) or isinstance(token, int):
            stack.append(token)
        else:
            if token == '_':
                cur = stack.pop()
                stack.append(-cur)
            elif token == '!':
                cur = stack.pop()
                stack.append(int(not cur))
            elif token == '~':
                cur = stack.pop()
                stack.append(~cur)
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
            order = replace_variable(order)
        return order
    res = order
    for s, e in reversed(v):
        t = order[s:e]
        if get_variable(t, '{', '}'):
            t = replace_variable(t)
        res = res[:s] + my_str(calc(t)) + res[e:]
    return res


def replace_variable(order, get=False, keep=False):
    v = get_variable(order, '{', '}')
    if not v:
        if get_variable(order, '(', ')'):
            order = calc_order(order)
        return replace_variable_only(order, keep) if get else order
    res = order
    for s, e in reversed(v):
        t = order[s + 1:e - 1].strip()
        if get_variable(t, '(', ')'):
            t = calc_order(t)
        res = res[:s] + replace_variable_only(replace_variable(t), keep) + res[e:]
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
        s = 1 if s == 'True' else (0 if s == 'False' else s)
        return bool(s)
    return bool(s)


cast = {'int': int, 'float': float, 'str': str, 'dict': get_dict, 'list': get_list, 'bool': get_bool}


def parse_set(order: str, origin=False, val=None):
    global scope
    global in_macro
    order = order.split(maxsplit=3)
    left = []
    right = []
    for i, j in enumerate(order[1]):
        if j == '[':
            left.append(i)
        elif j == ']':
            right.append(i)
    d: dict = scope
    if left and len(left) == len(right) and left[0] > 0:
        start = left[0]
        name = order[1][:start]
        get = False
        if in_macro:
            for target in reversed(call_stack):
                if name in target:
                    d = target[name]
                    get = True
                    break
        if not get:
            d = scope[name]
        left_idx = left[-1]
        right_idx = right[-1]
        left = left[:-1]
        right = right[:-1]
        for start, end in zip(left, right):
            try:
                d = d[order[1][start + 1:end]]
            except:
                try:
                    d = d[int(order[1][start + 1:end])]
                except:
                    try:
                        a, b = special_split(order[1][start + 1:end], ':')
                        a = 0 if a == '' else int(a)
                        b = len(d) if b == '' else int(b)
                        d = d[int(a):int(b)]
                    except:
                        raise KeyError(f'{order[1][start + 1:end]} not a usable index')
        try:
            d[order[1][left_idx + 1:right_idx]] = cast[order[2]](order[3])
            if origin:
                d[order[1][left_idx + 1:right_idx]] = val
        except:
            try:
                d[int(order[1][left_idx + 1:right_idx])] = cast[order[2]](order[3])
                if origin:
                    d[int(order[1][left_idx + 1:right_idx])] = val
            except:
                try:
                    a, b = special_split(order[1][left_idx + 1:right_idx], ':')
                    a = 0 if a == '' else int(a)
                    b = len(d) if b == '' else int(b)
                    d[int(a):int(b)] = cast[order[2]](order[3])
                    if origin:
                        d[int(a):int(b)] = val
                except:
                    raise KeyError(f'{order[1][left_idx + 1:right_idx]} not a usable index')
    else:
        if in_macro:
            d = call_stack[-1]
        d[order[1]] = cast[order[2]](order[3])
        if origin:
            d[order[1]] = val


def push(order):
    os.chdir(order[5:])


help = helpFile.help_str

files = []

orders = []


def print_current_scope():
    global in_macro
    if not in_macro:
        print(scope)
    else:
        print(call_stack[-1])


sample_order = {'exit': lambda: sys.exit(), 'scope': lambda: print_current_scope(),
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


def check_get(s: str, left: str, right: str):
    arr = special_split(s, ';')
    count = 0
    arr = [i for i in arr if i != '']
    if arr[-1] != right:
        return False
    for i in arr:
        if i.startswith(left):
            count += 1
        elif i == right:
            if count == 0:
                return False
            count -= 1
    return count == 0


def run_if(work):
    global record
    save_old_record = record
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
                    record = save_old_record
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
                    record = save_old_record
                    raise ValueError('if and endif must equal')
                statement = ';'.join(inner_while)
            run(statement)
        record = save_old_record


def get_if(order):
    arr = []
    if not check_get(order, 'if', 'endif'):
        arr.append(order)
        count = 0
        limit = 1
        while count != limit:
            cur = input().strip()
            if cur.startswith('#'):
                continue
            arr.append(cur)
            count += cur == 'endif'
            limit += cur.startswith('if')
        work = ';'.join(arr)
        if record:
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
    save_old_record = record
    arr = special_split(work, ';')
    ok = arr[0][5:].strip()
    arr = list(map(lambda x: x.strip(), arr))
    while replace_variable(ok) != '0':
        jmp = 0
        for i in range(1, len(arr) - 1):
            if jmp:
                jmp -= 1
                continue
            if arr[i] == 'break':
                break_flag = True
            elif arr[i] == 'continue':
                continue_flag = True
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
                    record = save_old_record
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
                    record = save_old_record
                    raise ValueError('if and endif must equal')
                statement = ';'.join(inner_if)
            run(statement)
    break_flag = False
    continue_flag = False
    record = save_old_record


def get_while(order):
    arr = []
    if not check_get(order, 'while', 'endwhile'):
        arr.append(order)
        count = 0
        limit = 1
        while count != limit:
            cur = input().strip()
            if cur.startswith('#'):
                continue
            arr.append(cur)
            count += cur == 'endwhile'
            limit += cur.startswith('while')
        work = ';'.join(arr)
        if record:
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
        v = get_variable(var, '[', ']')
        if v:
            first = var[:v[-1][0]]
            index = var[v[-1][0] + 1:v[-1][1] - 1]
            target = replace_variable(first, get=True, keep=True)
            res = target
            if isinstance(target, dict) or isinstance(target, list):
                try:
                    res = target[index]
                    target[index] = int(res) + num
                except:
                    try:
                        res = target[int(index)]
                        target[int(index)] = int(res) + num
                    except:
                        raise KeyError(f'{res} is not a variable that can be plus or sub')
                return
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
            v = get_variable(name, '[', ']')
            if v:
                want = name[:v[-1][0]].strip()
                index = name[v[-1][0] + 1:v[-1][1] - 1].strip()
                arr = replace_variable(want, get=True, keep=True)
                if isinstance(arr, list) or isinstance(arr, dict):
                    try:
                        arr[index].extend(t)
                    except:
                        try:
                            arr[int(index)].extend(t)
                        except:
                            l_r = special_split(index, ':')
                            a = 0
                            b = len(arr)
                            if len(l_r) == 2:
                                if l_r[0] != '':
                                    a = int(l_r[0])
                                if l_r[1] != '':
                                    b = int(l_r[1])
                            ok = True
                            iterable = arr[a:b]
                            for j in iterable:
                                if not isinstance(j, list):
                                    ok = False
                                    break
                            if not ok:
                                raise TypeError(f'the iterable arr from index {a} to {b} not all list')
                            for j in iterable:
                                j.extend(t)
            else:
                d[name] = t
    elif kind == 'dict':
        t = [special_split(i, ':') for i in special_split(content, ',')]
        if name in d and isinstance(d[name], dict):
            for i in t:
                d[name][i[0]] = i[1]
        else:
            v = get_variable(name, '[', ']')
            if v:
                want = name[:v[-1][0]].strip()
                index = name[v[-1][0] + 1:v[-1][1] - 1].strip()
                arr = replace_variable(want, get=True, keep=True)
                if isinstance(arr, list) or isinstance(arr, dict):
                    try:
                        for i in t:
                            arr[index][i[0]] = i[1]
                    except:
                        try:
                            for i in t:
                                arr[int(index)][i[0]] = i[1]
                        except:
                            l_r = special_split(index, ':')
                            a = 0
                            b = len(arr)
                            if len(l_r) == 2:
                                if l_r[0] != '':
                                    a = int(l_r[0])
                                if l_r[1] != '':
                                    b = int(l_r[1])
                            else:
                                raise NameError(f'{index} is invalid key or index')
                            ok = True
                            iterable = arr[a:b]
                            for j in iterable:
                                if not isinstance(j, dict):
                                    ok = False
                                    break
                            if not ok:
                                raise TypeError(f'the iterable arr from index {a} to {b} not all dict')
                            for j in iterable:
                                for i in t:
                                    j[i[0]] = i[1]
            else:
                d[name] = {i[0]: i[1] for i in t}


def get_len(order):
    s = order[3:].strip()
    origin, res = s.split(maxsplit=1)
    v = get_variable(origin, '[', ']')
    d: dict = scope
    global in_macro
    name = origin
    idx = origin
    if v:
        name = origin[:v[-1][0]]
        idx = origin[v[-1][0] + 1:v[-1][1] - 1]
    get = False
    if in_macro:
        for target in reversed(call_stack):
            if v:
                g, t = search(name, target)
                if g:
                    d = t
                    get = True
                    break
            elif origin in target:
                d = target
                get = True
                break
    if not get:
        if v:
            g, t = search(name, scope)
            if g:
                d = t
    out = get_inner_index(d, idx)
    if not out:
        raise ValueError(f'{origin} is not a variable')

    if isinstance(out, list) or isinstance(out, dict) or isinstance(out, str):
        parse_set(f'set {res} int {len(out)}')
    else:
        parse_set(f'set {res} int 1')


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
    if not check_get(order, 'macro', 'endmacro'):
        arr.append(order)
        count = 0
        limit = 1
        while count != limit:
            cur = input().strip()
            if cur.startswith('#'):
                continue
            arr.append(cur)
            count += cur == 'endmacro'
            limit += cur.startswith('macro')
        work = ';'.join(arr)
        if record:
            orders.append(work)
    else:
        work = order
    declare_macro(work)


def run_macro(arr):
    name = arr[0]
    t = arr[1]
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
    for i in range(len(t)):
        get = False
        for target in reversed(call_stack):
            if t[i] in target:
                t[i] = target[t[i]]
                get = True
                break
        if not get:
            if t[i] in scope:
                t[i] = scope[t[i]]
            else:
                t[i] = replace_variable(t[i], get=True, keep=True)
    cur_call_scope = {k: v for k, v in zip(origin, t)}
    call_stack.append(cur_call_scope)
    global record
    global in_macro
    global return_flag
    global has_res_flag
    global break_flag
    global continue_flag
    save_old_macro_flag = in_macro
    save_old_record = record
    save_old_return_flag = return_flag
    return_flag = False
    jmp = 0
    for i in range(1, len(content) - 1):
        if jmp:
            jmp -= 1
            continue
        if return_flag:
            return_flag = save_old_return_flag
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
            continue
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
                record = save_old_record
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
                record = save_old_record
                raise ValueError('while and endwhile must equal')
            statement = ';'.join(inner_while)
        record = False
        in_macro = True
        run(statement)
    call_stack.pop()
    in_macro = save_old_macro_flag
    return_flag = save_old_return_flag
    break_flag = False
    continue_flag = False
    record = save_old_record


def parse_return(order):
    res = order[6:].strip()
    global has_res_flag
    has_res_flag = True
    return_stack.append(res)


def special_iter(order):
    source = order[4:].strip()
    global in_macro
    d: dict = scope if not in_macro else call_stack[-1]
    target = replace_variable(source, get=True, keep=True)
    if not isinstance(target, dict):
        raise ValueError(f'{source} not a dict')
    d['_iter_arr'] = [(k, v) for k, v in target.items()]
    d['_iter_arr_index'] = 0
    d['_key'] = d['_iter_arr'][0][0]
    d['_val'] = d['_iter_arr'][0][1]
    d['_hasnext'] = d['_iter_arr_index'] < len(d['_iter_arr'])


def iter_next():
    d = scope
    global in_macro
    if in_macro:
        for t in reversed(call_stack):
            if '_iter_arr' in t:
                d = t
                break
    if '_iter_arr' not in d:
        return
    d['_iter_arr_index'] += 1
    d['_hasnext'] = d['_iter_arr_index'] < len(d['_iter_arr'])
    if d['_hasnext']:
        d['_key'] = d['_iter_arr'][d['_iter_arr_index']][0]
        d['_val'] = d['_iter_arr'][d['_iter_arr_index']][1]


stdin = []

imp_re = []
imp_flags = []

in_import = False


def import_file(order):
    address = order[6:].strip()
    stdin.append(sys.stdin)
    f = open(strip_quotes(address), 'r', encoding='utf8')
    global record
    imp_re.append(record)
    global in_import
    imp_flags.append(in_import)
    in_import = True
    record = False
    sys.stdin = f


def delete(order):
    name = order[3:].strip()
    arr = name.split(maxsplit=1)
    local = True
    name = arr[0]
    if len(arr) > 1:
        if arr[0] == 'global':
            local = False
            name = arr[1]
        else:
            raise NameError(f'{order} is a invalid order')
    global in_macro
    if not local:
        d = scope
        for target in reversed(call_stack):
            if name in target:
                d = target
                break
        if name in d:
            try:
                d.pop(name)
                return
            except:
                pass
        try:
            d.pop(int(name))
            return
        except:
            pass
        v = get_variable(name, '[', ']')
        if not v:
            return
        s = name[:v[-1][0]]
        target = replace_variable(s, get=True, keep=True)
        try:
            target.pop(name[v[-1][0] + 1:v[-1][1] - 1])
            return
        except:
            try:
                target.pop(int(name[v[-1][0] + 1:v[-1][1] - 1]))
                return
            except:
                pass
    else:
        d = scope if not in_macro else call_stack[-1]
        if name in d:
            try:
                d.pop(name)
                return
            except:
                pass
        try:
            d.pop(int(name))
            return
        except:
            pass
        v = get_variable(name, '[', ']')
        if not v:
            return
        s = name[:v[-1][0]]
        res, map = search(s, d)
        if res:
            if name[v[-1][0] + 1:v[-1][1] - 1] in map:
                try:
                    map.pop(name[v[-1][0] + 1:v[-1][1] - 1])
                    return
                except:
                    pass
            try:
                map.pop(int(name[v[-1][0] + 1:v[-1][1] - 1]))
            except:
                pass


def haskey(order):
    s = order[6:].strip()
    name, key, var = s.split(maxsplit=3)
    d: dict = scope
    global in_macro
    if in_macro:
        for target in reversed(call_stack):
            if name in target:
                d = target
                break
    if name in d and isinstance(d[name], dict):
        res = key in d[name]
        parse_set(f'set {var} bool {1 if res else 0}')
        return
    map = replace_variable(name, get=True, keep=True)
    if isinstance(map, dict):
        parse_set(f'set {var} bool {1 if key in map else 0}')
    else:
        parse_set(f'set {var} bool {0}')


def search(name, d):
    v = get_variable(name, '[', ']')
    if not v:
        s = name
    else:
        s = name[:v[0][0]]
    d = get_inner_index(d, s)
    if not d:
        return False, 0
    for s, e in v:
        key = name[s + 1:e - 1]
        d = get_inner_index(d, key)
        if not d:
            return False, 0
    return True, d


def delete_key(order):
    s = order[6:].strip()
    arr = s.split(maxsplit=3)
    local = True
    if len(arr) == 3:
        if arr[0] == 'global':
            local = False
            name = arr[1]
            key = arr[2]
        else:
            raise NameError(f'{order} is a invalid order')
    elif len(arr) == 2:
        name = arr[0]
        key = arr[1]
    else:
        raise TypeError(f'{order} is a invalid order')
    global in_macro
    if not local:
        d = scope
        if in_macro:
            for target in reversed(call_stack):
                if name in target:
                    d = target
                    break
        if name in d and isinstance(d[name], dict):
            if key in d[name]:
                d[name].pop(key)
                return
        map = replace_variable(name, get=True, keep=True)
        if isinstance(map, dict):
            if key in map:
                map.pop(key)
        else:
            raise NameError(f'can not find a dict called {name} in global')
    else:
        d = call_stack[-1] if in_macro else scope
        res, map = search(name, d)
        if res:
            if key in map:
                map.pop(key)
        else:
            raise NameError(f'can not find a dict called {name} in local')


def delete_index(order):
    temp = order[8:].strip().split(maxsplit=2)
    local = True
    if len(temp) == 3:
        if temp[0] == 'global':
            local = False
            name = temp[1]
            idx = temp[2]
        else:
            raise NameError(f'{order} is a invalid order')
    elif len(temp) == 2:
        name = temp[0]
        idx = temp[1]
    else:
        raise TypeError(f'{order} is a invalid order')
    global in_macro
    if not local:
        d: dict = scope
        if in_macro:
            for target in reversed(call_stack):
                if name in target:
                    d = target
                    break
        if name in d:
            arr = d[name]
            if isinstance(arr, list):
                arr.pop(int(idx))
            else:
                raise TypeError(f'{name} is not a list')
        else:
            v = get_variable(name, '[', ']')
            if v:
                want = name[:v[-1][0]].strip()
                prev_index = name[v[-1][0] + 1:v[-1][1] - 1].strip()
                target = replace_variable(want, get=True, keep=True)
                try:
                    arr = target[prev_index]
                except:
                    arr = target[int(prev_index)]
                if isinstance(arr, list):
                    arr.pop(int(idx))
                else:
                    raise TypeError(f'{name} is not a list')
    else:
        d = scope if not in_macro else call_stack[-1]
        if name in d:
            arr = d[name]
            if isinstance(arr, list):
                arr.pop(int(idx))
            else:
                raise TypeError(f'{name} is not a list')
        else:
            v = get_variable(name, '[', ']')
            if v:
                want = name[:v[-1][0]].strip()
                prev_index = name[v[-1][0] + 1:v[-1][1] - 1].strip()
                res, target = search(want, d)
                if not res:
                    raise NameError(f'{name} is not a variable in local')
                try:
                    arr = target[prev_index]
                except:
                    try:
                        arr = target[int(prev_index)]
                    except:
                        raise NameError(f'{name} is not a variable in local')
                if isinstance(arr, list):
                    arr.pop(int(idx))
                else:
                    raise TypeError(f'{name} is not a list')
            else:
                raise NameError(f'{name} is not a variable in local')


def histc(order):
    global orders
    if order == 'histc':
        orders = []
    else:
        num = int(order[5:].strip())
        orders = orders[num:]


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
            print(f'error,when command {order},because {str(e)}')
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
    elif order.startswith('histc'):
        histc(order)
    elif order.startswith('reo'):
        if record:
            orders.pop()
        if not in_import:
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
    elif order.startswith('iter '):
        special_iter(order)
    elif order == 'next':
        iter_next()
    elif order.startswith('import '):
        import_file(order)
    elif order.startswith('del '):
        delete(order)
    elif order.startswith('hist'):
        hist(order)
    elif order.startswith('haskey'):
        haskey(order)
    elif order.startswith('delkey'):
        delete_key(order)
    elif order.startswith('delindex'):
        delete_index(order)
    else:
        if record:
            orders.pop()
        raise NameError(f'please enter right order,error:{order}')


while True:
    work_dir = os.getcwd()
    scope['_wd'] = work_dir
    if len(files) == 0 or files[-1] != work_dir:
        files.append(work_dir)
    if sys.stdin == sys.__stdin__:
        print(work_dir, end='>')
    try:
        order = input().strip()
    except EOFError:
        sys.stdin.close()
        sys.stdin = stdin.pop()
        order = ''
        record = imp_re.pop()
        in_import = imp_flags.pop()
    if order == '':
        continue
    if order.startswith('#'):
        continue
    try:
        run(order)
    except EOFError:
        sys.stdin.close()
        sys.stdin = stdin.pop()
        order = ''
        record = imp_re.pop()
        in_import = imp_flags.pop()
    except Exception:
        print('please enter help to get using assistance')
        record = True
        break_flag = False
        continue_flag = False
        call_stack = []
        return_stack = []
        has_res_flag = False
        return_flag = False
        in_macro = False
        sys.stdin = sys.__stdin__
        imp_re = []
        imp_flags = []
