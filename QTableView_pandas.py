#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import csv, codecs 
import os
import pandas as pd
from PyQt5.QtCore import Qt, QDir, QItemSelectionModel, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtWidgets import (QMainWindow, QTableView, QApplication, 
                                                            QAction, QMenu, QFileDialog, QAbstractItemView, QMessageBox)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCursor, QIcon, QKeySequence

class PandasModel(QAbstractTableModel):
    def __init__(self, df = pd.DataFrame(), parent=None): 
        QAbstractTableModel.__init__(self, parent=None)
        self._df = df
        self.setChanged = False
        self.dataChanged.connect(self.setModified)

    def setModified(self):
        self.setChanged = True
        print(self.setChanged)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError, ):
                return QVariant()
        elif orientation == Qt.Vertical:
            try:
                return self._df.index.tolist()[section]
            except (IndexError, ):
                return QVariant()

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if (role == Qt.EditRole):
                return self._df.values[index.row()][index.column()]
            elif (role == Qt.DisplayRole):
                return self._df.values[index.row()][index.column()]
        return None

    def setData(self, index, value, role):
        row = self._df.index[index.row()]
        col = self._df.columns[index.column()]
        self._df.values[row][col] = value
        self.dataChanged.emit(index, index)
        return True

    def rowCount(self, parent=QModelIndex()): 
        return len(self._df.index)

    def columnCount(self, parent=QModelIndex()): 
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending= order == Qt.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

class Viewer(QMainWindow):
    def __init__(self, parent=None):
      super(Viewer, self).__init__(parent)
      self.filename = ""
      self.setGeometry(0, 0, 800, 600)
      self.lb = QTableView()
      self.model =  PandasModel()
      self.lb.setModel(self.model)
      self.lb.setEditTriggers(QAbstractItemView.DoubleClicked)
      self.lb.setSelectionBehavior(self.lb.SelectRows)
      self.lb.setSelectionMode(self.lb.SingleSelection)
      self.setStyleSheet(stylesheet(self))
      self.lb.setAcceptDrops(True)
      self.setCentralWidget(self.lb)
      self.setContentsMargins(10, 10, 10, 10)
      self.statusBar().showMessage("Ready", 0)

      self.createMenuBar()
      self.lb.setFocus()

    def closeEvent(self, event):
        print(self.model.setChanged)
        if  self.model.setChanged == True:
            print("is changed, saving?")
            quit_msg = "<b>The document was changed.<br>Do you want to save the changes?</ b>"
            reply = QMessageBox.question(self, 'Save Confirmation', 
                     quit_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.writeCSV_update()
            else:
                print("not saved, goodbye ...")
                return
        else:
            print("nothing changed. goodbye")

    def createMenuBar(self):
        bar=self.menuBar()
        self.filemenu=bar.addMenu("File")
        self.separatorAct = self.filemenu.addSeparator()
        self.filemenu.addAction(QIcon.fromTheme("document-open"), "Open",  self.loadCSV, QKeySequence.Open) 
        self.filemenu.addAction(QIcon.fromTheme("document-save"), "Save",  self.writeCSV_update, QKeySequence.Save) 
        self.filemenu.addAction(QIcon.fromTheme("document-save-as"), "Save as ...",  self.writeCSV, QKeySequence.SaveAs) 

    def openFile(self, path=None):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath() + "/Dokumente/CSV/","CSV Files (*.csv)")
        if path:
            return path

    def loadCSV(self):
        fileName = self.openFile()
        if fileName:
            print(fileName + " loaded")
            f = open(fileName, 'r+b')
            with f:
                self.filename = fileName
                df = pd.read_csv(f, delimiter = '\t', keep_default_na = False, low_memory=False, header=None)
                self.model = PandasModel(df)
                self.lb.setModel(self.model)
                self.lb.resizeColumnsToContents()
                self.lb.selectRow(0)
        self.statusBar().showMessage("%s %s" % (fileName, "loaded"), 0)

    def writeCSV(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Open File", self.filename,"CSV Files (*.csv)")
        if fileName:
            print(fileName + " saved")
            f = open(fileName, 'w')
            newModel = self.model
            dataFrame = newModel._df.copy()
            dataFrame.to_csv(f, sep='\t', index = False, header = False)

    def writeCSV_update(self):
        if self.filename:
            print(self.filename + " saved")
            f = open(self.filename, 'w')
            newModel = self.model
            dataFrame = newModel._df.copy()
            dataFrame.to_csv(f, sep='\t', index = False, header = False)
            self.model.setChanged = False

def stylesheet(self):
        return """
        QMenuBar
        {
            background: transparent;
            border: 0px;
        }
        QTableView
        {
            border: 1px solid #d3d7cf;
            border-radius: 0px;
            font-size: 8pt;
            background: #eeeeec;
            selection-color: #ffffff
        }
        QTableView::item:hover
        {   
            color: #d3d7cf;
            background: #1f3c5d;;           
        }
        
        QTableView::item:selected {
            color: #F4F4F4;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 #2a82da, stop:1 #1f3c5d);
        } 

        QTableView QTableCornerButton::section {
            background: #D6D1D1;
            border: 0px outset black;
        }
    """
 
if __name__ == "__main__":
 
    app = QApplication(sys.argv)
    main = Viewer()
    main.show()
sys.exit(app.exec_())
