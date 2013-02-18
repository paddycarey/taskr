# stdlib imports
import re


def convert_camel_case(name):

    """
    Simple function that'll un-camelcase a string

    eg. SomeClassName -> Some class name
    """

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1)
