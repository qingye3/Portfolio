__author__ = 'qingye3'

from bad_words import bad_words
import re


def replace(match):
    """
    replacer for re.sub
    :param match: re.match object
    :return: replacing string
    """
    bad_word = match.group()
    return bad_word[0] + '*'*(len(bad_word) - 2) + bad_word[-1]


def filter(text):
    """
    replace bad words in the text with clean words
    :param text: text to be filtered
    :return: filtered words
    """
    regex = re.compile(r'\b(%s)\b' % "|".join(bad_words), re.IGNORECASE)
    return regex.sub(replace, text)
