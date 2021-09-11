## I can't edit the cards while reviewing!
Please check if you enabled editing your field in the note type. Go to the addon config, select the `Fields` tab. Choose your note type from the dropdown and see if the fields are editable.

Alternatively, you can control each fields editability by editing the notetype card template. Add or remove `edit:` from the field name. For example, `{{edit:Front}}`, `{{edit:cloze:Text}}`.


## What do I put in as keyboard shortcut?

Each shortcut can have `"Ctrl"`, `"Shift"`, `"Alt"`, and one other key. They are combined using `+`. Whitespaces and letter case is ignored when parsing the shortcut. 

The 'one other key' can be one of the alphanumeric keys, or a value in <a href="https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/code/code_values">this list</a>. If you want to use a special key, use its name for the shortcut. (ex. `Comma`, `BracketLeft`, `F1`)

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

Before editing in the Advanced config editor, you should probably save the existing config in another place. If you modify the config incorrectly, you will be able to restore your previous config.

## How do I apply styles to editable field html?
You can use the css selector `div[data-efdrcfield]` (or `span[data-efdrcfield]` depending on your config)

## How do I align fields next to each other? (Instead of field going to a new line)
For now, please put the following line into note type template styling:
```css
div[data-efdrcfield] {
    display: inline-block;
}
```
