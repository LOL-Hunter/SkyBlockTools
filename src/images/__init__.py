import os
import tksimple as tk
from pysettings.text import MsgText

PATH = os.path.split(os.path.realpath(__file__))[0]
ICON_PATH = os.path.join(PATH, "icons")



class IconLoader:
    ICONS = {}
    @staticmethod
    def loadIcons():
        icons = 0
        MsgText.info("Loading icons...")

        for image in os.listdir(ICON_PATH):
            icons += 1
            _ext = image.split(".")[0]
            IconLoader.ICONS[_ext] = tk.PILImage.loadImage(os.path.join(ICON_PATH, image)).resizeTo(32, 32).preRender()
        MsgText.info(f"Successfully loaded {icons} icons!")