#
# Copyright (c), 2018-2020, SISSA (International School for Advanced Studies).
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
#
# @author Davide Brunato <brunato@sissa.it>
#
"""
Subpackage for processing regular expression. Patterns are translated to an
equivalent Python's regex pattern with get_python_pattern().

XPath/XQuery/XML-Schema regex flavors are supported through get_python_pattern()
options. Default options process XPath/XQuery patterns.
"""
from .codepoints import iter_code_points
from .unicode_subsets import RegexError, UnicodeSubset, UNICODE_CATEGORIES, UNICODE_BLOCKS
from .character_classes import I_SHORTCUT_REPLACE, C_SHORTCUT_REPLACE, CharacterClass
from .patterns import get_python_pattern

__all__ = ['UNICODE_CATEGORIES', 'UNICODE_BLOCKS', 'I_SHORTCUT_REPLACE',
           'C_SHORTCUT_REPLACE', 'get_python_pattern', 'RegexError',
           'UnicodeSubset', 'CharacterClass', 'iter_code_points']