- ctrl_click: If set to `true`, to edit field, press ctrl while clicking. Default: `false`.

- process_paste: When pasting, save images locally, strip unnecessary html formatting, etc. Experimental and officially only support 2.1.19. Turn if off if you encounter errors regarding `editorwv` on paste.  Default: `true`.

- remove_span: When editing on reviewer, will remove all span tags. If you rely on span tags, do not set this to true or they will all be deleted. Most users who don't need span tags are recommended to set it to `true`. Default: `false`.

- tag: Which html tag to use for editable field. Default: `div`.

- undo: Whether the last field edit should be undo-able. Default: `true`.