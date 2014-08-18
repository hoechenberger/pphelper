#!/usr/bin/env python

import sys

try:
    import pytest
except ImportError:
    raise sys.exit('Could not import pytest.')


if __name__ == '__main__':
    sys.exit(pytest.main())
