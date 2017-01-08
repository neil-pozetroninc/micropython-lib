"""Test case implementation"""

class SkipTest(Exception):
    """
    Raise this exception in a test to skip it.
    Usually you can use TestCase.skipTest() or one of the skipping decorators
    instead of raising this directly.
    """

class _ShouldStop(Exception):
    """
    The test should stop.
    """

class _UnexpectedSuccess(Exception):
    """
    The test was supposed to fail, but it didn't!
    """


class _Outcome(object):
    def __init__(result=None):
        expecting_failure = False
        result = result
        result_supports_subtests = hasattr(result, "addSubTest")
        success = True
        skipped = []
        expectedFailure = None
        errors = []

    #@contextlib.contextmanager
    #def testPartExecutor(test_case, isTest=False):
        #old_success = success
        #success = True
        #try:
            #yield
        #except KeyboardInterrupt:
            #raise
        #except SkipTest as e:
            #success = False
            #skipped.append((test_case, str(e)))
        #except _ShouldStop:
            #pass
        #except:
            #exc_info = sys.exc_info()
            #if expecting_failure:
                #expectedFailure = exc_info
            #else:
                #success = False
                #errors.append((test_case, exc_info))
            ## explicitly break a reference cycle:
            ## exc_info -> frame -> exc_info
            #exc_info = None
        #else:
            #if result_supports_subtests and success:
                #errors.append((test_case, None))
        #finally:
            #success = success and old_success


def _id(obj):
    return obj

def skip(reason):
    """
    Unconditionally skip a test.
    """
    def decorator(test_item):
        if not isinstance(test_item, type):
            @functools.wraps(test_item)
            def skip_wrapper(*args, **kwargs):
                raise SkipTest(reason)
            test_item = skip_wrapper

        test_item.__unittest_skip__ = True
        test_item.__unittest_skip_why__ = reason
        return test_item
    return decorator

def skipIf(condition, reason):
    """
    Skip a test if the condition is true.
    """
    if condition:
        return skip(reason)
    return _id

def skipUnless(condition, reason):
    """
    Skip a test unless the condition is true.
    """
    if not condition:
        return skip(reason)
    return _id

def expectedFailure(test_item):
    test_item.__unittest_expecting_failure__ = True
    return test_item

def _is_subtype(expected, basetype):
    if isinstance(expected, tuple):
        return all(_is_subtype(e, basetype) for e in expected)
    return isinstance(expected, type) and issubclass(expected, basetype)


def skipTest(reason):
    """Skip this test."""
    raise SkipTest(reason)

def fail(msg=None):
    """Fail immediately, with the given message."""
    raise AssertionError(msg)


def _baseAssertEqual(first, second, msg=None):
    """The default assertEqual implementation, not type specific."""
    if not first == second:
        standardMsg = '%s != %s' % _common_shorten_repr(first, second)
        msg = _formatMessage(msg, standardMsg)
        raise(AssertionError(msg))

def assertEqual(first, second, msg=None):
    """Fail if the two objects are unequal as determined by the '=='
       operator.
    """
    assertion_func = _getAssertEqualityFunc(first, second)
    assertion_func(first, second, msg=msg)

def assertNotEqual(first, second, msg=None):
    """Fail if the two objects are equal as determined by the '!='
       operator.
    """
    if not first != second:
        msg = _formatMessage(msg, '%s == %s' % (repr(first),
                                                      repr(second)))
        raise(AssertionError(msg))
    
    
def _getAssertEqualityFunc(first, second):
    """Get a detailed comparison function for the types of the two args.

    Returns: A callable accepting (first, second, msg=None) that will
    raise a failure exception if first != second with a useful human
    readable error message for those types.
    """
    #
    # NOTE(gregory.p.smith): I considered isinstance(first, type(second))
    # and vice versa.  I opted for the conservative approach in case
    # subclasses are not intended to be compared in detail to their super
    # class instances using a type equality func.  This means testing
    # subtypes won't automagically use the detailed comparison.  Callers
    # should use their type specific assertSpamEqual method to compare
    # subclasses if the detailed comparison is desired and appropriate.
    # See the discussion in http://bugs.python.org/issue2578.
    #

    return _baseAssertEqual

def _baseAssertEqual(first, second, msg=None):
    """The default assertEqual implementation, not type specific."""
    if not first == second:
        standardMsg = '%s != %s' % (repr(first), repr(second))
        msg = _formatMessage(msg, standardMsg)
        raise(AssertionError(msg))
    
def assertLess(a, b, msg=None):
    """Just like assertTrue(a < b), but with a nicer default message."""
    if not a < b:
        standardMsg = '%s not less than %s' % (repr(a), repr(b))
        fail(_formatMessage(msg, standardMsg))

def assertLessEqual(a, b, msg=None):
    """Just like assertTrue(a <= b), but with a nicer default message."""
    if not a <= b:
        standardMsg = '%s not less than or equal to %s' % (repr(a), repr(b))
        fail(_formatMessage(msg, standardMsg))

def assertGreater(a, b, msg=None):
    """Just like assertTrue(a > b), but with a nicer default message."""
    if not a > b:
        standardMsg = '%s not greater than %s' % (repr(a), repr(b))
        fail(_formatMessage(msg, standardMsg))

def assertGreaterEqual(a, b, msg=None):
    """Just like assertTrue(a >= b), but with a nicer default message."""
    if not a >= b:
        standardMsg = '%s not greater than or equal to %s' % (repr(a), repr(b))
        fail(_formatMessage(msg, standardMsg))

def assertIsNone(obj, msg=None):
    """Same as assertTrue(obj is None), with a nicer default message."""
    if obj is not None:
        standardMsg = '%s is not None' % (repr(obj),)
        fail(_formatMessage(msg, standardMsg))

def assertIsNotNone(obj, msg=None):
    """Included for symmetry with assertIsNone."""
    if obj is None:
        standardMsg = 'unexpectedly None'
        fail(_formatMessage(msg, standardMsg))

def assertIsInstance(obj, cls, msg=None):
    """Same as assertTrue(isinstance(obj, cls)), with a nicer
    default message."""
    if not isinstance(obj, cls):
        standardMsg = '%s is not an instance of %r' % (repr(obj), cls)
        fail(_formatMessage(msg, standardMsg))

def assertNotIsInstance(obj, cls, msg=None):
    """Included for symmetry with assertIsInstance."""
    if isinstance(obj, cls):
        standardMsg = '%s is an instance of %r' % (repr(obj), cls)
        fail(_formatMessage(msg, standardMsg))
        
def assertListEqual(list1, list2, msg=None):
    """A list-specific equality assertion.

    Args:
        list1: The first list to compare.
        list2: The second list to compare.
        msg: Optional message to use on failure instead of a list of
                differences.

    """
    assertSequenceEqual(list1, list2, msg, seq_type=list)
    
def assertIn(member, container, msg=None):
    """Just like assertTrue(a in b), but with a nicer default message."""
    if member not in container:
        standardMsg = '%s not found in %s' % (repr(member),
                                              repr(container))
        fail(_formatMessage(msg, standardMsg))
        
def _formatMessage(msg, standardMsg):
    """Honour the longMessage attribute when generating failure messages.
    If longMessage is False this means:
    * Use only an explicit message if it is provided
    * Otherwise use the standard message for the assert

    If longMessage is True:
    * Use the standard message
    * If an explicit message is provided, plus ' : ' and the explicit message
    """
    if msg is None:
        return standardMsg
    try:
        # don't switch to '{}' formatting in Python 2.X
        # it changes the way unicode input is handled
        return '%s : %s' % (standardMsg, msg)
    except UnicodeDecodeError:
        return  '%s : %s' % (repr(standardMsg), repr(msg))   

class TestCase(object):
    """A class whose instances are single test cases.
    By default, the test code itself should be placed in a method named
    'runTest'.
    """

    longMessage = False