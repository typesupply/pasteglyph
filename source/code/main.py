from AppKit import NSApp
from pasteGlyph.controller import _PasteGlyphController

if __name__ == "__main__":
    NSApp().PasteGlyphController = _PasteGlyphController()
