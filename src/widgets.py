from constants import STYLE_GROUP as SG
from pysettings import tk
import os



class CompleterEntry(tk.Entry):
    def __init__(self, _master):
        if isinstance(_master, dict):
            self.data = _master
        elif isinstance(_master, tk.Tk) or isinstance(_master, tk.Frame) or isinstance(_master, tk.LabelFrame) or isinstance(_master, tk.NotebookTab):
            #data = {"master":_master, "widget":_tk_.Entry(_master._get())}
            super().__init__(_master, SG)
            #self._addData(data)
            self.selected = -1 # selected index during the lb is open
            self._listBox = tk.Listbox(_master, SG)
            self.bind(self._onRelPlace, tk.EventType.CUSTOM_RELATIVE_UPDATE)
            self.bind(self._up, "<Up>")
            self.bind(self._down, "<Down>")
            self.bind(self._escape, "<Escape>")
            self._listBox.bind(self._escape, "<Escape>")
            self.isListboxOpen = False
            self._scroll = tk.ScrollBar(_master)
            self._listBox.attachVerticalScrollBar(self._scroll)
            self._rect = None
        else:
            raise tk.TKExceptions.InvalidWidgetTypeException("_master must be " + str(self.__class__.__name__) + ", Frame or Tk instance not: " + str(_master.__class__.__name__))
    def _up(self, e):
        if self.isListboxOpen:
            selected = self._listBox.getSelectedIndex()
            if selected is None or selected == 0:
                selected = -1
                self._listBox.clearSelection()
                #self._listBox.setItemSelectedByIndex(0)
            else:
                if selected > 0:
                    selected -= 1
                    self._listBox.setItemSelectedByIndex(selected)


            self._listBox.see(selected)
            self.selected = selected
    def _down(self, e):
        if self.isListboxOpen:
            selected = self._listBox.getSelectedIndex()
            if selected is None:
                selected = 0
                self._listBox.setItemSelectedByIndex(0)
            else:
                if selected < self._listBox.length():
                    selected += 1
                    self._listBox.setItemSelectedByIndex(selected)

            self._listBox.see(selected)
            self.selected = selected
    def _escape(self, e):
        self.closeListbox()
    def _updateMenu(self, e, out):
        if out is None or self._rect is None or out == [] or e.getTkArgs().keysym == "Escape" or (e.getTkArgs().keysym == "Return" and self.selected == -1):
            self.isListboxOpen = False
            self._listBox.placeForget()
            self._scroll.placeForget()
            return
        if not self.isListboxOpen:
            rect = tk.Rect.fromLocWidthHeight(tk.Location2D(self._rect.loc1.clone()), self._rect.getWidth()-20, self._rect.getHeight())
            rect2 = tk.Rect.fromLocWidthHeight(tk.Location2D(self._rect.loc1.clone()).change(x=+self._rect.getWidth()-20), 20, self._rect.getHeight())
            self._listBox.place(rect)
            self._scroll.place(rect2)
        self.isListboxOpen = True
        selected = -1
        if self._listBox.length() == len(out) and self._listBox.getSelectedIndex() is not None:
            selected = self.selected
        self._listBox.clear()
        self._listBox.addAll(out)
        if selected == -1: return
        self._listBox.setItemSelectedByIndex(selected)
        self._listBox.see(selected)
    def _onListboxSelect(self, e):
        if e.type == "35" or e.keysym == "Escape": #virtual event triggered by shift-Left? without no marking
            return None
        #entry = self.getValue()
        #if self.selected == -1:
        #    self.closeListbox()
        #    return self.getValue()
        selected = self._listBox.getSelectedItem()
        if selected is None: return None
        self.setValue(selected)
        self.closeListbox()
        return selected
    def closeListbox(self):
        self.isListboxOpen = False
        self._listBox.placeForget()
    def _decryptEvent(self, args):
        return args
    def onUserInputEvent(self, func, args:list=None, priority:int=0, defaultArgs=False, disableArgs=False):
        event = tk.EventHandler._registerNewEvent(self, func, tk.EventType.KEY_UP, args, priority, decryptValueFunc=self._decryptEvent, defaultArgs=defaultArgs, disableArgs=disableArgs)
        event["afterTriggered"] = self._updateMenu
    """def onListBoxSelectEvent(self, func, args: list = None, priority: int = 0, defaultArgs=False, disableArgs=False):
        self._listboxSelect = tk.EventHandler._registerNewEvent(self._listBox, func, tk.EventType.LISTBOX_SELECT, args, priority, defaultArgs=defaultArgs, disableArgs=disableArgs, decryptValueFunc=self.__decryptEvent)"""
    def onSelectEvent(self, func, args: list = None, priority: int = 0, defaultArgs=False, disableArgs=False):
        tk.EventHandler._registerNewEvent(self._listBox, func, tk.EventType.LISTBOX_SELECT, args, priority, decryptValueFunc=self._onListboxSelect, defaultArgs=defaultArgs, disableArgs=disableArgs)
        tk.EventHandler._registerNewEvent(self._listBox, func, tk.EventType.DOUBBLE_LEFT, args, priority, decryptValueFunc=self._onListboxSelect, defaultArgs=defaultArgs, disableArgs=disableArgs)
        tk.EventHandler._registerNewEvent(self, func, tk.EventType.RETURN, args, priority, decryptValueFunc=self._onListboxSelect, defaultArgs=defaultArgs, disableArgs=disableArgs)
    def __decryptEvent(self, args):
        try:
            w = args.widget
            if self._listBox["selectionMode"] == tk.Listbox.SINGLE:
                return w.get(int(w.curselection()[0]))
            else:
                return [w.get(int(i)) for i in w.curselection()]
        except IndexError:
            pass
    def _onRelPlace(self, e):
        if e.getValue() is None: return

        x, y, width, height = e.getValue()
        self._rect = tk.Rect.fromLocWidthHeight(tk.Location2D(x, y + height), width, 200)
    def place(self, x=None, y=None, width=None, height=None, anchor:tk.Anchor=tk.Anchor.UP_LEFT):
        assert not self["destroyed"], "The widget has been destroyed and can no longer be placed."
        if x is None: x = 0
        if y is None: y = 0
        if hasattr(anchor, "value"):
            anchor = anchor.value
        if isinstance(x, tk.Location2D):
            x, y = x.get()
        if isinstance(x, tk.Rect):
            width = x.getWidth()
            height = x.getHeight()
            x, y, = x.getLoc1().get()
        x = int(round(x, 0))
        y = int(round(y, 0))
        self.placeForget()
        self._rect = tk.Rect.fromLocWidthHeight(tk.Location2D(x, y + height), width, 180)
        self["widget"].place(x=x, y=y, width=width, height=height, anchor=anchor)
        self["alive"] = True
        return self