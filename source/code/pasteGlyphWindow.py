from copy import deepcopy
import pprint
import AppKit
import ezui
from fontParts.world import (
    AllFonts,
    OpenFont,
    CurrentFont,
    CurrentGlyph
)

if __name__ == "__main__":
    from lib.tools.debugTools import ClassNameIncrementer
else:
    def ClassNameIncrementer(clsName, bases, dct):
        return type(clsName, bases, dct)


lastPasteNameLibKey = "com.typesupply.PasteGlyph.lastPastedGlyphName"
lastPasteSettingsLibKey = "com.typesupply.PasteGlyph.lastPastedGlyphSettings"
openFontItemName = "Open Font…"

xAlignmentOptions = {
    "Left Margin" : "leftMargin",
    "Right Margin" : "rightMargin",
    "Width Center" : "center",
    "Bounds Left" : "leftBounds",
    "Bounds Center" : "centerBounds",
    "Bounds Right" : "rightBounds",
    "Before" : "before",
    "After" : "after"
}
yAlignmentOptions = {
    "Baseline" : "baseline",
    "Descender" : "descender",
    "X-Height" : "xHeight",
    "Cap Height" : "capHeight",
    "Ascender" : "ascender",
    "Bounds Bottom" : "bottomBounds",
    "Bounds Center" : "centerBounds",
    "Bounds Top" : "topBounds",
    "Below" : "below",
    "Above" : "above"
}


class PasteGlyphWindowController(ezui.WindowController):

    # Setup
    # -----

    def build(self, glyphWindow):
        self.sourceFonts = {}
        for font in AllFonts(sortOptions="magic"):
            self.addSourceFont(font)
        self.sourceFont = None
        self.currentGlyph = CurrentGlyph()
        self.history = []

        content = """
        = TwoColumnForm

        !§ Source

        : Font:
        ( ...)                   @sourceFontNamePopUpButton

        : Glyph:
        [_ ...]                  @sourceGlyphNameComboBox

        : Layers:
        | Layer Name |           @sourceLayerNameTable

        !§ Destination

        : Layer:
        ( ...)                  @destinationLayerNamePopUpButton

        !§ Options

        : Paste:
        [X] Contours             @optionsPasteContoursCheckbox
        [ ] Components           @optionsPasteComponentsCheckbox
        [ ] Width                @optionsPasteWidthCheckbox

        : X Alignment:
        ( ...)                   @optionsXAlignmentPopUpButton

        : Y Alignment:
        ( ...)                   @optionsYAlignmentPopUpButton

        !§                       # XXX this is a hack just to put a line above the footer

        ====================

        (Cancel)                 @cancelButton
        (Apply)                  @applyButton
        (OK)                     @okButton
        """
        footerButtonWidth = 65
        descriptionData = dict(
            content=dict(
                titleColumnWidth=100,
                itemColumnWidth=275,
            ),
            sourceFontNamePopUpButton=dict(
                items=self.getSourceFontNames()
            ),
            sourceLayerNameTable=dict(
                height=100
            ),
            destinationLayerNamePopUpButton=dict(
                items=self.currentGlyph.font.layerOrder
            ),
            optionsXAlignmentPopUpButton=dict(
                items=list(xAlignmentOptions.keys())
            ),
            optionsYAlignmentPopUpButton=dict(
                items=list(yAlignmentOptions.keys())
            ),
            cancelButton=dict(
                keyEquivalent=".",
                keyEquivalentModifiers="command",
                width=footerButtonWidth
            ),
            applyButton=dict(
                width=footerButtonWidth
            ),
            okButton=dict(
                width=footerButtonWidth
            )
        )

        self.w = ezui.EZSheet(
            content=content,
            descriptionData=descriptionData,
            parent=glyphWindow.w,
            defaultButton="okButton",
            controller=self
        )

        self.sourceFontNamePopUpButton = self.w.getItem("sourceFontNamePopUpButton")
        self.sourceGlyphNameComboBox = self.w.getItem("sourceGlyphNameComboBox")
        self.sourceLayerNameTable = self.w.getItem("sourceLayerNameTable")
        self.destinationLayerNamePopUpButton = self.w.getItem("destinationLayerNamePopUpButton")
        self.optionsPasteContoursCheckbox = self.w.getItem("optionsPasteContoursCheckbox")
        self.optionsPasteComponentsCheckbox = self.w.getItem("optionsPasteComponentsCheckbox")
        self.optionsPasteWidthCheckbox = self.w.getItem("optionsPasteWidthCheckbox")
        self.optionsXAlignmentPopUpButton = self.w.getItem("optionsXAlignmentPopUpButton")
        self.optionsYAlignmentPopUpButton = self.w.getItem("optionsYAlignmentPopUpButton")

        self._sourceGlyphNameComboBoxDataSource = PasteGlyphComboBoxDataSource.alloc().init()
        self.sourceGlyphNameComboBox.getNSComboBox().setUsesDataSource_(True)
        self.sourceGlyphNameComboBox.getNSComboBox().setDataSource_(self._sourceGlyphNameComboBoxDataSource)

    def started(self):
        self.sourceFontNamePopUpButtonCallback(self.sourceFontNamePopUpButton)
        self.w.open()

    # Footer Buttons
    # --------------

    def cancelButtonCallback(self, sender):
        self.w.close()

    def applyButtonCallback(self, sender):
        self.paste()

    def okButtonCallback(self, sender):
        self.paste()
        self.w.close()

    # Item Population
    # ---------------

    def addSourceFont(self, font):
        names = self.sourceFonts.keys()
        family = font.info.familyName
        style = font.info.styleName
        if family is None:
            family = "Untitled Family"
        if style is None:
            style = "Untitled Style"
        name = "-".join((family, style))
        if name == "Untitled Family-Untitled Style":
            name = "Untitled Font"
        increment = 0
        while 1:
            if increment > 500:
                raise NotImplementedError("Do you really have 500 fonts with the same name open!?")
            if increment == 0:
                if name not in names:
                    break
                else:
                    increment = 1
            else:
                n = name + " " + repr(increment)
                if n not in names:
                    name = n
                    break
                else:
                    increment += 1
        self.sourceFonts[name] = font
        return name

    def getSourceFontNames(self):
        sourceFontNames = list(self.sourceFonts.keys()) + [
            AppKit.NSMenuItem.separatorItem(),
            openFontItemName
        ]
        return sourceFontNames

    def populateSourceGlyphs(self):
        names = list(self.sourceFont.glyphOrder)
        unordered = set()
        for layer in self.sourceFont.layers:
            for name in layer.keys():
                if name not in names:
                    unordered.add(name)
        names += sorted(unordered)
        settings = {}
        if self.sourceFont != self.currentGlyph.font:
            if self.currentGlyph.name in self.sourceFont.keys():
                selection = self.currentGlyph.name
        else:
            settings = self.currentGlyph.lib.get(lastPasteSettingsLibKey, settings)
            if not settings:
                settings["sourceGlyphName"] = self.currentGlyph.lib.get(lastPasteNameLibKey, None)
        self._sourceGlyphNameComboBoxDataSource.setGlyphNames_(names)
        self.populatePreviousSettings(settings)

    def populatePreviousSettings(self, settings):
        sourceGlyphName = settings.get("sourceGlyphName", None)
        sourceLayerNames = settings.get("sourceLayerNames", None)
        destinationLayerName = settings.get("destinationLayerName", None)
        pasteContours = settings.get("pasteContours", None)
        pasteComponents = settings.get("pasteComponents", None)
        pasteWidth = settings.get("pasteWidth", None)
        xAlignment = settings.get("xAlignment", None)
        yAlignment = settings.get("yAlignment", None)
        if sourceGlyphName is not None:
            self.sourceGlyphNameComboBox.set(sourceGlyphName)
        if sourceLayerNames is not None:
            existingNames = self.sourceLayerNameTable.get()
            sourceLayerNames = [n for n in sourceLayerNames if n in existingNames]
            self.sourceLayerNameTable.setSelectedItems(sourceLayerNames)
        if destinationLayerName is not None:
            existingNames = self.destinationLayerNamePopUpButton.getItems()
            if destinationLayerName in existingNames:
                index = existingNames.index(destinationLayerName)
                self.destinationLayerNamePopUpButton.set(index)
        if pasteContours is not None:
            self.optionsPasteContoursCheckbox.set(pasteContours)
        if pasteComponents is not None:
            self.optionsPasteComponentsCheckbox.set(pasteComponents)
        if pasteWidth is not None:
            self.optionsPasteWidthCheckbox.set(pasteWidth)
        if xAlignment is not None:
            index = 0
            for i, option in enumerate(xAlignmentOptions.values()):
                if option == xAlignment:
                    index = i
                    break
            self.optionsXAlignmentPopUpButton.set(index)
        if yAlignment is not None:
            index = 0
            for i, option in enumerate(yAlignmentOptions.values()):
                if option == yAlignment:
                    index = i
                    break
            self.optionsYAlignmentPopUpButton.set(index)

    def populateSourceLayers(self):
        layers = self.sourceFont.layerOrder
        layerTable = self.sourceLayerNameTable
        layerTable.set(layers)
        currentLayer = self.currentGlyph.layer.name
        if currentLayer in layers:
            selection = [layers.index(currentLayer)]
        else:
            selection = []
        layerTable.setSelectedIndexes(selection)

    # Item Callbacks
    # --------------

    def sourceFontNamePopUpButtonCallback(self, sender):
        index = sender.get()
        name = sender.getItems()[index]
        if name == openFontItemName:
            font = OpenFont(path=None, showInterface=False)
            if font is None:
                name = self.getSourceFontNames()[0]
            else:
                name = self.addSourceFont(font)
            names = self.getSourceFontNames()
            index = names.index(name)
            sender.setItems(names)
            sender.set(index)
        self.sourceFont = self.sourceFonts[name]
        self.populateSourceGlyphs()
        self.populateSourceLayers()

    def sourceLayerNameTableSelectionCallback(self, sender):
        haveOneLayer = len(sender.getSelectedIndexes()) == 1
        self.destinationLayerNamePopUpButton.enable(haveOneLayer)

    # The Point of Everything
    # -----------------------

    def paste(self):
        settings = self.getPasteSettings()
        # ignore repeats because they are most
        # likely accidental buttion presses
        if self.history:
            if self.history[-1] == settings:
                return
        self.history.append(settings)
        # extract settings
        sourceGlyphName = settings["sourceGlyphName"]
        sourceLayerNames = settings["sourceLayerNames"]
        destinationLayerName = settings["destinationLayerName"]
        pasteContours = settings["pasteContours"]
        pasteComponents = settings["pasteComponents"]
        pasteWidth = settings["pasteWidth"]
        xAlignment = settings["xAlignment"]
        yAlignment = settings["yAlignment"]
        # gather source data
        sourceFont = self.sourceFont
        sourceLayers = {}
        for sourceLayer in sourceFont.layers:
            if sourceLayer.name not in sourceLayerNames:
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
            # calculate x offset
            xOffset = 0
            if xAlignment == "leftMargin":
                pass
            elif xAlignment == "rightMargin":
                xOffset = destinationGlyph.width - sourceGlyph.width
            elif xAlignment == "center":
                xOffset = (destinationGlyph.width - sourceGlyph.width) / 2
            elif xAlignment == "leftBounds":
                if sourceGlyph.bounds and destinationGlyph.bounds:
                    xOffset = destinationGlyph.bounds[0] - sourceGlyph.bounds[0]
            elif xAlignment == "centerBounds":
                if sourceGlyph.bounds and destinationGlyph.bounds:
                    dW = destinationGlyph.bounds[2] - destinationGlyph.bounds[0]
                    sW = sourceGlyph.bounds[2] - sourceGlyph.bounds[0]
                    xOffset = (dW - sW) / 2
            elif xAlignment == "rightBounds":
                if sourceGlyph.bounds and destinationGlyph.bounds:
                    xOffset = destinationGlyph.bounds[2] - sourceGlyph.bounds[2]
            elif xAlignment == "before":
                xOffset = -sourceGlyph.width
            elif xAlignment == "after":
                xOffset = destinationGlyph.width
            # calculate the y offset
            yOffset = 0
            sourceFont = sourceGlyph.font
            destinationFont = destinationGlyph.font
            if yAlignment == "baseline":
                pass
            elif yAlignment == "descender":
                yOffset = destinationFont.info.descender - sourceFont.info.descender
            elif yAlignment == "xHeight":
                yOffset = destinationFont.info.xHeight - sourceFont.info.xHeight
            elif yAlignment == "capHeight":
                yOffset = destinationFont.info.capHeight - sourceFont.info.capHeight
            elif yAlignment == "ascender":
                yOffset = destinationFont.info.ascender - sourceFont.info.ascender
            elif yAlignment == "bottomBounds":
                if sourceGlyph.bounds and destinationGlyph.bounds:
                    yOffset = destinationGlyph.bounds[1] - sourceGlyph.bounds[1]
            elif yAlignment == "centerBounds":
                if sourceGlyph.bounds and destinationGlyph.bounds:
                    dH = destinationGlyph.bounds[3] - destinationGlyph.bounds[1]
                    sH = sourceGlyph.bounds[3] - sourceGlyph.bounds[1]
                    yOffset = (dH - sH) / 2
            elif yAlignment == "topBounds":
                if sourceGlyph.bounds and destinationGlyph.bounds:
                    yOffset = destinationGlyph.bounds[3] - sourceGlyph.bounds[3]
            elif yAlignment == "below":
                yOffset = -sourceFont.info.ascender
            elif yAlignment == "above":
                yOffset = destinationFont.info.ascender
            # start the undo step
            destinationGlyph.prepareUndo("Paste Glyph")
            # store for future reference
            if sourceGlyph.font == destinationGlyph.font:
                destinationGlyph.lib[lastPasteNameLibKey] = sourceGlyph.name
                destinationGlyph.lib[lastPasteSettingsLibKey] = deepcopy(settings)
            # do the paste
            selectContours = []
            if pasteContours:
                for contour in sourceGlyph:
                    contour = destinationGlyph.appendContour(contour, offset=(xOffset, yOffset))
                    selectContours.append(contour)
            selectComponents = []
            if pasteComponents:
                for component in sourceGlyph.components:
                    xO, yO = component.offset
                    xO += xOffset
                    yO += yOffset
                    component = destinationGlyph.appendComponent(component=component, offset=(xO, yO))
                    selectComponents.append(component)
            if pasteWidth:
                destinationGlyph.width = sourceGlyph.width
            # select the newly pasted data
            if selectContours or selectComponents:
                destinationGlyph.selectedContours = selectContours
                destinationGlyph.selectedComponents = selectComponents
            # end the undo step
            destinationGlyph.performUndo()

    def getPasteSettings(self):
        sourceGlyphName = self.sourceGlyphNameComboBox.get()
        sourceLayerNames = self.sourceLayerNameTable.getSelectedItems()
        destinationLayerName = self.destinationLayerNamePopUpButton.getItems()[self.destinationLayerNamePopUpButton.get()]
        pasteContours = self.optionsPasteContoursCheckbox.get()
        pasteComponents = self.optionsPasteComponentsCheckbox.get()
        pasteWidth = self.optionsPasteWidthCheckbox.get()
        xAlignment = self.optionsXAlignmentPopUpButton.getItems()[self.optionsXAlignmentPopUpButton.get()]
        xAlignment = xAlignmentOptions[xAlignment]
        yAlignment = self.optionsYAlignmentPopUpButton.getItems()[self.optionsYAlignmentPopUpButton.get()]
        yAlignment = yAlignmentOptions[yAlignment]
        settings = dict(
            sourceGlyphName=sourceGlyphName,
            sourceLayerNames=sourceLayerNames,
            destinationLayerName=destinationLayerName,
            pasteContours=pasteContours,
            pasteComponents=pasteComponents,
            pasteWidth=pasteWidth,
            xAlignment=xAlignment,
            yAlignment=yAlignment,
        )
        return settings


class PasteGlyphComboBoxDataSource(AppKit.NSObject, metaclass=ClassNameIncrementer):

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
        if text not in self._glyphNames:
            return -1
        return self._glyphNames.index(text)

    def comboBox_objectValueForItemAtIndex_(self, comboBox, index):
        return self._glyphNames[index]

    def numberOfItemsInComboBox_(self, comboBox):
        return len(self._glyphNames)


if __name__ == "__main__":
    from mojo.UI import CurrentGlyphWindow
    glyphWindow = CurrentGlyphWindow()
    PasteGlyphWindowController(glyphWindow)