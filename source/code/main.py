from AppKit import NSFont, NSBeep, NSObject
import vanilla
from mojo.UI import CurrentGlyphWindow, StatusInteractivePopUpWindow
from booster.controller import BoosterController

debug = False
controllerIdentifier = "com.typesupply.PasteGlyph"
lastPasteLibKey = "com.typesupply.PasteGlyph.lastPastedGlyphName"


class PasteGlyphController(BoosterController):

    identifier = controllerIdentifier

    def start(self, glyph):
        super(PasteGlyphController, self).start()

        self.history = []

        self.currentGlyph = glyph

        top = 15
        titleL = 15
        titleW = 50
        inputL = 75
        inputW = -15

        width = 370
        height = 505
        editorWindow = CurrentGlyphWindow()
        (editorX, editorY, editorW, editorH), screen = getGlyphEditorRectAndScreen(editorWindow)
        x = editorX + ((editorW - width) / 2)
        y = editorY + ((editorH - height) / 2)
        self.w = StatusInteractivePopUpWindow((x, y, width, height), screen=screen)

        self.w.sourceTitle = vanilla.TextBox((titleL, top, inputW, 17), "Source")
        top += 25
        self.w.sourceLine = vanilla.HorizontalLine((titleL, top, inputW, 1))
        top += 15

        self.w.sourceFontTitle = vanilla.TextBox((titleL, top+2, titleW, 17), "Font:", alignment="right")
        self.w.sourceFontPopUp = vanilla.PopUpButton(
            (inputL, top, inputW, 20),
            [],
            callback=self.fontPopUpCallback
        )
        top += 30
        self.w.sourceGlyphTitle = vanilla.TextBox((titleL, top+2, titleW, 17), "Glyph:", alignment="right")
        self.w.sourceGlyphComboBox = vanilla.ComboBox(
            (inputL, top, inputW, 21),
            []
        )
        self._glyphNameComboBoxDataSource = PasteGlyphComboBoxDataSource.alloc().init()
        self.w.sourceGlyphComboBox.getNSComboBox().setUsesDataSource_(True)
        self.w.sourceGlyphComboBox.getNSComboBox().setDataSource_(self._glyphNameComboBoxDataSource)

        top += 30
        self.w.sourceLayersTitle = vanilla.TextBox((titleL, top+2, titleW, 17), "Layers:", alignment="right")
        self.w.sourceLayersList = vanilla.List(
            (inputL, top, inputW, 150),
            [],
            drawFocusRing=False,
            selectionCallback=self.sourceLayersListSelectionCallback,
            allowsEmptySelection=False
        )
        top += 160
        self.w.sourceContoursCheckBox = vanilla.CheckBox(
            (inputL, top, inputW, 22),
            "Paste Contours",
            value=True
        )
        top += 25
        self.w.sourceComponentsCheckBox = vanilla.CheckBox(
            (inputL, top, inputW, 22),
            "Paste Components"
        )
        top += 25
        self.w.sourceWidthCheckBox = vanilla.CheckBox(
            (inputL, top, inputW, 22),
            "Paste Width",
            value=len(self.currentGlyph.contours) + len(self.currentGlyph.components) == 0
        )
        top += 45

        self.w.destinationTitle = vanilla.TextBox((titleL, top, inputW, 17), "Destination")
        top += 25
        self.w.destinationLine = vanilla.HorizontalLine((titleL, top, inputW, 1))
        top += 15
        self.w.destinationLayerTitle = vanilla.TextBox((titleL, top+2, titleW, 17), "Layer:", alignment="right")
        self.w.destinationLayerPopUp = vanilla.PopUpButton(
            (inputL, top, inputW, 20),
            []
        )

        self.w.line = vanilla.HorizontalLine((15, -45, -15, 1))
        self.w.cancelButton = vanilla.Button((-245, -35, 70, 20), "Cancel", callback=self.cancelButtonCallback)
        self.w.applyButton = vanilla.Button((-165, -35, 70, 20), "Apply", callback=self.applyButtonCallback)
        self.w.okButton = vanilla.Button((-85, -35, 70, 20), "OK", callback=self.okButtonCallback)

        makeTextBold(self.w.sourceTitle)
        makeTextBold(self.w.destinationTitle)

        self.populateSourceFonts()
        self.populateDestinationLayer()

        self.w.setDefaultButton(self.w.okButton)
        self.w.cancelButton.bind(".", ["command"])
        self.w.getNSWindow().makeFirstResponder_(self.w.sourceGlyphComboBox.getNSComboBox())


        self.w.open()

    # ---------
    # Callbacks
    # ---------

    def okButtonCallback(self, sender):
        self.paste()
        self.w.close()

    def applyButtonCallback(self, sender):
        self.paste()

    def cancelButtonCallback(self, sender):
        self.w.close()

    def fontPopUpCallback(self, sender):
        index = sender.get()
        font = self.fonts[index]
        self.font = font
        self.populateSourceGlyphs()
        self.populateSourceLayers()

    def sourceLayersListSelectionCallback(self, sender):
        haveOneLayer = len(sender.getSelection()) == 1
        self.w.destinationLayerPopUp.enable(haveOneLayer)

    # -----------------
    # Populate Controls
    # -----------------

    def populateSourceFonts(self):
        self.fonts = self.getAllFonts()
        names = [font.uniqueName for font in self.fonts]
        self.w.sourceFontPopUp.setItems(names)
        self.fontPopUpCallback(self.w.sourceFontPopUp)

    def populateSourceGlyphs(self):
        names = list(self.font.glyphOrder)
        unordered = set()
        for layer in self.font.layers:
            for name in layer.keys():
                if name not in names:
                    unordered.add(name)
        names += sorted(unordered)
        selection = ""
        if self.font != self.currentGlyph.font:
            if self.currentGlyph.name in self.font.keys():
                selection = self.currentGlyph.name
        else:
            selection = self.currentGlyph.lib.get(lastPasteLibKey, selection)
        self._glyphNameComboBoxDataSource.setGlyphNames_(names)
        self.w.sourceGlyphComboBox.set(selection)

    def populateSourceLayers(self):
        layers = self.font.layerOrder
        self.w.sourceLayersList.set(layers)
        currentLayer = self.currentGlyph.layer.name
        if currentLayer in layers:
            selection = [layers.index(currentLayer)]
        else:
            selection = []
        self.w.sourceLayersList.setSelection(selection)

    def populateDestinationLayer(self):
        layers = self.currentGlyph.font.layerOrder
        self.w.destinationLayerPopUp.setItems(layers)
        currentLayer = self.currentGlyph.layer.name
        index = layers.index(currentLayer)
        self.w.destinationLayerPopUp.set(index)

    # -----
    # Paste
    # -----

    def _getPasteSettings(self):
        settings = dict(
            destinationLayerName=self.w.destinationLayerPopUp.getItems()[self.w.destinationLayerPopUp.get()],
            doContours=self.w.sourceContoursCheckBox.get(),
            doComponents=self.w.sourceComponentsCheckBox.get(),
            doWidth=self.w.sourceWidthCheckBox.get(),
            copyLayerNames=set()
        )
        for index in self.w.sourceLayersList.getSelection():
            layerName = self.w.sourceLayersList[index]
            settings["copyLayerNames"].add(layerName)
        return settings

    def paste(self):
        settings = self._getPasteSettings()
        # check/update history
        if self.history:
            if self.history[-1] == settings:
                return
        self.history.append(settings)
        # extract settings
        copyLayerNames = settings["copyLayerNames"]
        destinationLayerName = settings["destinationLayerName"]
        doContours = settings["doContours"]
        doComponents = settings["doComponents"]
        doWidth = settings["doWidth"]
        # gather source data
        sourceFont = self.font
        sourceGlyphName = self.w.sourceGlyphComboBox.get().strip()
        sourceLayers = {}
        for sourceLayer in sourceFont.layers:
            if sourceLayer.name not in copyLayerNames:
                continue
            if not sourceGlyphName:
                continue
            if sourceGlyphName not in sourceLayer:
                continue
            sourceLayers[sourceLayer.name] = sourceLayer[sourceGlyphName]
        # gather destination data
        destinationGlyph = self.currentGlyph
        destinationGlyphName = destinationGlyph.name
        destinationFont = destinationGlyph.font
        destinationLayers = {}
        for destinationLayer in destinationFont.layers:
            if destinationGlyphName in destinationLayer:
                destinationLayers[destinationLayer.name] = destinationLayer[destinationGlyphName]
        # pair layers
        pairs = []
        if len(sourceLayers) == 1:
            destinationGlyph = None
            for layerGlyph in self.currentGlyph.layers:
                if layerGlyph.name == destinationLayerName:
                    destinationGlyph = layerGlyph
                    break
            if destinationGlyph is None:
                destinationGlyph = self.currentGlyph.newLayer(destinationLayerName)
            sourceGlyph = list(sourceLayers.values())[0]
            pairs.append((sourceGlyph, destinationGlyph))
        else:
            for layerName, sourceGlyph in sourceLayers.items():
                if layerName not in destinationLayers:
                    destinationLayers[layerName] = destinationGlyph.newLayer(layerName)
                destinationGlyph = destinationLayers[layerName]
                pairs.append((sourceGlyph, destinationGlyph))
        # copy data
        for sourceGlyph, destinationGlyph in pairs:
            destinationGlyph.prepareUndo("Paste Glyph")
            if sourceGlyph.font == destinationGlyph.font:
                destinationGlyph.lib[lastPasteLibKey] = sourceGlyph.name
            selectContours = []
            if doContours:
                for contour in sourceGlyph:
                    contour = destinationGlyph.appendContour(contour)
                    selectContours.append(contour)
            selectComponents = []
            if doComponents:
                for component in sourceGlyph.components:
                    component = destinationGlyph.appendComponent(component=component)
                    selectComponents.append(component)
            if selectContours or selectComponents:
                destinationGlyph.selectedContours = selectContours
                destinationGlyph.selectedComponents = selectComponents
            if doWidth:
                destinationGlyph.width = sourceGlyph.width
            destinationGlyph.performUndo()


# ------------------
# Combo Box Delegate
# ------------------

if debug:
    from booster.debug import ClassNameIncrementer
else:
    ClassNameIncrementer = None

class PasteGlyphComboBoxDataSource(NSObject, metaclass=ClassNameIncrementer):

    def init(self):
        self = super(PasteGlyphComboBoxDataSource, self).init()
        self._glyphNames = []
        return self

    def setGlyphNames_(self, names):
        self._glyphNames = names

    def comboBox_completedString_(self, comboBox, text):
        if text in self._glyphNames:
            return text
        for name in self._glyphNames:
            if name.startswith(text):
                return name
        return text

    def comboBox_indexOfItemWithStringValue_(self, comboBox, text):
        return self._glyphNames.index(text)

    def comboBox_objectValueForItemAtIndex_(self, comboBox, index):
        return self._glyphNames[index]

    def numberOfItemsInComboBox_(self, comboBox):
        return len(self._glyphNames)


# -------
# Support
# -------

def makeTextBold(textBox):
    font = textBox.getNSTextField().font()
    font = NSFont.boldSystemFontOfSize_(font.pointSize())
    textBox.getNSTextField().setFont_(font)

def getGlyphEditorRectAndScreen(editorWindow):
    screen = editorWindow.w.getNSWindow().screen()
    nsWindow = editorWindow.w.getNSWindow()
    scrollView = editorWindow.getGlyphView().enclosingScrollView()
    rectInWindowCoords = scrollView.convertRect_toView_(scrollView.frame(), None)
    rectInScreenCoords = nsWindow.convertRectToScreen_(rectInWindowCoords)
    (screenX, screenY), (screenWidth, screenHeight) = screen.frame()
    (x, y), (w, h) = rectInScreenCoords
    y = -(y + h)
    return (x, y, w, h), screen


if __name__ == "__main__":
    glyph = CurrentGlyph()
    if glyph is not None:
        controller = PasteGlyphController()
        controller.start(glyph)
    else:
        NSBeep()
