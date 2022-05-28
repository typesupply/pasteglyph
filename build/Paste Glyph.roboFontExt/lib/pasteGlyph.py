from fontParts.world import CurrentGlyph
from mojo.UI import CurrentGlyphWindow
from pasteGlyphWindow import PasteGlyphWindowController

glyph = CurrentGlyph
glyphWindow = CurrentGlyphWindow()

if glyphWindow is not None and glyph is not None:
    PasteGlyphWindowController(glyphWindow)