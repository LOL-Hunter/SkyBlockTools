from gui import Window
from os import _exit
from pysettings.text import Title, Color, MsgText

if __name__ == '__main__':
    Title().print("Sky Block Tools", Color.GREEN)
    window = Window()
    MsgText.info("GUI opened successfully!")
    window.mainloop()
    _exit(0)