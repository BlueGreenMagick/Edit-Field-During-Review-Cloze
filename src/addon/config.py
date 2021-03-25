
from enum import Enum
import re
from typing import Tuple, List, Dict, TypedDict, Union, Optional

from anki.models import NoteType, Template
from aqt import mw
from aqt.qt import Qt, QCheckBox, QComboBox, QListWidget, QListWidgetItem, QWidget

from .configmanager import ConfigManager, ConfigWindow, ConfigLayout

conf = ConfigManager()


def general_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.addTab("General")
    layout = tab.vlayout()

    layout.checkbox(
        "ctrl_click", "Ctrl + Click to edit field (Cmd on mac)"
    ).setToolTip("If not checked, there is no need to press Ctrl")
    layout.checkbox(
        "outline", "Show a blue outline around the field when editing"
    )
    layout.checkbox(
        "process_paste", "Process pasted content for images and HTML"
    )
    layout.checkbox("undo", "Enable undo")

    tag_hlayout = layout.hlayout()
    tag_hlayout.label("HTML tag to use for editable field:")
    tag_options = ["div", "span"]
    tag_hlayout.dropdown(
        "tag", tag_options, tag_options
    ).setToolTip("Use span if you want an inline field")
    tag_hlayout.stretch()
    layout.stretch()

    layout.label("Image Resizing", bold=True)
    layout.checkbox("resize_image_default_state",
                    "Default state for image resizing.\nYPress Alt + S to toggle state. (Opt + S on Mac)")
    resize_hlayout = layout.hlayout()
    resize_hlayout.label("Image resizing mode:")
    option_labels = [
        "Don't preserve ratio",
        "Preserve ratio when using corner",
        "Always preserve ratio"
    ]
    option_values = [0, 1, 2]
    resize_hlayout.dropdown(
        "resize_image_preserve_ratio", option_labels, option_values
    )
    resize_hlayout.stretch()

    layout.stretch()


def formatting_tab(conf_window: ConfigWindow) -> None:
    conf = conf_window.conf
    tab = conf_window.addTab("Formatting")
    layout = tab.vlayout()
    layout.setContentsMargins(25, 25, 25, 25)
    scroll_layout = layout.scroll_layout(horizontal=False)
    for formatting in conf["special_formatting"]:
        hlayout = scroll_layout.hlayout()
        item_key = f"special_formatting.{formatting}"
        hlayout.checkbox(f"{item_key}.enabled")
        label_width = conf_window.fontMetrics().width("A" * 15)
        hlayout.label(formatting).setFixedWidth(label_width)
        hlayout.text_input(f"{item_key}.shortcut").setFixedWidth(label_width)
        if conf[f"{item_key}.arg"] is not None:
            if conf[f"{item_key}.arg.type"] == "color":
                hlayout.color_input(f"{item_key}.arg.value")
            else:
                hlayout.text_input(f"{item_key}.arg.value").setFixedWidth(60)
        hlayout.stretch(1)

    layout.stretch(1)


class FieldInfo(TypedDict):
    name: str
    edit: bool
    modifiers: List[str]


def parse_fields(template: str) -> List[FieldInfo]:
    matches = re.findall("{{[^#/}]+?}}", template)  # type: ignore
    fields = []
    for m in matches:
        # strip off mustache
        m = re.sub(r"[{}]", "", m)
        # strip off modifiers
        splitted = m.split(":")
        modifiers = splitted[:-1]
        field_name = splitted[-1]
        has_edit = False
        try:
            modifiers.remove("edit")
            has_edit = True
        except:
            pass
        field_info = FieldInfo(
            name=field_name, edit=has_edit, modifiers=modifiers
        )
        fields.append(field_info)
    return fields


def toggle_edit_mod(note_type: NoteType, front: bool, index: int, checked: bool) -> None:
    "Insert or remove edit: modifier in note type template"
    pass


def populate_field_info(qlist: QListWidget, note_type: NoteType, fields: List[FieldInfo]) -> None:
    qlist.clear()
    for i, field in enumerate(fields):
        field_label = field["name"]
        for mod in field["modifiers"]:
            field_label += f" ({mod})"
        # {{edit:FrontSide}} is ignored
        if field["name"] == "FrontSide":
            item = QListWidgetItem(field_label, qlist, 0)
            qlist.addItem(item)
            continue
        item = QListWidgetItem(field_label, qlist, 0)
        item.setCheckState(Qt.Checked if field["edit"] else Qt.Unchecked)


class FieldsListWidgetContent(TypedDict):
    front_widget: Optional[QWidget]
    back_widget: Optional[QWidget]
    front_inner: Optional[ConfigLayout]
    back_inner: Optional[ConfigLayout]


def fields_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.addTab("Fields")
    layout = tab.vlayout()
    dropdown = QComboBox()
    layout.addWidget(dropdown)
    layout.space(20)
    hlayout = layout.hlayout()
    layout.space(20)
    list_stylesheet = "QListWidget{border: 1px solid; padding: 6px;}"
    front_list = QListWidget()
    front_list.setStyleSheet(list_stylesheet)
    back_list = QListWidget()
    back_list.setStyleSheet(list_stylesheet)
    hlayout.addWidget(front_list)
    hlayout.addWidget(back_list)

    def switch_template(idx: int) -> None:
        if idx == -1:
            return
        note_type, template = dropdown.itemData(idx, Qt.UserRole)
        qfields = parse_fields(template["qfmt"])
        populate_field_info(front_list, note_type, qfields)
        afields = parse_fields(template["afmt"])
        populate_field_info(back_list, note_type, afields)

    dropdown.currentIndexChanged.connect(switch_template)

    def on_open() -> None:
        dropdown.clear()

        models = mw.col.models
        note_types = models.all()
        for note_type in note_types:
            templates = note_type["tmpls"]
            for template in templates:
                label = "{}: {}".format(note_type["name"], template["name"])
                dropdown.addItem(label, (note_type, template))

        dropdown.setCurrentIndex(0)  # Triggers currentIndexChanged

    conf_window.widget_on_open.append(on_open)


conf_window = conf.enable_config_window()
general_tab(conf_window)
formatting_tab(conf_window)
fields_tab(conf_window)
