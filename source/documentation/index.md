# Paste Glyph

Paste some data from a glyph into the current glyph.

## Source

- **Font:** Pick the font you want to copy from. If you want to paste from a font that isn't open, select "Open Font…" and choose the font you want.
- **Glyph:** Enter the name of the glyph you want to copy from.
- **Layers:** Select the layer, or layers, that you want to copy from.

## Destination

**Layer:** Select the layer you want to paste to. If you are copying more than one layer, this will be disabled and the layers to paste to will have the same names as the layers being copied from.

## Options

- **Paste:** You can copy the contours, components and/or width from the source.
- **X Alignment:** Choose where you want the pasted glyph to align horizontally.
- **Y Alignment:** Choose where you want the pasted glyph to align vertically.

## Buttons

- **OK:** Paste with the current settings and close the window.
- **Apply:** Paste with the current settings and leave the window open so you can paste something else.
- **Cancel:** Close the window without pasting with the current settings. If you've used the *Apply* button, this will not undo those pastes. If you need to undo, use the standard *Undo* menu/key command.

*Note:* In *OK* and *Apply*, if you try to paste using the same settings twice in a row, the second time will be ignored. This prevents double pasting.

## Heuristics

Setting all of these buttons for a quick paste is fiddly, so the extension tries to apply some basic heuristics to set up the defaults for each paste. So, if you are wondering, "Why does it not always have the same settings when it first opens?" This is why.