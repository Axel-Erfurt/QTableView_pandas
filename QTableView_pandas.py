#!/usr/bin/python3
# -*- coding: utf-8 -*-
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import csv, codecs 
import os
import pandas as pd
from PyQt5.QtCore import Qt, QDir, QItemSelectionModel, QAbstractTableModel, QModelIndex, QVariant, QSize, QSettings
from PyQt5.QtWidgets import (QMainWindow, QTableView, QApplication, QToolBar, QLineEdit, QComboBox, QDialog, 
                                                            QAction, QMenu, QFileDialog, QAbstractItemView, QMessageBox, QWidget)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCursor, QIcon, QKeySequence, QTextDocument, QTextCursor, QTextTableFormat
from PyQt5 import QtPrintSupport

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
      self.MaxRecentFiles = 5
      self.windowList = []
      self.recentFiles = []
      self.settings = QSettings('Axel Schneider', 'QTableViewPandas')
      self.filename = ""
      self.setGeometry(0, 0, 800, 600)
      self.lb = QTableView()
      self.lb.verticalHeader().setVisible(True)
      self.lb.setGridStyle(1)
      self.model =  PandasModel()
      self.lb.setModel(self.model)
      self.lb.setEditTriggers(QAbstractItemView.DoubleClicked)
      self.lb.setSelectionBehavior(self.lb.SelectRows)
      self.lb.setSelectionMode(self.lb.SingleSelection)
      self.setStyleSheet(stylesheet(self))
      self.lb.setAcceptDrops(True)
      self.setCentralWidget(self.lb)
      self.setContentsMargins(10, 10, 10, 10)
      self.createToolBar()
      self.readSettings()
      self.lb.setFocus()
      self.statusBar().showMessage("Ready", 0)

    def readSettings(self):
        print("reading settings")
        if self.settings.contains("geometry"):
            self.setGeometry(self.settings.value('geometry'))
        if self.settings.contains("recentFiles"):
            self.recentFiles = self.settings.value('recentFiles')
            self.lastFiles.addItem("last Files")
            self.lastFiles.addItems(self.recentFiles[:15])

    def saveSettings(self):
        print("saving settings")
        self.settings.setValue('geometry', self.geometry())
        self.settings.setValue('recentFiles', self.recentFiles)

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
        self.saveSettings()

    def createToolBar(self):
        openAction = QAction(QIcon.fromTheme("document-open"), "Open",  self, triggered=self.loadCSV, shortcut = QKeySequence.Open)
        saveAction = QAction(QIcon.fromTheme("document-save"), "Save", self, triggered= self.writeCSV_update, shortcut = QKeySequence.Save) 
        saveAsAction = QAction(QIcon.fromTheme("document-save-as"), "Save as ...", self,  triggered=self.writeCSV, shortcut = QKeySequence.SaveAs) 
        self.tbar = self.addToolBar("File")
        self.tbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.tbar.setIconSize(QSize(16, 16))
        self.tbar.setMovable(False)
        self.tbar.addAction(openAction) 
        self.tbar.addAction(saveAction) 
        self.tbar.addAction(saveAsAction) 

        empty = QWidget()
        empty.setFixedWidth(10)
        self.tbar.addWidget(empty)

        self.lastFiles = QComboBox()
        self.lastFiles.setFixedWidth(300) 
        self.lastFiles.currentIndexChanged.connect(self.loadRecent)
        self.tbar.addWidget(self.lastFiles)  

        empty = QWidget()
        empty.setFixedWidth(10)
        self.tbar.addWidget(empty)

        findbyText = QAction(QIcon.fromTheme("edit-find-symbolic"), "find", self, triggered = self.findInTable)
        self.lineFind = QLineEdit()
        self.lineFind.addAction(findbyText, 0)
        self.lineFind.setPlaceholderText("find")
        self.lineFind.setClearButtonEnabled(True)
        self.lineFind.setFixedWidth(250)
        self.lineFind.returnPressed.connect(self.findInTable)
        self.tbar.addWidget(self.lineFind)
        self.tbar.addAction(findbyText)   

        empty = QWidget()
        empty.setFixedWidth(10)
        self.tbar.addWidget(empty)

        self.previewAction = QAction(QIcon.fromTheme("document-print-preview"), "print", self, triggered = self.handlePreview)
        self.tbar.addAction(self.previewAction)
        self.printAction = QAction(QIcon.fromTheme("document-print"), "print", self, triggered = self.handlePrint)
        self.tbar.addAction(self.printAction)

    def loadRecent(self):
        if self.lastFiles.currentIndex() > 0:
            print(self.lastFiles.currentText())
            print(self.model.setChanged)
            if  self.model.setChanged == True:
                print("is changed, saving?")
                quit_msg = "<b>The document was changed.<br>Do you want to save the changes?</ b>"
                reply = QMessageBox.question(self, 'Save Confirmation', 
                         quit_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.openCSV(self.lastFiles.currentText())
                else:
                    self.openCSV(self.lastFiles.currentText())
            else:
                self.openCSV(self.lastFiles.currentText())

    def openCSV(self, path):
        f = open(path, 'r+b')
        with f:
            df = pd.read_csv(f, delimiter = '\t', keep_default_na = False, low_memory=False, header=None)
            f.close()
            self.model = PandasModel(df)
            self.lb.setModel(main.model)
            self.lb.resizeColumnsToContents()
            self.lb.selectRow(0)
            self.statusBar().showMessage("%s %s" % (path, "loaded"), 0)

    def findInTable(self):
        self.lb.clearSelection()
        text = self.lineFind.text()
        model = self.lb.model()
        for column in range(self.model.columnCount()):
            start = model.index(0, column)
            matches = model.match(start, Qt.DisplayRole, text, -1, Qt.MatchContains)
            if matches:
                for index in matches:
                    print(index.row(), index.column())
                    self.lb.selectionModel().select(index, QItemSelectionModel.Select)

    def openFile(self, path=None):
        print(self.model.setChanged)
        if  self.model.setChanged == True:
            print("is changed, saving?")
            quit_msg = "<b>The document was changed.<br>Do you want to save the changes?</ b>"
            reply = QMessageBox.question(self, 'Save Confirmation', 
                     quit_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.writeCSV_update()
            else:
                print("not saved, loading ...")
                return
        path, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath() + "/Dokumente/CSV/","CSV Files (*.csv)")
        if path:
            return path

    def loadCSV(self):
        fileName = self.openFile()
        if fileName:
            print(fileName + " loaded")
            f = open(fileName, 'r+b')
            with f:
                df = pd.read_csv(f, delimiter = '\t', keep_default_na = False, low_memory=False, header=None)
                f.close()
                self.model = PandasModel(df)
                self.lb.setModel(self.model)
                self.lb.resizeColumnsToContents()
                self.lb.selectRow(0)
        self.statusBar().showMessage("%s %s" % (fileName, "loaded"), 0)
        self.recentFiles.insert(0, fileName)
        self.lastFiles.insertItem(1, fileName)

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
            f = open(self.filename, 'w')
            newModel = self.model
            dataFrame = newModel._df.copy()
            dataFrame.to_csv(f, sep='\t', index = False, header = False)
            self.model.setChanged = False
            print("%s %s" % (self.filename, "saved"))
            self.statusBar().showMessage("%s %s" % (self.filename, "saved"), 0)

    def handlePrint(self):
        if self.model.rowCount() == 0:
            self.msg("no rows")
        else:
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec_() == QDialog.Accepted:
                self.handlePaintRequest(dialog.printer())
                print("Document printed")

    def handlePreview(self):
        if self.model.rowCount() == 0:
            self.msg("no rows")
        else:
            dialog = QtPrintSupport.QPrintPreviewDialog()
            dialog.setFixedSize(1000,700)
            dialog.paintRequested.connect(self.handlePaintRequest)
            dialog.exec_()
            print("Print Preview closed")

    def handlePaintRequest(self, printer):
        printer.setDocName(self.filename)
        document = QTextDocument()
        cursor = QTextCursor(document)
        model = self.lb.model()
        tableFormat = QTextTableFormat()
        tableFormat.setBorder(0.2)
        tableFormat.setBorderStyle(3)
        tableFormat.setCellSpacing(0);
        tableFormat.setTopMargin(0);
        tableFormat.setCellPadding(4)
        table = cursor.insertTable(model.rowCount() + 1, model.columnCount(), tableFormat)
        model = self.lb.model()
        ### get headers
        myheaders = []
        for i in range(0, model.columnCount()):
            myheader = model.headerData(i, Qt.Horizontal)
            cursor.insertText(str(myheader))
            cursor.movePosition(QTextCursor.NextCell)
        ### get cells
        for row in range(0, model.rowCount()):
           for col in range(0, model.columnCount()):
               index = model.index( row, col )
               cursor.insertText(str(index.data()))
               cursor.movePosition(QTextCursor.NextCell)
        document.print_(printer)

def stylesheet(self):
        return """
    QMainWindow
        {
         background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                 stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                 stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
        }
        QMenuBar
        {
            background: transparent;
            border: 0px;
        }
        QTableView
        {
            background: qlineargradient(y1:0,  y2:1,
                        stop:0 #d3d7cf, stop:1 #ffffff);
            border: 1px solid #d3d7cf;
            border-radius: 0px;
            font-size: 8pt;
            selection-color: #ffffff
        }
        QTableView::item:hover
        {   
            color: #eeeeec;
            background: #c4a000;;           
        }
        
        
        QTableView::item:selected {
            color: #F4F4F4;
            background: qlineargradient(y1:0,  y2:1,
                        stop:0 #2a82da, stop:1 #1f3c5d);
        } 

        QTableView QTableCornerButton::section {
            background: transparent;
            border: 0px outset black;
        }
    QHeaderView
        {
         background: qlineargradient( y1: 0, y2: 1,
                                 stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                 stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
        color: #888a85;
        }

    QToolBar
        {
        background: transparent;
        border: 0px;
        }
    QStatusBar
        {
        background: transparent;
        border: 0px;
        color: #555753;
        font-size: 7pt;
        }

    """
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = Viewer()
    main.show()
    if len(sys.argv) > 1:
        main.openCSV(sys.argv[1])
sys.exit(app.exec_())
