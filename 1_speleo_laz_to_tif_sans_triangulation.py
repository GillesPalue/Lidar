"""
***************************************************************************
*                    LIDAR BATCH PROCESSING FOR QGIS
*   By Zoran Zoran Čučković @ LandscapeArchaeology.org
GNU licence:
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
*   Modifs Gilles pour la spéléo : 02/05/2024                             *
*   Se contente de transformer les laz en raster en utilisant :           *
*   - uniquement la couche "sol" (classification == 2)                    *
*   - la triangulation (meilleur résultats)                               *
*   - Attribut Z = 0,25m (meilleurs compromis entre résolution et poids)  *
***************************************************************************
"""

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
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_FOLDER = 'INPUT'
    RESOLUTION = 'RESOLUTION'
    CLASSIFICATION = 'CLASSIFICATION'
    OUTPUT_FOLDER = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExampleProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'speleo_laz_to_tif_sans_triangulation'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('1. Nuages de points (.laz) -> rasters (.tif) sans triangulation')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Speleo')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Speleo'

    
    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(QgsProcessingParameterFile(
            self.INPUT_FOLDER,
            self.tr("\nRASTÉRISATION SANS TRIANGULATION, avec remplissage des vides (méthode Philippe Mathios)\n\nAttention, Bien attendre le mot 'Complete' dans la barre de progression avant de fermer (pas juste 100 %). Compter 15 minutes / km2\n\n\n DOSSIER CONTENANT LES NUAGES DE POINTS TÉLÉCHARGÉS DEPUIS L'IGN"),
            behavior=QgsProcessingParameterFile.Folder))
            
        self.addParameter(
            QgsProcessingParameterNumber(
                self.RESOLUTION,
                self.tr('\n\nRÉSOLUTION SUR ALTITUDE Z (en m) : \n\npar km2 :        Z = 1 m       Z = 0,1 m    Z = 0,05 m\nbrutes :               8 Mo           900 Mo              3 Go\ncompressées :  1,5 Mo          130 Mo          500 Mo'),
                QgsProcessingParameterNumber.Double,
                0.25))
        
        self.addParameter(
            QgsProcessingParameterString(
                self.CLASSIFICATION,
                self.tr('\nClasses séparées par des virgules (non attribué = 1, sol = 2, point bas = 7)'),
                '1,2,7'))
  
        self.addParameter(QgsProcessingParameterFile(
            self.OUTPUT_FOLDER,
            self.tr("\nDOSSIER QUI VA CONTENIR LES RASTERS"),
            behavior=QgsProcessingParameterFile.Folder))
            
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        



        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsFile(parameters, self.INPUT_FOLDER, context)
        resolution = self.parameterAsDouble(parameters, self.RESOLUTION, context)              
        destination =  self.parameterAsFile(parameters, self.OUTPUT_FOLDER, context)
        classification = 'Classification in ( {} )'.format(
            self.parameterAsString(parameters, self.CLASSIFICATION, context))
    
        if source == destination : 
            err= (" \n ****** \n ERREUR ! \n Le dossier de destination est le même que celui d'import !")
            feedback.reportError(err, fatalError = True)
            raise QgsProcessingException(err)
            
            
        input_files = os.listdir(source)
        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / len(input_files)
        count = 1
        feedback.setProgress(0)
             
     
        for f in input_files:
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            full_path = os.path.join(source, f)
            output_file = os.path.join(destination, os.path.basename(f) + ".tif")
            output_file_fill_nodata = os.path.join(destination, os.path.basename(f) + ".fill_nodata.tif")
            output_file_compressed = os.path.join(destination, os.path.basename(f) + ".compressed.tif")

            

            # Gilles : conversion du nuage de points .laz en raster .tif
            if f[-4:] in (".las" ,".laz"): 
                                            
                # Gilles : voir https://docs.qgis.org/3.34/en/docs/user_manual/processing_algs/qgis/pointcloudconversion.html#export-raster-using-triangulation
                # pour la commande
                feedback.pushInfo("\n" + f + " :\nConversion raster en cours...")
                try:
                    processing.run("pdal:exportraster", {
                        'INPUT': full_path,
                        'ATTRIBUTE' : 'Z',
                        'FILTER_EXPRESSION' : classification, 
                        'RESOLUTION' : resolution,
                        'OUTPUT': output_file
                    })
                except :
                    feedback.pushInfo("ECHEC !!!!!!!!!!\n\n\n")
                else :
                    feedback.pushInfo(" OK\n")
                
                    # Gilles : étape 2 : remplissage des vides
                    feedback.pushInfo("Remplissage des vides...")
                    if os.path.isfile(output_file):
                        try :
                            processing.run("gdal:fillnodata", {
                                'INPUT': output_file,
                                'BAND' : '1',
                                'DISTANCE' : '60',
                                'OUTPUT': output_file_fill_nodata
                            })
                        except :
                            feedback.pushInfo("ECHEC !!!!!!!!!!\n\n\n")
                        else :
                            feedback.pushInfo(" OK\n")
                    else :
                        feedback.pushInfo("\nERREUR : " + output_file + " : introuvable\n")
                                    
                    
                    # Gilles : étape 3 : compression du fichier raster .tif
                    feedback.pushInfo("Compression en cours...")
                    if os.path.isfile(output_file_fill_nodata):
                        processing.run("gdal:translate", {
                            'INPUT': output_file_fill_nodata,
                            'OPTIONS' : 'COMPRESS=LERC_DEFLATE|MAX_Z_ERROR=' + str(resolution/10) + '|PREDICTOR=3|NUM_THREADS=ALL_CPUS|GDAL_DISABLE_READDIR_ON_OPEN=TRUE',
                            'OUTPUT': output_file_compressed
                        })
                        feedback.pushInfo(" OK\n")
                    else :
                        feedback.pushInfo("\nERREUR : " + output_file_fill_nodata + " : introuvable\n")
                    
                    # Gilles : étape 4 : suppression des fichiers bruts
                    feedback.pushInfo("Suppression des fichiers temporaires...")
                    try :
                        if os.path.isfile(output_file):
                            os.remove(output_file)
                            
                            if os.path.isfile(output_file + ".aux.xml"):
                                os.remove(output_file + ".aux.xml")
                                
                                if os.path.isfile(output_file_fill_nodata):
                                    os.remove(output_file_fill_nodata)
                            
                                    if os.path.isfile(output_file_fill_nodata + ".aux.xml"):
                                        os.remove(output_file_fill_nodata + ".aux.xml")
                                    else :
                                        feedback.pushInfo("\nERREUR : " + output_file_fill_nodata + ".aux.xml" + " : introuvable")                                
                                else :
                                    feedback.pushInfo("\nERREUR : " + output_file_fill_nodata + " introuvable")          
                            else :
                                feedback.pushInfo("\nERREUR : " + output_file + ".aux.xml" + " : introuvable")                        
                        else :
                            feedback.pushInfo("\nERREUR : " + output_file + " introuvable")                  
                    except :
                        feedback.pushInfo("ECHEC !!!!!!!!!!\n\n\n")
                    else :
                        feedback.pushInfo(" OK\n")
                
                        
                            
                    feedback.pushInfo("\n")
                
            else : feedback.pushInfo("\n" + f + " : Fichier ignoré.\n")
            
            
            
            # Update the progress bar
            feedback.setProgress(int(count * total))
            count +=1
            
            

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT_FOLDER: None}


