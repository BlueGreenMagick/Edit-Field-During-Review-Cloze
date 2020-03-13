## Config Options

- ctrl_click: If set to `true`, ctrl+click on a field to edit. Default: `false`.

- outline: If set to `true`, add a blue outline around the field when it is in edit mode. Default, `true`.

- process_paste: When pasting, save images locally, strip unnecessary HTML formatting, etc. Experimental and officially only support 2.1.19. Set it to `false` if you encounter errors regarding `editorwv` on paste.  Default: `true`.

- remove_span: When editing on reviewer, will remove all span tags. If you rely on span tags, do not set this to true or they will all be deleted. Most users who don't need span tags are recommended to set it to `true`. Default: `false`.

- tag: Which HTML tag to use for editable field. Default: `div`.

- undo: Whether the last field edit should be undo-able. Default: `true`.

- z_special_formatting: Shortcuts for special formattings. Possible choices are written below, and its corresponding shortcuts. Set `false` to `true` to enable each, and `true` to `false` to disable.

- min-width, win-height: minimal width and height of images. It ensures that images can't be resized so smally that they can't be seen anymore

- resizable-style: css style to apply to images to show that they are resizable. In particular, it allows showing their border.

- preserve_ratio: It value can be: "current" (preserve the current ration. If image was resized, it will keep the new ratio), "original" (if image was resized, it'll take back original ratio). With any other value it'll resize freely.


#### Special Formatting options

Below are additional formatting options. Italic(Ctrl+I), Bold(Ctrl+B), Underline(Ctrl+U) is implemented by default. `fontcolor`, `removeformat`, `strikethrough` is set to `true` by default.

- `"fontcolor"`: F7
Note that this requires either a hex code or a rgb value as the second value in the array.
- `"formatblock"`: Ctrl + .
Note that this requires a html tag as the second value in the array. Example: `"pre"`. Note that 'pre' doesn't get removed by 'removeformat'.
- `"highlight"`: Ctrl + Shift + B
Note that this requires either a hex code or a rgb value as the second value in the array. Also, to use highlights, you have to set `remove_span` config to `false`. Example: `"#00f"`.
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


