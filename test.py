# -*- coding: utf-8 -*-

import timeit
from threading import Thread
import cpuinfo

print 'CPU cores:', cpuinfo.info.cpu_count()

print 'Default process affinity:', cpuinfo.affinity.get_affinity()

# test
cnt = 100000000
trying = 2

def count():
    n = cnt
    while n>0:
        n-=1

def test1():
    count()
    count()

def test2():
    t1 = Thread(target=count)
    t1.start()
    t2 = Thread(target=count)
    t2.start()
    t1.join(); t2.join()

def test3():
    cpuinfo.affinity.set_affinity(0,1)
    test2()

seq1 = timeit.timeit( 'test1()', 'from __main__ import test1', number=trying )/trying
print seq1

par1 = timeit.timeit( 'test2()', 'from __main__ import test2', number=trying )/trying
print par1

par2 = timeit.timeit( 'test3()', 'from __main__ import test3', number=trying )/trying
print par2
