"""Process-local Conda DLL setup; no installed environment is changed."""
import os
import sys
from pathlib import Path
os.environ.setdefault('MKL_THREADING_LAYER', 'SEQUENTIAL')
os.environ.setdefault('MKL_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
_handles = []
if sys.platform == 'win32':
    p = Path(sys.executable).parent / 'Library' / 'bin'
    if p.exists():
        _handles.append(os.add_dll_directory(str(p)))
