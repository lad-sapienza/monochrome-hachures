"""Processing provider for hachure generation algorithms."""

from qgis.core import QgsProcessingProvider
from .hachures_algorithm import HachureAlgorithm

class Provider(QgsProcessingProvider):
    """QGIS Processing provider that supplies hachure generation algorithms.
    
    This provider registers algorithms in the Processing Toolbox under
    the 'Monochrome Hachures' group.
    """
    
    def __init__(self, iface=None):
        """Initialize the provider.
        
        Args:
            iface: QGIS interface instance (optional).
        """
        super().__init__()
        self.iface = iface

    def loadAlgorithms(self):
        """Load all algorithms provided by this provider.
        
        Registers the HachureAlgorithm with the Processing framework.
        """
        self.addAlgorithm(HachureAlgorithm(self.iface))

    def id(self):
        """Return the unique provider ID.
        
        Returns:
            str: The provider identifier used internally by QGIS.
        """
        return "monochrome_hachures_full"

    def name(self):
        """Return the human-readable provider name.
        
        Returns:
            str: The provider name shown in the Processing Toolbox.
        """
        return "Monochrome Hachures"
