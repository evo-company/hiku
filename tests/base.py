try:
    from unittest.mock import patch as _patch, Mock as _Mock
except ImportError:
    from mock import patch as _patch, Mock as _Mock


patch = _patch
Mock = _Mock
