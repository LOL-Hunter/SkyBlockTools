import time as t
import pyfiglet as py
import termcolor as c
from enum import Enum

class Color(Enum):
    GREY = "grey"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    WHITE = "white"
    BLACK = None
class Title:
    def __init__(self, font="big"):
        self._title = py.Figlet(font=font)
    def print(self, text, col=Color.BLACK):
        TextColor.print(self._title.renderText(text), col)
    def get(self, text):
        return self._title.renderText(text)
class TextColor:
    @staticmethod
    def _strf(text):
        """
                §D: DEFAULT
                §W: WHITE
                §B: BLACK

                §r: RED
                §g: GREEN
                §b: BLUE
                §c: CYAN
                §y: YELLOW
                §m: MAGENTA

                @param text:
                @return:
                """

        colors = {'§W':Color.WHITE.value,
                  '§B':Color.BLACK.value,
                  '§r':Color.RED.value,
                  '§g':Color.GREEN.value,
                  '§b':Color.BLUE.value,
                  '§c':Color.CYAN.value,
                  '§y':Color.YELLOW.value,
                  '§m':Color.MAGENTA.value}
        text = text.replace("§INFO", t.strftime("§g[INFO-%H:%M:%S]: "))
        text = text.replace("§ERROR", t.strftime("§r[ERROR-%H:%M:%S]: "))
        text = text.replace("§WARN", t.strftime("§y[WARNING-%H:%M:%S]: "))

        fmt_str = "\033[%dm"
        for k, v in zip(colors.keys(), colors.values()):
            while k in text:
                text = text.replace(k, fmt_str % c.COLORS[v])
        return text
    @staticmethod
    def getStrf(text):
        return TextColor._strf(text)
    @staticmethod
    def printStrf(text):
        print(TextColor._strf(text))
    @staticmethod
    def get(text, col=Color.BLACK):
        if hasattr(col, "value"): col = col.value
        return c.colored(text, color=col)
    @staticmethod
    def print(text, col=Color.BLACK, end="\n"):
        if hasattr(col, "value"): col = col.value
        print(c.colored(text, color=col), end=end)
class MsgText:
    @staticmethod
    def info(msg):
        TextColor.print(t.strftime("[INFO-%H:%M:%S]: ")+str(msg), Color.GREEN)
    @staticmethod
    def warning(msg):
        TextColor.print(t.strftime("[WARNING-%H:%M:%S]: ")+str(msg), Color.YELLOW)
    @staticmethod
    def error(msg, exit_=False):
        TextColor.print(t.strftime("[ERROR-%H:%M:%S]: ") + str(msg), Color.RED)
