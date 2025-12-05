"""QGIS Plugin for generating hachure maps from DEM data.

This plugin provides a Processing provider that generates hachure-style
terrain visualization following Robin Hawkes' methodology.
"""

from qgis.core import QgsApplication
from .hachures_provider import Provider


class HachuresPlugin:
    """Main plugin class that manages the Processing provider lifecycle."""
    
    def __init__(self, iface):
        """Initialize the plugin.
        
        Args:
            iface: QGIS interface instance.
        """
        self.iface = iface
        self.provider = None

    def initProcessing(self):
        """Initialize and register the processing provider.
        
        Creates the Provider instance and adds it to QGIS's
        processing registry so algorithms become available.
        """
        self.provider = Provider(self.iface)
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        """Initialize GUI elements when plugin is loaded.
        
        Called by QGIS when the plugin is enabled. Sets up the
        processing provider.
        """
        self.initProcessing()

    def unload(self):
        """Clean up when plugin is unloaded.
        
        Called by QGIS when the plugin is disabled or QGIS closes.
        Removes the processing provider from the registry.
        """
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
