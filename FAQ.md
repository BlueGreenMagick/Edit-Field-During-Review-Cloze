## I can't edit the cards while reviewing!

Please check if you enabled editing your field in the note type. Go to the addon config, select the `Fields` tab. Choose your note type from the dropdown and see if the fields are editable.

Alternatively, you can control each fields editability by editing the notetype card template. Add or remove `edit:` from the field name. For example, `{{edit:Front}}`, `{{edit:cloze:Text}}`.

## What do I put in as keyboard shortcut?

Each shortcut can have `"Ctrl"`, `"Shift"`, `"Alt"`, and one other key. They are combined using `+`.

Examples: `"K"`, `"Ctrl+C"`, `"Alt+Shift+,"`, `"Ctrl+Alt+F1`

If you are using Macs, use press `Cmd` key for `"Ctrl"`, and `Opt` key for `"Alt"`.

## Can I have multiple formatting shortcuts?

It is possible to have multiple formatting shortcut entries. You can do this to have multiple `fontcolor`, `formatblock`, or `highlight` shortcuts with different colors, or if you want multiple keyboard shortcuts.

You will need to go to the Advanced config editor. In `special_formatting`, copy paste the entry you want to duplicate, which looks like below.

```json
"fontcolor": {
    "arg": {
        "type": "color",
        "value": "#00f"
    },
    "command": "foreColor",
    "enabled": true,
    "shortcut": "F7"
},
```

Edit the entry name (`fontcolor`) to any unique name, then exit. If you exit the addon config and reopen it, your new entry should be there in the list of formatting shortcuts.

Before editing in the Advanced config editor, you should save the existing config in another place, so if you modify the config incorrectly, you will be able to restore your previous config.

When deleting the newly added entry from advanced config editor, you'll see an error after saving. You can ignore the error and click "Quit Config".

## How do I apply styles to editable field html?

You can use the css selector `div[data-efdrcfield]` (or `span[data-efdrcfield]` depending on your config)

## How do I align fields next to each other? (Instead of field going to a new line)

For now, please put the following line into note type template styling:

```css
div[data-efdrcfield] {
  display: inline-block;
}
```

## How to add a custom shortcut action

You can customize the note type to add a custom shortcut action during edit. You will need to know JavaScript. 

Add the following code to your note type. The handler will only be triggered when you press the shortcut while editing.
Any edits to elem.innerHTML is saved to note field when 'blur' event is triggered on elem.

```javascript
EFDRC.registerShortcut("Ctrl+Shift+Alt+R", (event, elem) => {
  // event: KeyEvent, elem: contenteditable field element that is being edited
  // Write code to do whatever you want.
}
```

## How to edit conditionally hidden field?

When you use conitional replacement in Anki notetype template to hide fields when empty,
you need to modify your note type to be able to edit it during review.

If you want to hide `{{Field}}` if it is empty, write the below code in your notetype:

```html
<div class="{{^Field}}hidden{{/Field}}">
  {{Field}}
</div>
```

Then add the following code into the Styling of the note type:

```css
.hidden {
  display: none;
}

[data-efdrc-ctrl] .hidden,
[data-efdrc-editing] .hidden {
  display: block;
}
```

This works because the add-on adds `data-efdrc-ctrl` attribute to card container div while ctrl is pressed,
and `data-efdrc-editing` while you are editing a field.
