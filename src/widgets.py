from constants import STYLE_GROUP as SG, AUCT_INFO_LABEL_GROUP as AILG, BAZAAR_INFO_LABEL_GROUP as BILG
from pysettings import tk
from analyzer import getPlotData
from constants import Constants, ConfigFile
from skyMath import getMedianFromList
from hyPI.skyCoflnetAPI import SkyConflnetAPI
from hyPI.APIError import APIConnectionError, NoAPIKeySetException
from pysettings.text import TextColor
from traceback import format_exc
from images import IconLoader
from threading import Thread

class SettingValue(tk.Frame):
    CONFIG = None
    def __init__(self, master, name, x, y, key):
        super().__init__(master, SG)
        self._key = key
        self._e = tk.TextEntry(self, SG)
        self._e.setValue(SettingValue.CONFIG["constants"][key])
        self._e.setText(name)
        self._e.getEntry().onUserInputEvent(self._set)
        self._e.place(0, 0, 250, 30)

        tk.Button(self, SG).setText("Reset").setCommand(self._reset).place(250, 0, 50, 30)

        self.place(x, y, 300, 30)
    def _reset(self):
        SettingValue.CONFIG["constants"][self._key] = SettingValue.CONFIG._std["constants"][self._key]
        SettingValue.CONFIG.save()
        self._e.setValue(SettingValue.CONFIG["constants"][self._key])

    def _set(self):
        SettingValue.CONFIG["constants"][self._key] = self._e.getValue()
        SettingValue.CONFIG.save()
class CustomPage(tk.MenuPage):
    """
    Custom Content Page. Uses the tk MenuPage to act as a Menu-page with history.
    Offers a build in Title set with: 'pageTitle' in __init__
    Toggleable Back-Button to get to the previous menu page.
    Toggleable Home-Button to get to the home menu page.

    Set the 'buttonText' parameter to select witch text should be displayed on the Menu-Button to this Page.

    place all widgets to build in content widget! -> 'contentFrame'

    """
    def __init__(self, master, pageTitle:str="", buttonText:str="", showBackButton=True, showTitle=True, showHomeButton=True, showInfoLabel=True, **kwargs):
        super().__init__(master, SG)
        self._buttonText = buttonText
        self._pageTitle = pageTitle
        self.master = master
        self.contentFrame = tk.Frame(self, SG)
        if showTitle and pageTitle is not None:
            self._titleL = tk.Label(self, SG).setFont(16).setText(pageTitle).placeRelative(centerX=True, fixHeight=30, fixY=10)
        if showBackButton:
            tk.Button(self, SG).setText("<Back").setCommand(self.openLastMenuPage).placeRelative(stickDown=True, fixWidth=100, fixHeight=40)
        if showHomeButton:
            tk.Button(self, SG).setImage(IconLoader.ICONS["home"]).setCommand(self._home).placeRelative(stickDown=True, stickRight=True, fixWidth=100, fixHeight=40)
        if showInfoLabel:
            self._info = tk.Label(self, AILG).placeRelative(stickDown=True, fixHeight=15, changeX=100, changeWidth=-200, changeY=-15)
            self._info2 = tk.Label(self, BILG).placeRelative(stickDown=True, fixHeight=15, changeX=100, changeWidth=-200)
    def _home(self):
        self.master.mainMenuPage._menuData["history"] = [self.master.mainMenuPage]
        self.placeForget()
        self.master.mainMenuPage.openMenuPage()
    def setPageTitle(self, t:str):
        self._titleL.setText(t)
    def placeContentFrame(self):
        self.contentFrame.placeRelative(fixY=40, changeHeight=-40)
    def hideContentFrame(self):
        self.contentFrame.placeForget()
    def getButtonText(self):
        return self._pageTitle if self._buttonText is None else self._buttonText
    def customShow(self, page):
        """
        Overwrite if you want custom show:
        per example:
        self.openNextMenuPage(self.master.searchPage,
                                                  input=[BazaarItemID],
                                                  msg="Search in Bazaar: (At least tree characters)",
                                                  next_page=self.master.itemInfoPage)

        except it will be :

        @return: if 1 continue to next page
        """
        return 1
class CustomMenuPage(CustomPage):
    """
    Menu Page with build in Menu button control.

    """
    def __init__(self, master, pageTitle:str="", buttonText:str="", showBackButton=True, showTitle=True, **kwargs):
        super().__init__(master, pageTitle, buttonText, showBackButton=showBackButton, showTitle=showTitle, **kwargs)
        self.master = master
    def _run(self, e:tk.Event):
        """
        Opens the right page!

        @param e:
        @return:
        """
        menuButton = e.getArgs(0)

        if menuButton.customShow(self) is None: return
        if isinstance(menuButton, tk.MenuPage):
            self.openNextMenuPage(menuButton)
        else: raise()
    def onShow(self):
        """
        triggerd from backend on show page!
        @return:
        """
        self.placeRelative()
class CompleterEntry(tk.Entry):
    def __init__(self, _master):
        if isinstance(_master, dict):
            self.data = _master
        elif isinstance(_master, tk.Tk) or isinstance(_master, tk.Frame) or isinstance(_master, tk.LabelFrame) or isinstance(_master, tk.NotebookTab):
            #data = {"master":_master, "widget":_tk_.Entry(_master._get())}
            super().__init__(_master, SG)
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
        event = tk._EventHandler._registerNewEvent(self, func, tk.EventType.KEY_UP, args, priority, decryptValueFunc=self._decryptEvent, defaultArgs=defaultArgs, disableArgs=disableArgs)
        event["afterTriggered"] = self._updateMenu
    """def onListBoxSelectEvent(self, func, args: list = None, priority: int = 0, defaultArgs=False, disableArgs=False):
        self._listboxSelect = tk._EventHandler._registerNewEvent(self._listBox, func, tk.EventType.LISTBOX_SELECT, args, priority, defaultArgs=defaultArgs, disableArgs=disableArgs, decryptValueFunc=self.__decryptEvent)"""
    def onSelectEvent(self, func, args: list = None, priority: int = 0, defaultArgs=False, disableArgs=False):
        tk._EventHandler._registerNewEvent(self._listBox, func, tk.EventType.LISTBOX_SELECT, args, priority, decryptValueFunc=self._onListboxSelect, defaultArgs=defaultArgs, disableArgs=disableArgs)
        tk._EventHandler._registerNewEvent(self._listBox, func, tk.EventType.DOUBBLE_LEFT, args, priority, decryptValueFunc=self._onListboxSelect, defaultArgs=defaultArgs, disableArgs=disableArgs)
        tk._EventHandler._registerNewEvent(self, func, tk.EventType.RETURN, args, priority, decryptValueFunc=self._onListboxSelect, defaultArgs=defaultArgs, disableArgs=disableArgs)
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
class TrackerWidget(tk.LabelFrame):
    def __init__(self, master, window, title):
        super().__init__(master, SG)
        self.master = window
        self.setText(title)
        self._hook = None

        self.treeView = tk.TreeView(self, SG)
        self.treeView.setTableHeaders(
            "Item",
            "Buy-Price",
            "Sell-Price",
            "Profit-Per-Item",
            "Time",
        )
        self.treeView.bind(self._onItemInfo, tk.EventType.DOUBBLE_LEFT)
        self.treeView.placeRelative(changeWidth=-3, changeHeight=-50)

        self.showType = tk.DropdownMenu(self, SG, [
            "All",
            "New",
        ])
        self.showType.setText("All")
        self.showType.placeRelative(stickDown=True, changeY=-25, fixWidth=100, fixHeight=25)

        self.notify = tk.Checkbutton(self, SG)
        self.notify.setText("Notification")
        self.notify.placeRelative(stickDown=True, changeY=-25, fixWidth=100, fixHeight=25, fixX=100)

        self.filterEnchantments = tk.Checkbutton(self, SG).setSelected()
        self.filterEnchantments.onSelectEvent(self._runHook)
        self.filterEnchantments.setText("Filter Enchantments")
        self.filterEnchantments.placeRelative(stickDown=True, changeY=-25, fixWidth=100, fixHeight=25, fixX=200)

        self.rMenu = tk.ContextMenu(self.treeView, SG)
        tk.Button(self.rMenu).setText("Request Average Price...").setCommand(self._requestAverage)
        self.rMenu.create()
    def _runHook(self):
        if self._hook is not None:
            self._hook()
    def _onItemInfo(self):
        sel = self.treeView.getSelectedItems()
        if sel is None: return
        self.master.showItemInfo(self, sel[0]["Item"])
    def _saveAverage(self):
        ConfigFile.AVERAGE_PRICE.saveConfig()
    def setUpdateHook(self, h):
        self._hook = h
    def _requestAverage(self):
        def request():
            try:
                self.currentHistoryData = getPlotData(id_, SkyConflnetAPI.getBazaarHistoryWeek)
            except APIConnectionError as e:
                TextColor.print(format_exc(), "red")
                tk.SimpleDialog.askError(self.master, e.getMessage(), "SkyBlockTools")
                Constants.WAITING_FOR_API_REQUEST = False
                return None
            except NoAPIKeySetException as e:
                TextColor.print(format_exc(), "red")
                tk.SimpleDialog.askError(self.master, e.getMessage(), "SkyBlockTools")
                Constants.WAITING_FOR_API_REQUEST = False
                return None
            Constants.WAITING_FOR_API_REQUEST = False

            ConfigFile.AVERAGE_PRICE[id_] = getMedianFromList(self.currentHistoryData["past_raw_buy_prices"])
            if self._hook is not None: self.master.runTask(self._hook).start()
            self.master.runTask(self._saveAverage).start()

        if not Constants.WAITING_FOR_API_REQUEST:
            selected = self.treeView.getSelectedItems()
            if selected is None: return
            id_ = selected[0]["Item"]

            Constants.WAITING_FOR_API_REQUEST = True
            Thread(target=request).start()




