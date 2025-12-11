"""
Traversal Information Algorithm

Algorithm for determining whether PROV elements belong to traversal information
or domain-specific provenance.
"""

from prov.constants import PROV_TYPE

from .constants import CPM_SUBTYPES, CPM_TI_ALLOWED_ATTRIBUTES


class TraversalInformationAlgorithm:
    """
    Algorithm for determining whether elements belong to traversal information
    or domain-specific provenance.
    """

    @staticmethod
    def belongs_to_traversal_information(element) -> bool:
        """
        Determine if a PROV element belongs to traversal information.

        Args:
            element: A PROV element to check

        Returns:
            True if element belongs to traversal information, False otherwise
        """
        # Check if element has CPM prov:type - if so, assume it's traversal information
        prov_types = element.get_attribute(PROV_TYPE)
        if prov_types:
            for prov_type in prov_types:
                if prov_type in CPM_SUBTYPES:
                    return True

        # For elements without CPM types, check if they have non-TI attributes
        if TraversalInformationAlgorithm._has_non_ti_attributes(element):
            return False

        # Default to False for non-CPM elements
        return False

    @staticmethod
    def _has_non_ti_attributes(element) -> bool:
        """
        Check if element has attributes not allowed in traversal information.

        Args:
            element: A PROV element to check

        Returns:
            True if element has non-TI attributes, False otherwise
        """
        for attr_name, _ in element.attributes:
            # Check if attribute belongs to CPM namespace or is dct:hasPart
            if attr_name not in CPM_TI_ALLOWED_ATTRIBUTES and not str(attr_name).startswith('cpm:'):
                return True
        return False
