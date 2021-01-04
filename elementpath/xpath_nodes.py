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
Helper functions for XPath nodes and basic data types.
"""
from urllib.parse import urlparse
from abc import ABC, abstractmethod
from typing import Union, Any, Optional
from xml.etree.ElementTree import Element

from .namespaces import XML_BASE, XSI_NIL
from .exceptions import ElementPathValueError


###
# Node types
class XPathNode(ABC):

    name = None
    value = None

    @property
    @abstractmethod
    def kind(self):
        raise NotImplementedError


class AttributeNode(XPathNode):
    """
    A class for processing XPath attribute nodes.

    :param name: the attribute name.
    :param value: a string value or an XSD attribute when XPath is applied on a schema.
    :param parent: the parent element.
    """
    def __init__(self, name: str, value: Union[str, Any], parent: Optional[Element] = None):
        self.name = name
        self.value = value
        self.parent = parent

    @property
    def kind(self):
        return 'attribute'

    def as_item(self):
        return self.name, self.value

    def __repr__(self):
        if self.parent is not None:
            return '%s(name=%r, value=%r, parent=%r)' % (
                self.__class__.__name__, self.name, self.value, self.parent
            )
        return '%s(name=%r, value=%r)' % (self.__class__.__name__, self.name, self.value)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.name == other.name and \
            self.value == other.value and \
            self.parent is other.parent

    def __hash__(self):
        return hash((self.name, self.value, self.parent))


class TextNode(XPathNode):
    """
    A class for processing XPath text nodes. An Element's property
    (elem.text or elem.tail) with a `None` value is not a text node.

    :param value: a string value.
    :param parent: the parent element.
    :param tail: provide `True` if the text node is the parent Element's tail.
    """
    _tail = False

    def __init__(self, value: str, parent: Optional[Element] = None, tail=False):
        self.value = value
        self.parent = parent
        if tail and parent is not None:
            self._tail = True

    @property
    def kind(self):
        return 'text'

    def is_tail(self):
        """Returns `True` if the node has a parent and represents the tail text."""
        return self._tail

    def __repr__(self):
        if self.parent is not None:
            return '%s(%r, parent=%r, tail=%r)' % (
                self.__class__.__name__, self.value, self.parent, self._tail
            )
        return '%s(%r)' % (self.__class__.__name__, self.value)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.value == other.value and \
            self.parent is other.parent and \
            self._tail is other._tail

    def __hash__(self):
        return hash((self.value, self.parent, self._tail))


class NamespaceNode(XPathNode):
    """
    A class for processing XPath namespace nodes.

    :param prefix: the namespace prefix.
    :param uri: the namespace URI.
    :param parent: the parent element.
    """
    def __init__(self, prefix: str, uri: str, parent: Optional[Element] = None):
        self.prefix = prefix
        self.uri = uri
        self.parent = parent

    @property
    def kind(self):
        return 'namespace'

    @property
    def name(self):
        return self.prefix

    @property
    def value(self):
        return self.uri

    def as_item(self):
        return self.prefix, self.uri

    def __repr__(self):
        if self.parent is not None:
            return '%s(prefix=%r, uri=%r, parent=%r)' % (
                self.__class__.__name__, self.prefix, self.uri, self.parent
            )
        return '%s(prefix=%r, uri=%r)' % (self.__class__.__name__, self.prefix, self.uri)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.prefix == other.prefix and \
            self.uri == other.uri and \
            self.parent is other.parent

    def __hash__(self):
        return hash((self.prefix, self.uri, self.parent))


class TypedElement(XPathNode):
    """
    A class for processing typed element nodes.

    :param elem: the linked element. Can be an Element, or an XSD element \
    when XPath is applied on a schema.
    :param xsd_type: the reference XSD type.
    :param value: the decoded value. Can be `None` for empty or element-only elements."
    """
    def __init__(self, elem: Element, xsd_type: Any, value: Any):
        self.elem = elem
        self.xsd_type = xsd_type
        self.value = value

    @property
    def kind(self):
        return 'element'

    @property
    def name(self):
        return self.elem.tag

    def __repr__(self):
        return '%s(tag=%r)' % (self.__class__.__name__, self.elem.tag)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.elem is other.elem and \
            self.value == other.value

    def __hash__(self):
        return hash((self.elem, self.value))


class TypedAttribute(XPathNode):
    """
    A class for processing typed attribute nodes.

    :param attribute: the origin AttributeNode instance.
    :param xsd_type: the reference XSD type.
    :param value: the types value.
    """
    def __init__(self, attribute: AttributeNode, xsd_type: Any, value: Any):
        self.attribute = attribute
        self.xsd_type = xsd_type
        self.value = value

    @property
    def kind(self):
        return 'attribute'

    @property
    def name(self):
        return self.attribute.name

    def as_item(self):
        return self.attribute.name, self.value

    def __repr__(self):
        return '%s(name=%r)' % (self.__class__.__name__, self.attribute.name)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.attribute == other.attribute and \
            self.value == other.value

    def __hash__(self):
        return hash((self.attribute, self.value))


###
# Utility functions for ElementTree's Element instances
def is_etree_element(obj):
    return hasattr(obj, 'tag') and hasattr(obj, 'attrib') and hasattr(obj, 'text')


def etree_iter_nodes(root, with_root=True, with_attributes=False):
    if isinstance(root, TypedElement):
        root = root.elem
    elif is_document_node(root) and with_root:
        yield root

    for e in root.iter():
        if callable(e.tag):
            continue  # is a comment or a process instruction
        if with_root or e is not root:
            yield e
        if e.text is not None:
            yield TextNode(e.text, e)
        if e.attrib and with_attributes:
            yield from map(lambda x: AttributeNode(*x, parent=e), e.attrib.items())
        if e.tail is not None and e is not root:
            yield TextNode(e.tail, e, True)


def etree_iter_strings(elem):
    if isinstance(elem, TypedElement):
        if elem.xsd_type.is_element_only():
            # Element-only text content is normalized
            elem = elem.elem
            for e in elem.iter():
                if callable(e.tag):
                    continue
                if e.text is not None:
                    yield e.text.strip() if e is elem else e.text
                if e.tail is not None and e is not elem:
                    yield e.tail.strip() if e in elem else e.tail
            return

        elem = elem.elem

    for e in elem.iter():
        if callable(e.tag):
            continue
        if e.text is not None:
            yield e.text
        if e.tail is not None and e is not elem:
            yield e.tail


def etree_deep_equal(e1, e2):
    if e1.tag != e2.tag:
        return False
    elif (e1.text or '').strip() != (e2.text or '').strip():
        return False
    elif (e1.tail or '').strip() != (e2.tail or '').strip():
        return False
    elif e1.attrib != e2.attrib:
        return False
    elif len(e1) != len(e2):
        return False
    return all(etree_deep_equal(c1, c2) for c1, c2 in zip(e1, e2))


###
# XPath node test functions
#
# XPath has there are 7 kinds of nodes:
#
#  element, attribute, text, namespace, processing-instruction, comment, document
#
# Element-like objects are used for representing elements and comments,
# ElementTree-like objects for documents. XPathNode subclasses are used
# for representing other node types and typed elements/attributes.
###
def match_element_node(obj, tag=None):
    """
    Returns `True` if the first argument is an element node matching the tag, `False` otherwise.
    Raises a ValueError if the argument tag has to be used but it's in a wrong format.

    :param obj: the node to be tested.
    :param tag: a fully qualified name, a local name or a wildcard. The accepted
    wildcard formats are '*', '*:*', '*:local-name' and '{namespace}*'.
    """
    if isinstance(obj, TypedElement):
        obj = obj.elem
    elif not is_etree_element(obj) or callable(obj.tag):
        return False

    if not tag:
        return True
    elif not obj.tag:
        return obj.tag == tag
    elif tag == '*' or tag == '*:*':
        return obj.tag != ''
    elif tag[0] == '*':
        try:
            _, name = tag.split(':')
        except (ValueError, IndexError):
            raise ElementPathValueError("unexpected format %r for argument 'tag'" % tag)
        else:
            if obj.tag[0] == '{':
                return obj.tag.split('}')[1] == name
            else:
                return obj.tag == name

    elif tag[-1] == '*':
        if tag[0] != '{' or '}' not in tag:
            raise ElementPathValueError("unexpected format %r for argument 'tag'" % tag)
        elif obj.tag[0] == '{':
            return obj.tag.split('}')[0][1:] == tag.split('}')[0][1:]
        else:
            return False
    else:
        return obj.tag == tag


def match_attribute_node(obj, name=None):
    """
    Returns `True` if the first argument is an attribute node matching the name, `False` otherwise.
    Raises a ValueError if the argument name has to be used but it's in a wrong format.

    :param obj: the node to be tested.
    :param name: a fully qualified name, a local name or a wildcard. The accepted wildcard formats \
    are '*', '*:*', '*:local-name' and '{namespace}*'.
    """
    if name is None or name == '*' or name == '*:*':
        return isinstance(obj, (AttributeNode, TypedAttribute))
    elif not isinstance(obj, (AttributeNode, TypedAttribute)):
        return False
    elif isinstance(obj, TypedAttribute):
        obj = obj.attribute

    if name[0] == '*':
        try:
            _, _name = name.split(':')
        except (ValueError, IndexError):
            raise ElementPathValueError("unexpected format %r for argument 'name'" % name)
        else:
            if obj.name[0] == '{':
                return obj.name.split('}')[1] == _name
            else:
                return obj.name == _name

    elif name[-1] == '*':
        if name[0] != '{' or '}' not in name:
            raise ElementPathValueError("unexpected format %r for argument 'name'" % name)
        elif obj.name[0] == '{':
            return obj.name.split('}')[0][1:] == name.split('}')[0][1:]
        else:
            return False
    else:
        return obj.name == name


def is_element_node(obj):
    return isinstance(obj, TypedElement) or \
        hasattr(obj, 'tag') and not callable(obj.tag) and \
        hasattr(obj, 'attrib') and hasattr(obj, 'text')


def is_schema_node(obj):
    return hasattr(obj, 'local_name') and hasattr(obj, 'type') and hasattr(obj, 'name')


def is_comment_node(obj):
    return hasattr(obj, 'tag') and callable(obj.tag) and obj.tag.__name__ == 'Comment'


def is_processing_instruction_node(obj):
    return hasattr(obj, 'tag') and callable(obj.tag) and obj.tag.__name__ == 'ProcessingInstruction'


def is_document_node(obj):
    return hasattr(obj, 'getroot') and hasattr(obj, 'parse') and hasattr(obj, 'iter')


def is_xpath_node(obj):
    return isinstance(obj, XPathNode) or \
        hasattr(obj, 'tag') and hasattr(obj, 'attrib') and hasattr(obj, 'text') or \
        hasattr(obj, 'local_name') and hasattr(obj, 'type') and hasattr(obj, 'name') or \
        hasattr(obj, 'getroot') and hasattr(obj, 'parse') and hasattr(obj, 'iter')


###
# Node accessors: in this implementation node accessors return None instead of empty sequence.
# Ref: https://www.w3.org/TR/xpath-datamodel-31/#dm-document-uri
def node_attributes(obj):
    if is_element_node(obj):
        return obj.attrib


def node_base_uri(obj):
    try:
        if is_element_node(obj):
            return obj.attrib[XML_BASE]
        elif is_document_node(obj):
            return obj.getroot().attrib[XML_BASE]
    except KeyError:
        pass


def node_document_uri(obj):
    if is_document_node(obj):
        try:
            uri = obj.getroot().attrib[XML_BASE]
            parts = urlparse(uri)
        except (KeyError, ValueError):
            pass
        else:
            if parts.scheme and parts.netloc or parts.path.startswith('/'):
                return uri


def node_children(obj):
    if is_element_node(obj):
        return (child for child in obj)
    elif is_document_node(obj):
        return (child for child in [obj.getroot()])


def node_nilled(obj):
    if is_element_node(obj):
        return obj.get(XSI_NIL) in ('true', '1')


def node_kind(obj):
    if isinstance(obj, XPathNode):
        return obj.kind
    elif is_element_node(obj):
        return 'element'
    elif is_document_node(obj):
        return 'document-node'
    elif is_comment_node(obj):
        return 'comment'
    elif is_processing_instruction_node(obj):
        return 'processing-instruction'


def node_name(obj):
    if isinstance(obj, XPathNode):
        return obj.name
    elif hasattr(obj, 'tag') and not callable(obj.tag) \
            and hasattr(obj, 'attrib') and hasattr(obj, 'text'):
        return obj.tag
