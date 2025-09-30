import tksimple as tk
from time import time

from core.bazaarAnalyzer import BazaarAnalyzer, updateBazaarAnalyzer
from core.constants import Color
from core.settings import Config
from core.skyMisc import parsePrizeToStr, parseTimeFromSec, playNotificationSound
from core.widgets import CustomPage, TrackerWidget


class ItemPriceTrackerPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Price Tracker", buttonText="Price Tracker")
        self._notificationsDisabled = False

        self.customTrackers = TrackerWidget(self.contentFrame, master, "Custom-Tracker")
        self.flipTrackers = TrackerWidget(self.contentFrame, master, "Flip-Tracker")
        self.crashTrackers = TrackerWidget(self.contentFrame, master, "Crash-Tracker")
        self.manipulationTrackers = TrackerWidget(self.contentFrame, master, "Manipulation-Tracker")

        self.customTrackers.setUpdateHook(self.onUpdate)
        self.flipTrackers.setUpdateHook(self.onUpdate)
        self.crashTrackers.setUpdateHook(self.onUpdate)
        self.manipulationTrackers.setUpdateHook(self.onUpdate)

        self.customTrackers.placeRelative(xOffsetRight=50, yOffsetDown=50)
        self.crashTrackers.placeRelative(xOffsetLeft=50, yOffsetDown=50)
        self.flipTrackers.placeRelative(xOffsetRight=50, yOffsetUp=50)
        self.manipulationTrackers.placeRelative(xOffsetLeft=50, yOffsetUp=50)

        self.customTrackers.notify.onSelectEvent(self.updateNotificationFromCheck)
        self.crashTrackers.notify.onSelectEvent(self.updateNotificationFromCheck)
        self.manipulationTrackers.notify.onSelectEvent(self.updateNotificationFromCheck)
        self.flipTrackers.notify.onSelectEvent(self.updateNotificationFromCheck)

        self.updateNotificationFromSettings()
        self.customTrackers.showType.placeForget()
    def updateNotificationFromSettings(self):
        self.customTrackers.notify.setState(Config.SETTINGS_CONFIG["notifications"]["tracker_custom"])
        self.crashTrackers.notify.setState(Config.SETTINGS_CONFIG["notifications"]["tracker_crash"])
        self.flipTrackers.notify.setState(Config.SETTINGS_CONFIG["notifications"]["tracker_flip"])
        self.manipulationTrackers.notify.setState(Config.SETTINGS_CONFIG["notifications"]["tracker_manipulation"])
    def updateNotificationFromCheck(self):
        Config.SETTINGS_CONFIG["notifications"]["tracker_custom"] = self.customTrackers.notify.getValue()
        Config.SETTINGS_CONFIG["notifications"]["tracker_crash"] = self.crashTrackers.notify.getValue()
        Config.SETTINGS_CONFIG["notifications"]["tracker_flip"] = self.flipTrackers.notify.getValue()
        Config.SETTINGS_CONFIG["notifications"]["tracker_manipulation"] = self.manipulationTrackers.notify.getValue()
        Config.SETTINGS_CONFIG.save()
    def onUpdate(self):
        """
        Triggers update after new Average request!
        @return:
        """
        updateBazaarAnalyzer()
        self.updateTreeView()
    def addNewCustomItem(self):
        pass
    def updateTreeView(self):
        notify = False
        self.manipulationTrackers.treeView.clear()
        manipulated = BazaarAnalyzer.getManipulatedItems()
        containsNew = False
        filterEnchantments = self.manipulationTrackers.filterEnchantments.getState()
        for sorter, _time in manipulated:
            if sorter["ID"].startswith("ENCHANTMENT_") and filterEnchantments: continue
            self.manipulationTrackers.treeView.addEntry(
                sorter["ID"],
                parsePrizeToStr(sorter["buyOrderPrice"], True),
                parsePrizeToStr(sorter["sellOrderPrice"], True),
                parsePrizeToStr(sorter["priceDifference"], True) + ("" if sorter["priceDifferenceChance"] == 0 else f" ({parsePrizeToStr(sorter['priceDifferenceChance'], True, True)})"),
                parseTimeFromSec(time()-_time),

                tag=sorter["manipulatedState"]
            )
            if sorter["manipulatedState"] == "new":
                containsNew = True
        self.manipulationTrackers.setText(f"Manipulation-Tracker [{self.manipulationTrackers.treeView.getSize()}]")
        self.manipulationTrackers.treeView.setBgColorByTag("old", Color.COLOR_DARK)
        self.manipulationTrackers.treeView.setBgColorByTag("new", "green")
        if self.manipulationTrackers.notify.getState():
            if containsNew: notify = True
        containsNew = False


        self.crashTrackers.treeView.clear()
        crashed = BazaarAnalyzer.getCrashedItems()
        crashed.sort()
        filterEnchantments = self.crashTrackers.filterEnchantments.getState()
        for sorter, _time in crashed:
            if sorter["ID"].startswith("ENCHANTMENT_") and filterEnchantments: continue
            self.crashTrackers.treeView.addEntry(
                sorter["ID"],
                parsePrizeToStr(sorter["buyOrderPrice"], True),
                parsePrizeToStr(sorter["sellOrderPrice"], True),
                parsePrizeToStr(sorter["priceDifference"], True) + ("" if sorter["priceDifferenceChance"] == 0 else f" ({parsePrizeToStr(sorter['priceDifferenceChance'], True, True)})"),
                parseTimeFromSec(time() - _time),
                tag=sorter["crashedState"]
            )
            if sorter["crashedState"] == "new":
                containsNew = True
        self.crashTrackers.setText(f"Crash-Tracker [{self.crashTrackers.treeView.getSize()}]")
        if self.crashTrackers.notify.getState():
            if containsNew: notify = True
        self.crashTrackers.treeView.setBgColorByTag("old", Color.COLOR_DARK)
        self.crashTrackers.treeView.setBgColorByTag("new", "green")

        if notify and not self._notificationsDisabled:
            playNotificationSound()
        self._notificationsDisabled = False
    def disableNotifications(self):
        self._notificationsDisabled = True
        return self
    def onAPIUpdate(self):
        self.updateTreeView()
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = None # hook to update tv on new API-Data available
        self.placeRelative()
        self.disableNotifications()
        self.updateTreeView()
        self.placeContentFrame()
        if not Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"]: tk.SimpleDialog.askWarning(self.master, "This feature requires 'auto_api_requests' feature to be active!\nTurn on In Settings or in the opper left corner in MainMenu!")