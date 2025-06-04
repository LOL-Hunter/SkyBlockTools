from gui import Window
from os import _exit
from logger import Title, MsgText



if __name__ == '__main__':
    Title().print("Sky Block Tools", "green")
    window = Window()
    MsgText.info("GUI opened successfully!")
    window.mainloop()
    _exit(0)