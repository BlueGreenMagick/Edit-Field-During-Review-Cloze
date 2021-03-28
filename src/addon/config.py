
from enum import Enum
import re
from typing import List, TypedDict, Set

from anki.models import Template, NoteType
from aqt import mw
from aqt.qt import Qt, QComboBox, QListWidget, QListWidgetItem

from .configmanager import ConfigManager, ConfigWindow

conf = ConfigManager()


def general_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.add_tab("General")
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
    tab = conf_window.add_tab("Formatting")
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


class TemplateField(TypedDict):
    name: str
    edit: bool


class Editability(Enum):
    NONE = 0
    PARTIAL = 1
    ALL = 2

    @classmethod
    def from_check_state(cls, check_state: Qt.CheckState) -> "Editability":
        if check_state == Qt.Unchecked:
            return cls.NONE
        if check_state == Qt.Checked:
            return cls.ALL
        return cls.PARTIAL

    @classmethod
    def to_check_state(cls, val: "Editability") -> Qt.CheckState:
        if val == cls.NONE:
            return Qt.Unchecked
        if val == cls.ALL:
            return Qt.Checked
        return Qt.PartiallyChecked


class FieldIsEditable(TypedDict):
    name: str
    orig_edit: Editability
    edit: Editability


class NoteTypeFields(TypedDict):
    name: str
    fields: List[FieldIsEditable]


def replace_field(note_type: NoteType, field: FieldIsEditable) -> NoteType:
    for template in note_type["tmpls"]:
        for side in ["qfmt", "afmt"]:
            if field["edit"] == Editability.ALL:
                template[side] = re.sub("{{((?:(?!edit:)[^#/:}]+:)*%s)}}" %
                                        field["name"], r"{{edit:\1}}", template[side])
            elif field["edit"] == Editability.NONE:
                template[side] = re.sub(
                    "{{((?:[^#/:}]+:)*)edit:((?:[^#/:}]+:)*%s)}}" % field["name"], r"{{\1\2}}", template[side])
    return note_type


def parse_fields(template: str) -> List[TemplateField]:
    matches = re.findall("{{[^#/}]+?}}", template)  # type: ignore
    fields = []
    for m in matches:
        # strip off mustache
        m = re.sub(r"[{}]", "", m)
        # strip off modifiers
        splitted = m.split(":")
        modifiers = splitted[:-1]
        field_name = splitted[-1]
        has_edit = ("edit" in modifiers)
        field_info = TemplateField(name=field_name, edit=has_edit)
        fields.append(field_info)
    return fields


def get_fields_in_every_notetype(fields_in_note_type: List[NoteTypeFields]) -> None:
    for i in fields_in_note_type:
        fields_in_note_type.pop()

    models = mw.col.models
    note_types = models.all()
    for note_type in note_types:
        templates: List[Template] = note_type["tmpls"]
        editable_field_names: Set[str] = set()
        uneditable_field_names: Set[str] = set()

        for template in templates:
            for side in ["qfmt", "afmt"]:
                for tmpl_field in parse_fields(template[side]):  # type: ignore
                    name = tmpl_field["name"]
                    if tmpl_field["edit"]:
                        editable_field_names.update([name])
                    else:
                        uneditable_field_names.update([name])

        field_names = [fld["name"] for fld in note_type["flds"]]
        fields_list = []
        for fldname in field_names:
            try:
                # if (False, False), skip since the field isn't used in any of the templates.
                editable = {
                    (True, True): Editability.PARTIAL,
                    (True, False): Editability.ALL,
                    (False, True): Editability.NONE
                }[(fldname in editable_field_names, fldname in uneditable_field_names)]

                field = FieldIsEditable(
                    name=fldname, edit=editable, orig_edit=editable)
                fields_list.append(field)
            except:
                pass
        nt = NoteTypeFields(name=note_type["name"], fields=fields_list)
        fields_in_note_type.append(nt)


def fields_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.add_tab("Fields")
    layout = tab.vlayout()
    dropdown = QComboBox()
    layout.addWidget(dropdown)
    layout.space(20)
    layout.label("Check the boxes to make the fields editable while reviewing")
    qlist = QListWidget()
    qlist.setStyleSheet("QListWidget{border: 1px solid; padding: 6px;}")
    layout.addWidget(qlist)

    fields_in_note_type: List[NoteTypeFields] = []

    def on_check(item: QListWidgetItem) -> None:
        fields = fields_in_note_type[dropdown.currentIndex()]["fields"]
        field = fields[qlist.row(item)]
        field["edit"] = Editability.from_check_state(item.checkState())

    qlist.itemChanged.connect(lambda item: on_check(item))

    def switch_template(idx: int) -> None:
        if idx == -1:
            return
        qlist.clear()
        fields = fields_in_note_type[idx]["fields"]
        for field in fields:
            item = QListWidgetItem(field["name"], qlist, QListWidgetItem.Type)
            qlist.addItem(item)
            item.setCheckState(Editability.to_check_state(field["edit"]))

    dropdown.currentIndexChanged.connect(switch_template)

    get_fields_in_every_notetype(fields_in_note_type)
    for nt in fields_in_note_type:
        dropdown.addItem(nt["name"])
    dropdown.setCurrentIndex(0)  # Triggers currentIndexChanged

    def on_save() -> None:
        for note_type_fields in fields_in_note_type:
            modified = False
            note_type = mw.col.models.byName(note_type_fields["name"])
            for field in note_type_fields["fields"]:
                if field["edit"] != field["orig_edit"]:
                    modified = True
                    note_type = replace_field(note_type, field)
            if modified:
                mw.col.models.save(note_type)

    conf_window.execute_on_save(on_save)


conf.use_custom_window()
conf.add_config_tab(general_tab)
conf.add_config_tab(formatting_tab)
conf.add_config_tab(fields_tab)
