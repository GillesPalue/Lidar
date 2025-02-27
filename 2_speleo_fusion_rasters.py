from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterString, 
                       QgsProcessingParameterNumber)
from qgis import processing
import os



class ExampleProcessingAlgorithm(QgsProcessingAlgorithm):

    INPUT_FOLDER = 'INPUT'
    OUTPUT_FOLDER = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExampleProcessingAlgorithm()

    def name(self):
        return 'speleo_fusions_rasters'

    def displayName(self):
        return self.tr('2. Fusion rasters en un seul')

    def group(self):
        return self.tr('Speleo')

    def groupId(self):
        return 'Speleo'

   
    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterFile(
            self.INPUT_FOLDER,
            self.tr("DOSSIER CONTENANT LES RASTERS A FUSIONNER"),
            behavior=QgsProcessingParameterFile.Folder))
        
        self.addParameter(QgsProcessingParameterFile(
            self.OUTPUT_FOLDER,
            self.tr("\nDOSSIER QUI VA RECEVOIR LE GROS RASTER FUSIONNÉ\n(poids estimé : environ la moitié du poids total des rasters à fusionner)"),
            behavior=QgsProcessingParameterFile.Folder))
            
        
    def processAlgorithm(self, parameters, context, feedback):

        source = self.parameterAsFile(parameters, self.INPUT_FOLDER, context)
        destination =  self.parameterAsFile(parameters, self.OUTPUT_FOLDER, context)
  
        if source == destination : 
            err= (" \n ****** \n ERREUR ! \n Le dossier de destination est le même que celui d'import !")
            feedback.reportError(err, fatalError = True)
            raise QgsProcessingException(err)
            
        input_files = os.listdir(source)
        output_file = os.path.join(destination, "gros_raster.fusionned.tif")
   
        # Gilles : préparation de la liste des rasters à fusionner
        liste_rasters = []
        for f in input_files:
            full_path = os.path.join(source, f)
            if f[-4:] in (".tif"): 
                liste_rasters.append(full_path)
        
        # Gilles : on lance la fusion des rasters
        processing.run("gdal:merge", {
            'INPUT':liste_rasters,
            'PCT':False,'SEPARATE':False,'NODATA_INPUT':None,'NODATA_OUTPUT':None,
            'OPTIONS':'COMPRESS=LERC|MAX_Z_ERROR=0.01|BIGTIFF=YES|TILED=YES|NUM_THREADS=ALL_CPUS',
            'EXTRA':'','DATA_TYPE':5,
            'OUTPUT': output_file})

        return {self.OUTPUT_FOLDER: None}






