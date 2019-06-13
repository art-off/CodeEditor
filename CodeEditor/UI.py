# UI.py

from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMessageBox, QWidget, QPlainTextEdit, QTextEdit
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QPainter, QTextFormat


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        # создаем экземпляр класса LineNumberArea
        self.lineNumberArea = LineNumberArea(self)
        # изменение, дополнение ширины виджета с номерами строк
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        # новая строка с нумерацией будет "рисоваться" каждый раз, когда будет меняться форм. блок
        self.updateRequest.connect(self.updateLineNumberArea)
        # выделение (подсвечивание) редкатируемой строки меняется когда менятся позиция курсора
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().width(' ') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            lineColor = QColor()
            lineColor.setNamedColor('#102020')
            lineColor.lighter(500)
            selection.format.setBackground(lineColor)

            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)

        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(), height, Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1


class MainWindow (QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # ПОЛЕ РЕДАКТОРА -------------------------------------------#

        # создаем поле для редактирования кода, наздачаем ему нужные стили и устанавливаем ширину табов
        self.editor = CodeEditor()
        self.editor.setStyleSheet("""QPlainTextEdit {
                                        background-color: #222;
                                        color: #A6B4C3;
                                        font-family: Courier;
                                    }"""
                             )
        self.editor.setTabStopDistance(4 * 8)   # 4 - кол-во, 8 - ширина одного таба

        # устанавилваем поле для редактирования кода центральным виджетом окна и меняем размер окна
        self.setCentralWidget(self.editor)
        self.resize(900, 500)

        # МЕНЮ БАР --------------------------------------------------#

        # создаем менюбар
        menubar = self.menuBar()

        #
        # добавляем нужные действия и нужные атрибуты к ним для меню "File"
        newFile = QAction('&New File', self)
        newFile.setShortcut('Ctrl+N')
        newFile.triggered.connect(self.newFile)

        openFile = QAction('&Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.triggered.connect(self.showDialogOpenFile)

        saveFile = QAction('&Save', self)
        saveFile.setShortcut('Ctrl+S')
        saveFile.triggered.connect(self.showDialogSaveFile)

        # создаем меню "File" в менюбар и добавляем туда все нужные действия
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(newFile)
        fileMenu.addAction(openFile)
        fileMenu.addAction(saveFile)

        #
        # добавляем нужные действия и нужные атрибуты к ним для меню "Edit"
        undoAction = QAction("&Undo last action", self)
        undoAction.setShortcut("Ctrl+Z")
        undoAction.triggered.connect(self.Undo)

        # создаем меню "Edit" в менюбар и добавляем туда все нужные действия
        editMenu = menubar.addMenu('&Edit')
        editMenu.addAction(undoAction)

        # СТАТУС БАР ------------------------------------------------#

        # создаем статусбар и назначаем ему вывод информации при изменении положения курсора
        self.status = self.statusBar()
        self.editor.cursorPositionChanged.connect(self.showCursorPosition)

    # ДИАЛОГИ ---------------------------------------------------------------------------------------------------------#
    # открытие файла
    def showDialogOpenFile(self):
        fileName, ok = QFileDialog.getOpenFileName(self, 'Open file', filter='*.py')

        if ok:
            f = open(fileName, 'r')
            with f:
                data = f.read()
                self.editor.setPlainText(data)

    # сохранение файла
    def showDialogSaveFile(self):
        fileName, ok = QFileDialog.getSaveFileName(self, 'Save file', filter='*.py')

        if ok:
            f = open(fileName, 'w')
            with f:
                data = self.editor.toPlainText()
                f.write(data)

    # создание нового файла
    def newFile(self):
        reply = QMessageBox.question(self, 'New File', "Are you want save this file?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.showDialogSaveFile()
        self.editor.clear()

    # ВНУТРЕННИЕ ФУНКЦИИ ----------------------------------------------------------------------------------------------#
    # отображение в статусбаре текущее положение курсора (строка и линия)
    def showCursorPosition(self):
        line = self.editor.textCursor().blockNumber()
        col = self.editor.textCursor().columnNumber()
        linecol = 'Line ' + str(line+1) + ' | ' + 'Column ' + str(col+1)
        self.status.showMessage(linecol)

    # отмена последнего действия
    def Undo(self):
        self.editor.undo()
