## Config Options

- ctrl_click: If set to `true`, to edit field, press ctrl while clicking. Default: `false`.

- outline: If set to `true`, add a blue outline around the field when it is in edit mode. Default, `true`.

- process_paste: When pasting, save images locally, strip unnecessary html formatting, etc. Experimental and officially only support 2.1.19. Turn if off if you encounter errors regarding `editorwv` on paste.  Default: `true`.

- remove_span: When editing on reviewer, will remove all span tags. If you rely on span tags, do not set this to true or they will all be deleted. Most users who don't need span tags are recommended to set it to `true`. Default: `false`.

- tag: Which html tag to use for editable field. Default: `div`.

- undo: Whether the last field edit should be undo-able. Default: `true`.

- z_special_formatting: Shortcuts for special formattings. Possible choices are written below, and its corresponding shortcuts. Set `false` to `true` to enable each, and `true` to `false` to disable.



#### Special Formatting options

The below are additional formatting options you can add to the addon. Italic(Ctrl+I), Bold(Ctrl+B), Underline(Ctrl+U) is implemented by default. `fontcolor`, `removeformat`, `strikethrough` is set to `true` by default.

- `"fontcolor"`: F7
Note that this requires a hex color code as the second value in the array.
- `"formatpre"`: Ctrl + .
Note that this requires a html tag as the second value in the array. Example: `"pre"`.
- `"highlight"`: Ctrl + Shift + B
Note that this requires a hex color code as the second value in the array. Also, to use highlights, you have to set `remove_span` config to `false`. Example: `"#00f"`.
- `"hyperlink"`: Ctrl + Shift + H
- `"indent"`: Ctrl + Shift + ]
- `"justifyCenter"`: Ctrl + Shift + Alt + S
- `"justifyFull"`: Ctrl + Shift + Alt + B
- `"justifyLeft"`: Ctrl + Shift + Alt + L
- `"justifyRight"`: Ctrl + Shift + Alt + R
- `"orderedlist"`: Ctrl + ]
- `"outdent"`: Ctrl + Shift + [
- `"removeformat"`: Ctrl + R
- `"strikethrough"`: Shift + Alt + 5
- `"subscript"`: Ctrl + =
- `"superscript"`: Ctrl + Shift + =
- `"unhyperlink"`: Ctrl + Shift + Alt + H
- `"unorderedlist"`: Ctrl + [


