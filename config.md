## Config Options

- ctrl_click: If set to `true`, to edit field, press ctrl while clicking. Default: `false`.

- process_paste: When pasting, save images locally, strip unnecessary html formatting, etc. Experimental and officially only support 2.1.19. Turn if off if you encounter errors regarding `editorwv` on paste.  Default: `true`.

- remove_span: When editing on reviewer, will remove all span tags. If you rely on span tags, do not set this to true or they will all be deleted. Most users who don't need span tags are recommended to set it to `true`. Default: `false`.

- special_formatting: Shortcuts for special formattings. Possible choices are written below, and its corresponding shortcuts. In the square bracket, write each wrapped in double quotes and square brackets, and put a comma between each choices. (After closing with quotes, before opening quote) Default: `[["removeformat"], ["fontcolor", "#00f"], ["strikethrough"]]`



- tag: Which html tag to use for editable field. Default: `div`.

- undo: Whether the last field edit should be undo-able. Default: `true`.


#### Special Formatting options

The below are additional formatting options you can add to the addon. Italic(Ctrl+I), Bold(Ctrl+B), Underline(Ctrl+U) is implemented by default.

- `"removeformat"`: Ctrl + R
- `"strikethrough"`: Shift + Alt + 5
- `"fontcolor"`: F7
Note that this requires a hex color code as the second value in the array.
- `"highlight"`: Ctrl + Shift + B
Note that this requires a hex color code as the second value in the array. Also, to use highlights, you have to set `remove_span` config to `false`. Example: `"#00f"`.
- `"subscript"`: Ctrl + =
- `"superscript"`: Ctrl + Shift + =
- `"formatpre"`: Ctrl + .
Note that this requires a html tag as the second value in the array. Example: `"pre"`.
- `"hyperlink"`: Ctrl + Shift + H
- `"unhyperlink"`: Ctrl + Shift + Alt + H
- `"unorderedlist"`: Ctrl + [
- `"orderedlist"`: Ctrl + ]
- `"indent"`: Ctrl + Shift + ]
- `"outdent"`: Ctrl + Shift + [
- `"justifyCenter"`: Ctrl + Shift + Alt + S
- `"justifyLeft"`: Ctrl + Shift + Alt + L
- `"justifyRight"`: Ctrl + Shift + Alt + R
- `"justifyFull"`: Ctrl + Shift + Alt + B