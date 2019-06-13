#! usr/local/bin/python3
# -*- coding: utf-8 -*-

# README: поменяйте путь к Python, если на вашем компьютере он установлен в другую дирректорию

# main.py

import UI
import PythonHighlighter

import sys
from PyQt5.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)

    mainWindow = UI.MainWindow()
    highlight = PythonHighlighter.PythonHighlighter(mainWindow.centralWidget().document())

    mainWindow.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
