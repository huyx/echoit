#!/usr/bin/env python
""" Echo calls made to functions and methods in a module.

"Echoing" a function call means printing out the name of the function
and the values of its arguments before making the call (which is more
commonly referred to as "tracing", but Python already has a trace module).

Example: to echo calls made to functions in "my_module" do:

  import echo
  import my_module
  echo.echo_module(my_module)

Example: to echo calls made to functions in "my_module.my_class" do:

  echo.echo_class(my_module.my_class)

Alternatively, echo.echo can be used to decorate functions. Calls to the
decorated function will be echoed.

Example:

  @echo.echo
  def my_function(args):
      pass
"""
import inspect
import sys

_write = sys.stdout.write
_eol = '\n'

def write(string):
    " Wrap output function. "
    _write(string + _eol)

def setup(write, eol):
    """ Customize write method and EndOfLine.

    @param write: write method
    @param eol: end of line
    """
    global _write, _eol
    _write = write
    _eol = eol

def name(item):
    " Return an item's name. "
    return item.__name__

def is_classmethod(instancemethod):
    " Determine if an instancemethod is a classmethod. "
    return instancemethod.im_self is not None

def is_class_private_name(name):
    " Determine if a name is a class private name. "
    # Exclude system defined names such as __init__, __add__ etc
    return name.startswith("__") and not name.endswith("__")

def method_name(method):
    """ Return a method's name.

    This function returns the name the method is accessed by from
    outside the class (i.e. it prefixes "private" methods appropriately).
    """
    mname = name(method)
    if is_class_private_name(mname):
        mname = "_%s%s" % (name(method.im_class), mname)
    return mname

def format_arg_value(arg_val):
    """ Return a string representing a (name, value) pair.

    >>> format_arg_value(('x', (1, 2, 3)))
    'x=(1, 2, 3)'
    """
    arg, val = arg_val
    return "%s=%r" % (arg, val)

def echo(fn):
    """ Echo calls to a function.

    Returns a decorated version of the input function which "echoes" calls
    made to it by writing out the function's name and the arguments it was
    called with.
    """
    import functools
    # Unpack function's arg count, arg names, arg defaults
    code = fn.func_code
    argcount = code.co_argcount
    argnames = code.co_varnames[:argcount]
    fn_defaults = fn.func_defaults or list()
    argdefs = dict(zip(argnames[-len(fn_defaults):], fn_defaults))

    @functools.wraps(fn)
    def wrapped(*v, **k):
        # Collect function arguments by chaining together positional,
        # defaulted, extra positional and keyword arguments.
        positional = map(format_arg_value, zip(argnames, v))
        defaulted = [format_arg_value((a, argdefs[a]))
                     for a in argnames[len(v):] if a not in k]
        nameless = map(repr, v[argcount:])
        keyword = map(format_arg_value, k.items())
        args = positional + defaulted + nameless + keyword
        write("%s(%s)" % (name(fn), ", ".join(args)))
        return fn(*v, **k)
    return wrapped

def echo_instancemethod(klass, method):
    """ Change an instancemethod so that calls to it are echoed.

    Replacing a classmethod is a little more tricky.
    See: http://www.python.org/doc/current/ref/types.html
    """
    mname = method_name(method)
    never_echo = "__str__", "__repr__", # Avoid recursion printing method calls
    if mname in never_echo:
        pass
    elif is_classmethod(method):
        setattr(klass, mname, classmethod(echo(method.im_func)))
    else:
        setattr(klass, mname, echo(method))

def echo_class(klass):
    """ Echo calls to class methods and static functions
    """
    for _, method in inspect.getmembers(klass, inspect.ismethod):
        echo_instancemethod(klass, method)
    for _, fn in inspect.getmembers(klass, inspect.isfunction):
        setattr(klass, name(fn), staticmethod(echo(fn)))

def echo_module(mod):
    """ Echo calls to functions and methods in a module.
    """
    for fname, fn in inspect.getmembers(mod, inspect.isfunction):
        setattr(mod, fname, echo(fn))
    for _, klass in inspect.getmembers(mod, inspect.isclass):
        echo_class(klass)

if __name__ == "__main__":
    import doctest
    optionflags=doctest.ELLIPSIS
    doctest.testfile('echoexample.txt', optionflags=optionflags)
    doctest.testmod(optionflags=optionflags)
