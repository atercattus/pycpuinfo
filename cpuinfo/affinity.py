# -*- coding: utf-8 -*-

import os
import ctypes

def __search_so(name):
    directories = ['/lib', '/usr/lib']

    res = []
    for dir in directories:
        if os.path.isdir(dir):
            for file in os.listdir(dir):
                if file.startswith(name):
                    res.append( os.path.join(dir, file) )
    return res

def __load_libc():
    pathes = __search_so('libc.so')
    _libc = None
    for path in pathes:
        try:
            return ctypes.CDLL( path )
        except OSError:
            pass

try:
    u"""
        Linux + ctypes.<libc>
    """
    _libc = __load_libc()
    if not _libc:
        raise ImportError # not Linux
    
    if _libc.sched_getaffinity and _libc.sched_setaffinity:
        __setaffinity = _libc.sched_setaffinity
        __setaffinity.argtypes = [ctypes.c_int, ctypes.c_size_t, ctypes.POINTER(ctypes.c_ulong)]
        __getaffinity = _libc.sched_getaffinity
        __getaffinity.argtypes = [ctypes.c_int, ctypes.c_size_t, ctypes.POINTER(ctypes.c_ulong)]

    def get_affinity(pid=0):
        mask = ctypes.c_ulong(0)
        c_ulong_size = ctypes.sizeof(ctypes.c_ulong)
        if __getaffinity(pid, c_ulong_size, mask) < 0:
            raise OSError
        return mask.value

    def set_affinity(pid=0, mask=1):
        mask = ctypes.c_ulong(mask)
        c_ulong_size = ctypes.sizeof(ctypes.c_ulong)
        if __setaffinity(pid, c_ulong_size, mask) < 0:
            raise OSError
        return

except (ImportError,AttributeError):
    try:
        u"""
            Windows + pywin32
        """
        import win32process, win32con, win32api, win32security
        import os

        def __open_process(pid,ro=True):
            if not pid:
                pid = os.getpid()
            
            access = win32con.PROCESS_QUERY_INFORMATION
            if not ro:
                access |= win32con.PROCESS_SET_INFORMATION
            
            hProc = win32api.OpenProcess(access, 0, pid)
            if not hProc:
                raise OSError
            return hProc
        
        def get_affinity(pid=0):
            hProc = __open_process(pid)
            mask, mask_sys = win32process.GetProcessAffinityMask(hProc)
            win32api.CloseHandle(hProc)
            return mask

        def set_affinity(pid=0, mask=1):
            try:
                hProc = __open_process(pid, ro=False)
                mask_old, mask_sys_old = win32process.GetProcessAffinityMask(hProc)
                res = win32process.SetProcessAffinityMask(hProc, mask)
                win32api.CloseHandle(hProc)
                if res:
                    raise OSError
            except win32process.error as e:
                raise ValueError, e
            return mask_old

    except (ImportError, AttributeError):
        try:
            u"""
                Windows + ctypes.windll
            """
            import ctypes
            import os
            PROCESS_SET_INFORMATION   =  512
            PROCESS_QUERY_INFORMATION = 1024

            __setaffinity = ctypes.windll.kernel32.SetProcessAffinityMask
            __setaffinity.argtypes = [ctypes.c_uint, ctypes.c_uint]

            __getaffinity = ctypes.windll.kernel32.GetProcessAffinityMask
            __getaffinity.argtypes = [ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]

            __close_handle = ctypes.windll.kernel32.CloseHandle

            def __open_process(pid,ro=True):
                if not pid:
                    pid = os.getpid()
                
                access = PROCESS_QUERY_INFORMATION
                if not ro:
                    access |= PROCESS_SET_INFORMATION
                
                hProc = ctypes.windll.kernel32.OpenProcess(access, 0, pid)
                if not hProc:
                    raise OSError
                return hProc
            
            def get_affinity(pid=0):
                hProc = __open_process(pid)
                
                mask_proc = ctypes.c_uint(0)
                mask_sys  = ctypes.c_uint(0)
                if not __getaffinity(hProc, mask_proc, mask_sys):
                    raise ValueError

                __close_handle(hProc)
                
                return mask_proc.value

            def set_affinity(pid=0, mask=1):
                hProc = __open_process(pid, ro=False)

                mask_proc = ctypes.c_uint(mask)
                res = __setaffinity(hProc, mask_proc)
                __close_handle(hProc)
                if not res:
                    raise OSError
                return
            
        except (ImportError, AttributeError) as e:
            u"""
                Not implemented yet
            """
            def get_affinity(pid=0):
                raise NotImplementedError
            
            def set_affinity(pid=0, mask=1):
                raise NotImplementedError
