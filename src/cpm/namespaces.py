"""Shared namespace configuration and helpers for CPM modules."""

from typing import Any

from prov.model import ProvBundle, ProvDocument


CPM_NAMESPACE_URI = "https://commonprovenancemodel.org/ns/cpm/"
DCT_NAMESPACE_URI = "http://purl.org/dc/terms/"
PROV_NAMESPACE_URI = "http://www.w3.org/ns/prov#"
XSD_NAMESPACE_URI = "http://www.w3.org/2001/XMLSchema#"

EXAMPLE_NAMESPACE_PREFIX = "ex"
EXAMPLE_NAMESPACE_URI = "http://example.org/"

DEFAULT_NAMESPACE_PREFIX = "default"
DEFAULT_NAMESPACE_URI = f"{EXAMPLE_NAMESPACE_URI}{DEFAULT_NAMESPACE_PREFIX}/"

ATTRIBUTE_NAMESPACE_PREFIX = "attr"
ATTRIBUTE_NAMESPACE_URI = f"{EXAMPLE_NAMESPACE_URI}{ATTRIBUTE_NAMESPACE_PREFIX}/"

BUNDLE_NAMESPACE_PREFIX = "bundle_ns"
BUNDLE_NAMESPACE_URI = f"{EXAMPLE_NAMESPACE_URI}bundle/"

DEFAULT_CPM_NAMESPACES = {
    "cpm": CPM_NAMESPACE_URI,
    "dct": DCT_NAMESPACE_URI,
    "prov": PROV_NAMESPACE_URI,
    "xsd": XSD_NAMESPACE_URI,
}


def build_example_namespace_uri(prefix: str) -> str:
    """Build a stable example namespace URI for dynamic prefixes."""
    return f"{EXAMPLE_NAMESPACE_URI}{prefix}/"


def get_namespace_uri(prefix: str) -> str:
    """Return the canonical URI for known prefixes or an example URI otherwise."""
    return DEFAULT_CPM_NAMESPACES.get(prefix, build_example_namespace_uri(prefix))


def get_document(bundle_or_document: Any) -> ProvDocument:
    """Return the owning document for a bundle-like object."""
    if isinstance(bundle_or_document, ProvDocument):
        return bundle_or_document
    if isinstance(bundle_or_document, ProvBundle):
        if getattr(bundle_or_document, "_document", None) is not None:
            return bundle_or_document._document
        if getattr(bundle_or_document, "document", None) is not None:
            return bundle_or_document.document
    return bundle_or_document


def get_namespace_by_prefix(document: ProvDocument, prefix: str):
    """Return the namespace registered under the given prefix, if any."""
    for namespace in document.namespaces:
        if namespace.prefix == prefix:
            return namespace
    return None


def ensure_namespace(document: ProvDocument, prefix: str, uri: str):
    """Return an existing namespace or register it when missing."""
    namespace = get_namespace_by_prefix(document, prefix)
    if namespace is not None:
        return namespace
    return document.add_namespace(prefix, uri)