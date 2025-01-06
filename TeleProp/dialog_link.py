# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic,QtGui
from qgis.PyQt.QtGui import QPen
from qgis.PyQt.QtCore import QVariant,Qt,QTranslator,QCoreApplication
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QAction,QMessageBox,QComboBox,QFileDialog,QInputDialog
from qgis.gui import QgsMapToolIdentifyFeature,QgsMapToolIdentify,QgsMapToolEmitPoint,QgsMapTool
from qgis.core import (
    Qgis,QgsApplication,
    QgsProject,QgsTask,QgsFeatureRequest,
    QgsVectorLayer,QgsRasterLayer,QgsMapLayer,
    QgsFeature,
    QgsGeometry,QgsReferencedGeometry,QgsCoordinateReferenceSystem,QgsCoordinateTransform,
    QgsVectorDataProvider,QgsField,
    QgsSymbol,QgsLineSymbol,QgsMarkerSymbol,QgsRendererRange,QgsGraduatedSymbolRenderer,
    QgsVectorLayerSimpleLabeling,QgsPalLayerSettings,QgsTextFormat,QgsTextBufferSettings,
    QgsPoint,QgsDistanceArea,QgsPointXY,QgsRegularPolygon,
    QgsMessageLog)
from qgis import processing
from .dataReaderTool import DataReaderTool
# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'dialog_link.ui'))

class Dialog_Link(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self,iface,layer,parent=None):
        """Constructor."""
        self.iface = iface
        self.parent=parent
        super(Dialog_Link,self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.canvas = self.iface.mapCanvas()
        self.LinkItem=None
        self.QComboBox_LinkItem.currentIndexChanged.connect(self.QComboBox_LinkItem_currentIndexChanged)
        self.QComboBox_LinkItem.clear()
        self.QComboBox_LinkItem.addItem("-")
        self.QComboBox_LinkItem.addItems(layer.fields().names())
    def QComboBox_LinkItem_currentIndexChanged(self):
        self.LinkItem=self.QComboBox_LinkItem.currentText()