# -*- coding: utf-8 -*-
"""
Created on Sun Apr 22 17:59:27 2018
"""

### Useful functions from the web

from functools import reduce

# source: https://stackoverflow.com/a/7359949/4931020
def repeated(f, n):
     def rfun(p):
         return reduce(lambda x, _: f(x), range(n), p)
     return rfun