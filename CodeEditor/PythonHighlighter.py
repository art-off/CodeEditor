# PythonHighlighter.py

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter


def format(color, style=''):
    """Возвращает QTextCharFormat с данными атрибутами."""

    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Стили, приминимые к разнам группам слов
STYLES = {
    'keyword':   format('orange'),
    'operator':  format('darkgray'),
    'brace':     format('darkGray'),
    'def_class': format('gold'),
    'string':    format('green',   'italic'),
    'comment1':  format('dimgray', 'italic'),
    'comment2':  format('greenyellow'),
    'self':      format('violet',  'italic'),
    'numbers':   format('brown'),
}


class PythonHighlighter (QSyntaxHighlighter):
    """Подсветчик синтаксиса для Python."""

    # Ключевые слова Python
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False'
    ]

    # Операторы Python
    operators = [
        '=',
        # Сравнение
        '==', '!=', '<', '<=', '>', '>=',
        # Арифметика
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # Сокращенная арифметика
        '\+=', '-=', '\*=', '/=', '\%=',
        # Битовые операторы
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Скобки Python
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        # Многострочные коментарии (регулярное выражение, флаг, стиль)
        self.tri_single = (QRegExp("'''"), 1, STYLES['comment2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['comment2'])

        rules = []

        # (регулярное выражение, nth, стиль)
        # Добавляем правила для ключевых слов, операторов, скобок
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
                  for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
                  for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
                  for b in PythonHighlighter.braces]

        # Добавляем другие правила
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Строки в двойных кавычках, которые могут содержать escape-последовательности
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Строки в одинарных кавычках, которые могут содержать escape-последовательности
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # Идентефикатор def'а
            (r'\bdef\b\s*(\w+)', 1, STYLES['def_class']),
            # Идентефикатор class'а
            (r'\bclass\b\s*(\w+)', 1, STYLES['def_class']),

            # Коментарий от # до новой строки
            (r'#[^\n]*', 0, STYLES['comment1']),

            # Числа
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),
        ]

        # Создаем QRegExp для каждого шаблона
        self.rules = [(QRegExp(pat), index, fmt)
                          for (pat,  index, fmt) in rules]

    def highlightBlock(self, text):
        """Применяет подсветку синтаксиса следуя правилам, описанных нами.
           Вызывается, когда в тексте меняются блоки текста.
           (Мы переопределяем эту функцию из QSyntaxHighlighter)"""

        # Подсвечиваем синтаксис (expression - регулярное выражение для поиска
        #                         nth        - n-ое совпадение нужное нам
        #                         format      - стили редактируемого синтаксиса)
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)
            length = len(expression.cap(nth))
            while index >= 0:
                index = expression.pos(nth)
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        # Нужно для подсветки многострочных коментариев
        self.setCurrentBlockState(0)

        # Подсвечиваем многострочные коментарии
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, format):
        """Подсвечиваем многострочные коментарии.
        'delimiter' - это ограничение в виде QRegExp для тройных одинарных или двойных кавычек,
        'in_state'  - уникальное целое число для представления соответствующих изменений состояния внутри этих строк,
        'format'     - стили, применимые к многострочным коментариям.
        Возвращает True, если мы до сих пор в многострочном коментарии."""

        # Если внутри тройных одинарных кавычек, то начать сначала отсчет
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # В другом случае - искать ограничение (кавычки) на этой строке
        else:
            start = delimiter.indexIn(text)
            # Длинна совпадения
            add = delimiter.matchedLength()

        # Пока на этой линии есть ограничитель (кавычки)
        while start >= 0:
            # Находит завершиющий ограничитель (кавычки)
            end = delimiter.indexIn(text, start + add)
            # Зарершающий ограничитель (кавычки) на этой строке?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # Нет? значит все еще в многострочном коментарии
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Добавляем стили
            self.setFormat(start, length, format)
            # Смотрим ищем следующий ограничитель
            start = delimiter.indexIn(text, start + length)

        # Возвращаем True, если до сих пор в многострочном коментарии, иначе - False
        if self.currentBlockState() == in_state:
            return True
        else:
            return False
