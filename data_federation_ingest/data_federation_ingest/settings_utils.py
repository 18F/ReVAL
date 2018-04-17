import os
import sys
import json
from typing import List, Optional

Environ = os._Environ


def is_running_tests(argv: List[str]=sys.argv) -> bool:
    '''
    Returns whether or not we're running tests.
    '''

    basename = os.path.basename(argv[0])
    first_arg = argv[1] if len(argv) > 1 else None

    if basename == 'manage.py' and first_arg == 'test':
        return True
    if basename == 'py.test' or basename == 'pytest':
        return True

    return False
