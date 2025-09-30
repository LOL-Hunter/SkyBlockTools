import os
from datetime import timedelta, datetime, timezone
from threading import Thread
from time import sleep

import tksimple as tk
from core.analyzer import simulateElections, analyzeMayors
from core.constants import STYLE_GROUP as SG, MAYOR_PERK_AMOUNT, Path
from core.hyPI.APIError import APIConnectionError, NoAPIKeySetException, APITimeoutException
from core.hyPI.hypixelAPI.loader import HypixelMayorParser
from core.hyPI.parser import getMayorTimezone
from core.hyPI.skyCoflnetAPI import SkyConflnetAPI
from core.settings import Config
from core.skyMath import parseTimeDelta
from core.skyMisc import (
    parseTimeToStr,
    iterDict,
    throwAPITimeoutException,
    throwNoAPIKeyException,
    throwAPIConnectionException,
    requestMayorHypixelAPI,
    Sorter
)
from core.widgets import CustomPage, APIRequest


class MayorInfoPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Mayor Info Page", buttonText="Mayor Info")
        self.master = master
        self.currentMayorEnd = None
        Thread(target=self.updateTimer).start()

        self.images = self.loadMayorImages()

        self.currentMayorData:HypixelMayorParser = None
        self.mayorHistData:dict = None
        self.analyzedMayorData:dict = None
        self.simulatedElections:dict = None
        self.electionHasStarted = False
        self.electionSorters = []
        self.allVotes = 0

        self.notebook = tk.Notebook(self.contentFrame, SG)
        self.tabMayorCur = self.notebook.createNewTab("Current Mayor", SG)
        self.tabMayorHist = self.notebook.createNewTab("Next Election", SG)
        self.notebook.placeRelative()

        self.createCurrentTab(self.tabMayorCur)
        self.createHistoryTab(self.tabMayorHist)

        self.api = APIRequest(self, self._getTkMaster())
        self.api.setRequestAPIHook(self.requestAPIHook)
    def createCurrentTab(self, tab):
        self.topFrameCurr = tk.Frame(tab, SG)
        self.timerLf = tk.LabelFrame(self.topFrameCurr, SG)
        self.timerLf.setText("Time Remaining")

        self.timeLabel = tk.Label(self.timerLf, SG)
        self.timeLabel.setFg(tk.Color.rgb(227, 141, 30))
        self.timeLabel.setFont(20)
        self.timeLabel.placeRelative(changeWidth=-5, changeHeight=-20)

        self.timerLf.placeRelative(fixHeight=50, fixX=200) # fixWidth=395

        self.imageLf = tk.LabelFrame(self.topFrameCurr, SG)
        self.imageLf.setText("Current Mayor")
        self.imageDisplay = tk.Label(self.imageLf, SG).setText("No Image!")
        self.imageDisplay.placeRelative(fixWidth=100, fixHeight=230, fixX=5, changeHeight=-15, changeWidth=-15)
        self.imageLf.placeRelative(fixWidth=100, fixHeight=240)

        self.imageLf2 = tk.LabelFrame(self.topFrameCurr, SG)
        self.imageLf2.setText("Current Minister")
        self.imageDisplay2 = tk.Label(self.imageLf2, SG).setText("No Image!")
        self.imageDisplay2.placeRelative(fixWidth=100, fixHeight=230, fixX=5, changeHeight=-15, changeWidth=-15)
        self.imageLf2.placeRelative(fixX=100, fixWidth=100, fixHeight=240)

        self.dataLf = tk.LabelFrame(self.topFrameCurr, SG)
        self.dataLf.setText("Data")
        self.dataText = tk.Text(self.dataLf, SG, readOnly=True)
        self.dataText.setFont(15)
        self.dataText.placeRelative(changeWidth=-5, changeHeight=-20)
        self.dataLf.placeRelative(fixX=200, fixY=50, fixHeight=140+50) #fixWidth=395

        self.dataLf = tk.LabelFrame(self.topFrameCurr, SG)
        self.dataLf.setText("Perks")
        self.dataTextPerks = tk.ScrollableText(self.dataLf, SG, readOnly=True)
        self.dataTextPerks.setFont(15)
        self.dataTextPerks.setWrapping(tk.Wrap.WORD)
        self.dataTextPerks.placeRelative(changeWidth=-5, changeHeight=-20)
        self.dataLf.placeRelative(fixX=0, fixY=240) # fixWidth=595, fixHeight=250

        self.topFrameCurr.placeRelative() # fixWidth=600, centerX=True
    def createHistoryTab(self, tab):
        self.dataLf2 = tk.LabelFrame(tab, SG)
        self.dataLf2.setText("Data")
        self.dataPrediction = tk.Text(self.dataLf2, SG, readOnly=True)
        self.dataPrediction.setFont(15)
        self.dataPrediction.placeRelative(changeWidth=-5, changeHeight=-20)
        self.dataLf2.placeRelative(fixHeight=240)

        self.lfPrediction = tk.LabelFrame(tab, SG)
        self.lfPrediction.setText("Prediction")
        self.dataPredictionMayor = tk.ScrollableText(self.lfPrediction, SG, readOnly=True)
        self.dataPredictionMayor.setFont(15)
        self.dataPredictionMayor.placeRelative(changeWidth=-5, changeHeight=-20)
        self.lfPrediction.placeRelative(fixY=240, xOffsetRight=50)

        self.lfNext = tk.LabelFrame(tab, SG)
        self.lfNext.setText("Next-Election")
        self.dataNextMayor = tk.ScrollableText(self.lfNext, SG, readOnly=True)
        self.dataNextMayor.setFont(15)
        self.dataNextMayor.placeRelative(changeWidth=-5, changeHeight=-20)
        self.lfNext.placeRelative(fixY=240, xOffsetLeft=50)
    def configureContentFrame(self):
        mayorName = self.currentMayorData.getMainMayorName()
        ministerName = self.currentMayorData.getMinisterName()
        currYear = self.currentMayorData.getCurrentYear()

        mayorPerks = self.currentMayorData.getMainMayorPerks()
        mayorPerkCount = self.currentMayorData.getMainMayorPerksAmount()

        ministerPerk = self.currentMayorData.getMinisterPerk()

        self.currentMayorEnd = getMayorTimezone(self.mayorHistData[-1]["end"])

        delta:timedelta = self.currentMayorEnd - self.getLocalizedNow()
        self.timeLabel.setText(parseTimeToStr(parseTimeDelta(delta)))

        dataContent = {
            "Mayor Name:": mayorName,
            "Minister Name:": ministerName,
            "Year:": currYear,
            "Perks:": f"[{mayorPerkCount}/{MAYOR_PERK_AMOUNT[mayorName]}]"
        }
        self.dataText.setText(f"\n".join([f"{k} {v}" for k, v in iterDict(dataContent)]))

        out = "§o" + "Mayor-Perks" + "\n"
        for perk in mayorPerks:
            perkName = perk["name"]
            perkDesc = perk["description"]

            for enc in ["\xa7e", "\xa77", "\xa76", "\u2663", "\xa7d", "\xa7a", "\xa75", "\xa7b", "\u262f", "§3", "§9"]:
                perkDesc = perkDesc.replace(enc, "")

            out += f"§g== {perkName} ==\n"
            out += f"§c{perkDesc}\n"

        out += "\n\n§o" + "Minister-Perk" + "\n"

        perkName = ministerPerk["name"] if ministerPerk is not None else "None"
        perkDesc = ministerPerk["description"] if ministerPerk is not None else "None"

        perkDesc = perkDesc.encode('ascii', 'ignore').decode()
        out += f"§g== {perkName} ==\n"
        out += f"§c{perkDesc}\n"

        self.dataTextPerks.clear()
        self.dataTextPerks.addStrf(out)

        if mayorName.lower() in self.images.keys():
            self.imageDisplay.setImage(self.images[mayorName.lower()])
        else:
            self.imageDisplay.clearImage()
            self.imageDisplay.setText("No Image!")

        if ministerName is not None and ministerName.lower() in self.images.keys():
            self.imageDisplay2.setImage(self.images[ministerName.lower()])
        else:
            self.imageDisplay2.clearImage()
            self.imageDisplay2.setText("No Image!")

        out = ""
        for mayor in self.analyzedMayorData["next_perks"].keys():
            out += f"{self._chCC(self.analyzedMayorData['next_perks'][mayor])} === {mayor} ===\n"
            for perk in self.analyzedMayorData["next_perks"][mayor]["available_perks"]:
                out += f"\t§g{perk['name']}\n"
            for i, chance in enumerate(self.simulatedElections[mayor]["chances"]):
                out += f"\t§oChance to gain +{i} perks: {round(chance*100, 2)}%\n"
        self.dataPredictionMayor.clear()
        self.dataPredictionMayor.addStrf(out)

        dataContent = {
            "Possible Mayors:": len(self.analyzedMayorData["next_perks"].keys()),
            "Next Special Mayor:": self.analyzedMayorData["next_special_name"],
            "Next Special Mayor in": f"{self.analyzedMayorData['next_special_in_years']} Years! ({self.analyzedMayorData['next_special_year']})",
            "Next Year:": currYear+1
        }
        self.dataPrediction.setText(f"\n".join([f"{k} {v}" for k, v in iterDict(dataContent)]))

        self.lfNext.setText(f"Next-Election [year-{currYear+1}]")
        if self.electionHasStarted:
            self.lfPrediction.setText(f"Prediction [year-{currYear + 2}]")
            out = ""
            for sorter in self.electionSorters:
                if self.allVotes:
                    perc = (sorter["votes"] / self.allVotes) * 100
                    out += f"§c === {sorter['name']} ({round(perc, 2)}%) ===\n"
                else:
                    out += f"§c === {sorter['name']} (HIDDEN) ===\n"
                for perk in sorter["perks"]:
                    out += f"\t§g{perk['name']}\n"
            self.dataNextMayor.clear()
            self.dataNextMayor.addStrf(out)
        else:
            self.lfPrediction.setText(f"Prediction [year-{currYear+1}]")
            self.dataNextMayor.setText("Election not Started Yet!")
    def _chCC(self, data):
        """
        choose Color Code
        """
        if data["is_special"]:
            return "§m"
        if data["has_full_perks"]:
            return "§y"
        return "§c"
    def getLocalizedNow(self)->datetime:
        return timezone("Europe/Berlin").localize(datetime.now())
    def updateTimer(self):
        while True:
            sleep(1)
            if self.currentMayorEnd is None: continue
            delta: timedelta = self.currentMayorEnd - self.getLocalizedNow()
            self.timeLabel.setText(parseTimeToStr(parseTimeDelta(delta)))
    def loadMayorImages(self):
        images = {}
        pathMayor = os.path.join(Path.IMAGES, "mayors")
        for fName in os.listdir(pathMayor):
            path = os.path.join(pathMayor, fName)
            name = fName.split(".")[0]
            image = tk.PILImage.loadImage(path)
            image.resizeTo(500, 1080)
            image.resize(.2, useOriginal=False)
            image.preRender()
            images[name] = image
        return images
    def requestAPIHook(self):
        try:
            self.mayorHistData = SkyConflnetAPI.getMayorData()
        except APIConnectionError as e:
            throwAPIConnectionException(
                source="Mayor",
                master=self.master,
                event=e
            )
            return
        except NoAPIKeySetException as e:
            throwNoAPIKeyException(
                source="Mayor",
                master=self.master,
                event=e
            )
            return
        except APITimeoutException as e:
            throwAPITimeoutException(
                source="Mayor",
                master=self.master,
                event=e
            )
            return
        self.currentMayorData = requestMayorHypixelAPI(self.master, Config)
        yearOffset = 0
        if self.currentMayorData is not None and self.mayorHistData is not None:
            yearOffset = 1
            self.electionHasStarted = self.currentMayorData.hasElectionStarted()
            mayorHistData = self.mayorHistData.copy()
            minister = self.currentMayorData.getMinisterName()
            isLTI = (self.currentMayorData.getMinisterPerkName() == "Long Term Investment")
            if self.electionHasStarted: # add data from election to predict next election
                self.electionSorters = []
                self.allVotes = 0
                for candidate in self.currentMayorData.getCurrentCandidates():
                    self.electionSorters.append(
                        Sorter(
                            sortKey="votes",
                            votes=candidate["votes"] if "votes" in candidate.keys() else 0,
                            name=candidate["name"],
                            perks=candidate["perks"]
                        )
                    )
                    self.allVotes += candidate["votes"] if "votes" in candidate.keys() else 0
                self.electionSorters.sort()

                winner = self.electionSorters[0]
                minister = self.electionSorters[1]["name"]
                isLTI = "Long Term Investment" in [perk["name"] for perk in self.electionSorters[1]["perks"] if perk["minister"]]

                mayorHistData.append(
                    {
                        "year":mayorHistData[-1]["year"]+1,
                        "candidates":self.currentMayorData.getCurrentCandidates(),
                        "winner": {
                            "name":winner["name"],
                            "perks":winner["perks"]
                        }
                    }
                )
            self.analyzedMayorData = analyzeMayors(
                mayorHistData,
                minister,
                isLTI,
                yearOffset
            )

            self.simulatedElections = simulateElections(self.analyzedMayorData)

            self.configureContentFrame()
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = None  # hook to update tv on new API-Data available
        self.placeRelative()
        self.api.startAPIRequest()