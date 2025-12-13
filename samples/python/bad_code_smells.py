"""
Sample Bad Python Code #2: Code Smells

This file contains intentionally bad code for testing the AI Code Review Agent.
Issues: Long functions, deep nesting, magic numbers, poor naming
"""

def f(x, y, z, a, b, c, d, e):  # Poor naming, too many arguments
    r = 0
    for i in range(100):
        if x > 0:
            if y > 0:
                if z > 0:
                    if a > 0:
                        if b > 0:
                            if c > 0:
                                if d > 0:
                                    if e > 0:
                                        r = r + x * 3.14159 * 42  # Magic numbers
                                        r = r + 12345
                                        r = r + 98765
    return r

def very_long_function_that_does_too_many_things():
    # Missing docstring
    # This function is way too long and does too many things
    
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    h = 11
    i = 12
    j = 13
    k = 14
    l = 15
    m = 16
    n = 17
    o = 18
    p = 19
    q = 20
    r = 21
    s = 22
    t = 23
    u = 24
    v = 25
    
    result = x + y + z + a + b + c + d + e
    result = result + f + g + h + i + j + k + l
    result = result + m + n + o + p + q + r + s + t + u + v
    
    # TODO: Refactor this mess
    # FIXME: This is terrible code
    
    for item in range(result):
        print(item)
        if item > 50:
            break
    
    return result

class Mgr:  # Poor naming - unclear abbreviation
    def __init__(self):
        self.d = {}  # Poor naming
        self.l = []  # Poor naming
        self.c = 0   # Poor naming
    
    def p(self, x):  # Poor method naming
        self.l.append(x)
        self.c += 1
        self.d[self.c] = x
    
    def g(self, i):  # Poor method naming
        return self.d.get(i)

def calc(n):  # Missing docstring, poor naming
    # Magic numbers everywhere
    return n * 3.14159265359 * 2.71828 + 42 - 13 * 7
