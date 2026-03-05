"""
CPM Constants and Namespace Definitions

Based on the Common Provenance Model specification as described in the 
Reference Implementation thesis by Bc. Dávid Laurovič.
"""

from prov.identifier import Namespace, QualifiedName

# CPM Namespace
CPM_NAMESPACE_URI = "https://commonprovenancemodel.org/ns/cpm/"
CPM = Namespace("cpm", CPM_NAMESPACE_URI)

# DCT (Dublin Core Terms) Namespace - used for dct:hasPart
DCT_NAMESPACE_URI = "http://purl.org/dc/terms/"
DCT = Namespace("dct", DCT_NAMESPACE_URI)

# CPM Subtypes (prov:type values)
CPM_MAIN_ACTIVITY = CPM["MainActivity"]
CPM_BACKWARD_CONNECTOR = CPM["BackwardConnector"]
CPM_FORWARD_CONNECTOR = CPM["ForwardConnector"]
CPM_SENDER_AGENT = CPM["SenderAgent"]
CPM_RECEIVER_AGENT = CPM["ReceiverAgent"]
CPM_IDENTIFIER_ENTITY = CPM["IdentifierEntity"]
CPM_SUB_ACTIVITY = CPM["SubActivity"]
CPM_STORAGE_ACTIVITY = CPM["StorageActivity"]

# CPM Attributes
CPM_REFERENCED_BUNDLE_ID = CPM["referencedBundleId"]
CPM_REFERENCED_BUNDLE_HASH_VALUE = CPM["referencedBundleHashValue"]
CPM_REFERENCED_META_BUNDLE_ID = CPM["referencedMetaBundleId"]
CPM_HASH_ALG = CPM["hashAlg"]
CPM_EXTERNAL_ID = CPM["externalId"]
CPM_EXTERNAL_ID_TYPE = CPM["externalIdType"]
CPM_PROVENANCE_SERVICE_URI = CPM["provenanceServiceUri"]
CPM_CONTACT_ID_PID = CPM["contactIdPid"]
CPM_COMMENT = CPM["comment"]

# DCT Attributes
DCT_HAS_PART = DCT["hasPart"]

# Default CPM namespaces
DEFAULT_CPM_NAMESPACES = {
    "cpm": CPM_NAMESPACE_URI,
    "dct": DCT_NAMESPACE_URI,
    "prov": "http://www.w3.org/ns/prov#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
}

# CPM Traversal Information attributes (allowed in TI part)
CPM_TI_ALLOWED_ATTRIBUTES = {
    CPM_REFERENCED_BUNDLE_ID,
    CPM_REFERENCED_BUNDLE_HASH_VALUE,
    CPM_REFERENCED_META_BUNDLE_ID,
    CPM_HASH_ALG,
    DCT_HAS_PART
}

# CPM Subtypes for validation
CPM_SUBTYPES = {
    CPM_MAIN_ACTIVITY,
    CPM_BACKWARD_CONNECTOR,
    CPM_FORWARD_CONNECTOR,
    CPM_SENDER_AGENT,
    CPM_RECEIVER_AGENT,
    CPM_IDENTIFIER_ENTITY
}
