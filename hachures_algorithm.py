# -*- coding: utf-8 -*-
"""Processing algorithm for generating hachure maps from DEM data.

This algorithm implements the methodology described in Robin Hawkes' tutorial:
https://robinhawkes.com/blog/qgis-monochrome-hachures/

The approach:
1. Generate contours from the DEM
2. Calculate slope and aspect rasters
3. Place points along contour lines
4. Sample slope and aspect values at each point
5. Apply geometry generator styling to create hachure lines
"""

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorDestination,
    QgsProcessing,
    QgsProject
)
from qgis import processing

class HachureAlgorithm(QgsProcessingAlgorithm):
    """Processing algorithm that generates hachure points with aspect/slope data."""
    # Parameter name constants
    DEM = 'DEM'
    CONTOUR_INTERVAL = 'CONTOUR_INTERVAL'
    POINT_DISTANCE = 'POINT_DISTANCE'
    OUTPUT = 'OUTPUT'

    def __init__(self, iface=None):
        """Initialize the algorithm.
        
        Args:
            iface: QGIS interface instance (optional).
        """
        super().__init__()
        self.iface = iface

    def name(self):
        """Return the algorithm name (internal identifier).
        
        Returns:
            str: The unique algorithm identifier.
        """
        return 'monochrome_hachures_full'

    def displayName(self):
        """Return the human-readable algorithm name.
        
        Returns:
            str: The algorithm name shown in the Processing Toolbox.
        """
        return 'Generate Hachure Points with Aspect/Slope'

    def group(self):
        """Return the algorithm group name.
        
        Returns:
            str: The group name for organizing algorithms in the toolbox.
        """
        return 'Terrain'

    def groupId(self):
        """Return the algorithm group ID.
        
        Returns:
            str: The group identifier.
        """
        return 'terrain'

    def initAlgorithm(self, config=None):
        """Define the algorithm parameters.
        
        Sets up input parameters for the algorithm including DEM input,
        contour interval, point spacing, and output destination.
        
        Args:
            config: Algorithm configuration (optional).
        """
        # Input DEM raster layer
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.DEM, 
            'Input DEM (elevation raster)'
        ))
        
        # Contour interval in meters - spacing between elevation contours
        self.addParameter(QgsProcessingParameterNumber(
            self.CONTOUR_INTERVAL, 
            'Contour interval (meters)', 
            defaultValue=50,
            minValue=1
        ))
        
        # Distance between hachure points along contours
        self.addParameter(QgsProcessingParameterNumber(
            self.POINT_DISTANCE, 
            'Distance between hachure points (meters)', 
            defaultValue=50,
            minValue=1
        ))
        
        # Output vector layer destination
        self.addParameter(QgsProcessingParameterVectorDestination(
            self.OUTPUT, 
            'Output points with aspect/slope data'
        ))

    def processAlgorithm(self, parameters, context, feedback):
        """Execute the hachure generation algorithm.
        
        This algorithm follows the Robin Hawkes tutorial approach:
        1. Generate contours from DEM
        2. Generate aspect and slope rasters
        3. Place points along contours
        4. Sample aspect and slope at each point
        5. Apply geometry generator styling for visualization
        
        Args:
            parameters: Dictionary of algorithm parameters.
            context: Processing context.
            feedback: Feedback object for progress reporting.
            
        Returns:
            dict: Dictionary with OUTPUT key containing the result layer path.
        """
        # Extract parameters
        dem = self.parameterAsRasterLayer(parameters, self.DEM, context)
        contour_interval = self.parameterAsDouble(parameters, self.CONTOUR_INTERVAL, context)
        point_distance = self.parameterAsDouble(parameters, self.POINT_DISTANCE, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        # Step 1: Generate contours from DEM
        # Contours are the foundation for hachure placement - hachures will be
        # perpendicular to these elevation lines
        feedback.pushInfo(f'Step 1/7: Generating contours with {contour_interval}m interval...')
        contours = processing.run('gdal:contour', {
            'INPUT': dem,
            'BAND': 1,  # Use first band of DEM
            'INTERVAL': contour_interval,  # Vertical spacing between contours
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }, context=context, feedback=feedback)['OUTPUT']

        # Step 2: Generate aspect raster
        # Aspect = direction of slope (0-360 degrees from north)
        # Used to control hachure opacity based on sun direction (hillshading effect)
        feedback.pushInfo('Step 2/7: Generating aspect raster...')
        aspect = processing.run('qgis:aspect', {
            'INPUT': dem,
            'Z_FACTOR': 1,  # Vertical exaggeration factor
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }, context=context, feedback=feedback)['OUTPUT']

        # Step 3: Generate slope raster
        # Slope = steepness of terrain (0-90 degrees)
        # Used to control hachure line length (steeper = longer lines)
        feedback.pushInfo('Step 3/7: Generating slope raster...')
        slope = processing.run('qgis:slope', {
            'INPUT': dem,
            'Z_FACTOR': 1,  # Vertical exaggeration factor
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }, context=context, feedback=feedback)['OUTPUT']

        # Step 4: Place points along contours
        # Each point will become the origin of a hachure line
        # The 'angle' field stores the contour direction at each point
        feedback.pushInfo(f'Step 4/7: Placing points every {point_distance}m along contours...')
        points = processing.run('native:pointsalonglines', {
            'INPUT': contours,
            'DISTANCE': point_distance,  # Spacing between points = hachure density
            'START_OFFSET': 0,  # No offset at start of line
            'END_OFFSET': 0,  # No offset at end of line
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }, context=context, feedback=feedback)['OUTPUT']

        # Step 5: Sample aspect values at points
        # Extracts aspect value from raster at each point location
        # Creates 'aspect_1' field with values 0-360 (degrees from north)
        feedback.pushInfo('Step 5/7: Sampling aspect values...')
        points_with_aspect = processing.run('native:rastersampling', {
            'INPUT': points,
            'RASTERCOPY': aspect,  # Aspect raster to sample from
            'COLUMN_PREFIX': 'aspect_',  # Creates field 'aspect_1'
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }, context=context, feedback=feedback)['OUTPUT']

        # Step 6: Sample slope values at points
        # Extracts slope value from raster at each point location
        # Creates 'slope_1' field with values 0-90 (degrees of steepness)
        feedback.pushInfo('Step 6/7: Sampling slope values...')
        points_with_slope = processing.run('native:rastersampling', {
            'INPUT': points_with_aspect,
            'RASTERCOPY': slope,  # Slope raster to sample from
            'COLUMN_PREFIX': 'slope_',  # Creates field 'slope_1'
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }, context=context, feedback=feedback)['OUTPUT']
        
        # Step 7: Clean up fields and export
        # Keep only essential fields to avoid FID conflicts and reduce file size
        # Fields retained:
        #   - ID: Contour identifier
        #   - ELEV: Elevation value
        #   - distance: Distance along contour line
        #   - angle: Direction of contour (for perpendicular hachures)
        #   - aspect_1: Slope direction (for hillshading)
        #   - slope_1: Slope steepness (for line length)
        feedback.pushInfo('Step 7/7: Finalizing and exporting...')
        final_points = processing.run('native:retainfields', {
            'INPUT': points_with_slope,
            'FIELDS': ['ID', 'ELEV', 'distance', 'angle', 'aspect_1', 'slope_1'],
            'OUTPUT': output
        }, context=context, feedback=feedback)['OUTPUT']

        # Post-processing: Apply style and add to map
        # Load the output as a vector layer and apply the QML style automatically
        from qgis.core import QgsVectorLayer
        import os
        
        # Load the output file as a layer
        layer = QgsVectorLayer(final_points, 'Hachures', 'ogr')
        if layer.isValid():
            # Apply the pre-configured QML style
            # This style uses a geometry generator to create lines from points
            style_path = os.path.join(os.path.dirname(__file__), 'hachure_style.qml')
            if os.path.exists(style_path):
                result = layer.loadNamedStyle(style_path)
                if result[1]:  # result is (success, error_message)
                    feedback.pushInfo(f'Successfully applied hachure style')
                else:
                    feedback.pushInfo(f'Style applied with message: {result[0]}')
            else:
                feedback.pushInfo(f'Style file not found at: {style_path}')
            
            # Add styled layer to the current QGIS project
            QgsProject.instance().addMapLayer(layer)
            
            # Force the layer to redraw with the new style
            layer.triggerRepaint()
            
            feedback.pushInfo('')
            feedback.pushInfo('='*60)
            feedback.pushInfo('SUCCESS! Hachure layer created and styled.')
            feedback.pushInfo('='*60)
            feedback.pushInfo('')
            feedback.pushInfo('The layer uses a Geometry Generator to create lines from points.')
            feedback.pushInfo('Opacity is controlled by aspect (sun direction from north).')
            feedback.pushInfo('')
            feedback.pushInfo('To customize:')
            feedback.pushInfo('- Adjust line length: change "90 + 200 * slope_1 / 90"')
            feedback.pushInfo('- Adjust randomness: change "rand(0, 8)"')
            feedback.pushInfo('- Adjust sun direction: modify "aspect_1 - 180"')
            feedback.pushInfo('')

        return {self.OUTPUT: final_points}

    def createInstance(self):
        """Create a new instance of the algorithm.
        
        Required by the Processing framework for creating algorithm instances.
        
        Returns:
            HachureAlgorithm: A new instance of this algorithm.
        """
        return HachureAlgorithm()
