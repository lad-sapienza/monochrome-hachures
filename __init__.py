"""QGIS Plugin initialization."""

def classFactory(iface):
    """Load HachuresPlugin class from file hachures_plugin.
    
    Args:
        iface: A QGIS interface instance.
        
    Returns:
        HachuresPlugin: An instance of the plugin.
    """
    from .hachures_plugin import HachuresPlugin
    return HachuresPlugin(iface)
