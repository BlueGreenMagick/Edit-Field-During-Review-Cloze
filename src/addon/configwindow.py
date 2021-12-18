import re
from enum import Enum
from typing import List, TypedDict, Set, TYPE_CHECKING

from anki.models import NoteType
from aqt import mw
from aqt.qt import *

from .ankiaddonconfig import ConfigManager, ConfigWindow

conf = ConfigManager()


def general_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.add_tab("General")
    tab.checkbox(
        "ctrl_click",
        "Ctrl + Click to edit field (Cmd on mac)",
        tooltip="If not checked, there is no need to press Ctrl",
    )
    tab.checkbox("outline", "Show a blue outline around the field when editing")
    tab.checkbox("process_paste", "Process pasted content for images and HTML")
    tag_options = ["div", "span"]
    tab.dropdown(
        "tag",
        tag_options,
        tag_options,
        "HTML tag to use for editable field:",
        tooltip="div is recommended",
    )
    tab.text_input(
        "shortcuts.cloze-alt",
        "Shortcut for same number cloze:",
        tooltip="Default is Ctrl+Shift+Alt+C",
    )

    tab.space(20)
    tab.text("Image Resizing", bold=True)
    tab.checkbox(
        "resize_image_default_state",
        "Use image resizing",
        tooltip="Even when unchecked, you can toggle the 'image resize mode' with below shortcut",
    )
    option_labels = [
        "Don't preserve ratio",
        "Preserve ratio when using corner",
        "Always preserve ratio",
    ]
    option_values = [0, 1, 2]
    tab.dropdown(
        "resize_image_preserve_ratio",
        option_labels,
        option_values,
        "Image resizing mode:",
    )
    tab.text_input(
        "shortcuts.image-resize",
        "Shortcut for image resize mode:",
        tooltip="Pressing this shortcut toggles the image resize mode",
    )
    tab.stretch()


def formatting_tab(conf_window: ConfigWindow) -> None:
    conf = conf_window.conf
    tab = conf_window.add_tab("Formatting")
    tab.setContentsMargins(25, 25, 25, 25)
    scroll_layout = tab.scroll_layout(horizontal=False)
    for formatting in conf["special_formatting"]:
        hlayout = scroll_layout.hlayout()
        item_key = f"special_formatting.{formatting}"
        hlayout.checkbox(f"{item_key}.enabled")
        hlayout.text(formatting).setFixedWidth(120)
        hlayout.text_input(f"{item_key}.shortcut").setFixedWidth(160)
        if conf[f"{item_key}.arg"] is not None:
            if conf[f"{item_key}.arg.type"] == "color":
                hlayout.color_input(f"{item_key}.arg.value")
            else:
                hlayout.text_input(f"{item_key}.arg.value").setFixedWidth(60)
        hlayout.stretch()
    tab.stretch()


class TemplateField(TypedDict):
    name: str
    edit: bool


class Editability(Enum):
    NONE = 0
    PARTIAL = 1
    ALL = 2

    @classmethod
    def from_check_state(cls, check_state: Qt.CheckState) -> "Editability":
        if check_state == Qt.CheckState.Unchecked:
            return cls.NONE
        if check_state == Qt.CheckState.Checked:
            return cls.ALL
        return cls.PARTIAL

    @classmethod
    def to_check_state(cls, val: "Editability") -> Qt.CheckState:
        if val == cls.NONE:
            return Qt.CheckState.Unchecked
        if val == cls.ALL:
            return Qt.CheckState.Checked
        return Qt.CheckState.PartiallyChecked


class FieldIsEditable(TypedDict):
    name: str
    orig_edit: Editability
    edit: Editability


class NoteTypeFields(TypedDict):
    name: str
    fields: List[FieldIsEditable]


def modify_field_editability(
    note_type: "NoteType", field: FieldIsEditable
) -> "NoteType":
    for template in note_type["tmpls"]:
        for side in ["qfmt", "afmt"]:
            if field["edit"] == Editability.ALL:
                template[side] = re.sub(
                    "{{((?:(?!edit:)[^#/:}]+:)*%s)}}" % field["name"],
                    r"{{edit:\1}}",
                    template[side],
                )
            elif field["edit"] == Editability.NONE:
                template[side] = re.sub(
                    "{{((?:[^#/:}]+:)*)edit:((?:[^#/:}]+:)*%s)}}" % field["name"],
                    r"{{\1\2}}",
                    template[side],
                )
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
        has_edit = "edit" in modifiers
        field_info = TemplateField(name=field_name, edit=has_edit)
        fields.append(field_info)
    return fields


def get_fields_in_every_notetype(fields_in_note_type: List[NoteTypeFields]) -> None:
    for i in fields_in_note_type:
        fields_in_note_type.pop()

    models = mw.col.models
    note_types = models.all()
    for note_type in note_types:
        templates = note_type["tmpls"]
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
                    (False, True): Editability.NONE,
                }[(fldname in editable_field_names, fldname in uneditable_field_names)]

                field = FieldIsEditable(name=fldname, edit=editable, orig_edit=editable)
                fields_list.append(field)
            except:
                pass
        nt = NoteTypeFields(name=note_type["name"], fields=fields_list)
        fields_in_note_type.append(nt)


def fields_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.add_tab("Fields")
    dropdown = QComboBox()
    tab.addWidget(dropdown)
    tab.space(10)
    tab.text("Check the boxes to make the fields editable while reviewing")
    qlist = QListWidget()
    qlist.setStyleSheet("QListWidget{border: 1px solid; padding: 6px;}")
    tab.addWidget(qlist)

    fields_in_note_type: List[NoteTypeFields] = []

    def update_label_status(idx: int) -> None:
        notetype = fields_in_note_type[idx]
        editable = {Editability.NONE: 0, Editability.PARTIAL: 0, Editability.ALL: 0}
        for field in notetype["fields"]:
            editable[field["edit"]] += 1
        if editable[Editability.ALL] + editable[Editability.PARTIAL] == 0:
            status = "❌"
        elif editable[Editability.NONE] + editable[Editability.PARTIAL] == 0:
            status = "✅"
        else:
            status = "🔶"
        old_label = dropdown.itemText(idx)
        new_label = old_label[:-1] + status
        dropdown.setItemText(idx, new_label)

    def on_check(item: QListWidgetItem) -> None:
        nt_idx = dropdown.currentIndex()
        fields = fields_in_note_type[nt_idx]["fields"]
        field = fields[qlist.row(item)]
        field["edit"] = Editability.from_check_state(item.checkState())
        update_label_status(nt_idx)

    def on_double_click(item: QListWidgetItem) -> None:
        curr_check = item.checkState()
        if curr_check == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:  # Partially checked or unchecked
            item.setCheckState(Qt.CheckState.Checked)

    def switch_template(idx: int) -> None:
        if idx == -1:
            return
        qlist.clear()
        fields = fields_in_note_type[idx]["fields"]
        for field in fields:
            item = QListWidgetItem(field["name"], qlist, QListWidgetItem.ItemType.Type)
            qlist.addItem(item)
            item.setCheckState(Editability.to_check_state(field["edit"]))

    def on_save() -> None:
        for note_type_fields in fields_in_note_type:
            modified = False
            try:  # 2.1.45
                note_type = mw.col.models.by_name(note_type_fields["name"])
            except:  # 2.1.41-44
                note_type = mw.col.models.byName(  # type: ignore
                    note_type_fields["name"]
                )
            for field in note_type_fields["fields"]:
                if field["edit"] != field["orig_edit"]:
                    modified = True
                    note_type = modify_field_editability(note_type, field)
            if modified:
                mw.col.models.save(note_type)

    qlist.itemChanged.connect(on_check)
    qlist.itemDoubleClicked.connect(on_double_click)
    dropdown.currentIndexChanged.connect(switch_template)
    conf_window.execute_on_save(on_save)

    get_fields_in_every_notetype(fields_in_note_type)
    for idx, nt in enumerate(fields_in_note_type):
        dropdown.addItem(nt["name"] + "  ")
        update_label_status(idx)
    dropdown.setCurrentIndex(0)  # Triggers currentIndexChanged

    def make_every_field_editable() -> None:
        for idx, note_type_fields in enumerate(fields_in_note_type):
            for field in note_type_fields["fields"]:
                field["edit"] = Editability.ALL
            update_label_status(idx)
        switch_template(dropdown.currentIndex())

    tab.space(10)
    button_layout = tab.hlayout()
    button_layout.stretch()
    button = QPushButton("Make every field in every note type editable ✅")
    button.clicked.connect(make_every_field_editable)
    button_layout.addWidget(button)
    button_layout.stretch()
    tab.space(5)


def about_tab(conf_window: ConfigWindow) -> None:
    conf = conf_window.conf
    tab = conf_window.add_tab("About")
    tab.text("Edit Field During Review (Cloze)", bold=True, size=20)
    tab.text("© 2019-2021 Yoonchae Lee (Bluegreenmagick)")
    tab.text(f"Version {conf['version.major']}.{conf['version.minor']}")
    tab.text(
        "Found a bug?"
        " <a href='https://github.com/BlueGreenMagick/Edit-Field-During-Review-Cloze/issues'>"
        "Report issues here"
        "</a>.",
        html=True,
    )
    tab.space(15)
    tab.text("License", bold=True)
    tab.text(
        "Edit Field During Review (Cloze) is a Free and Open Source Software (FOSS)"
        " distributed under the GNU AGPL v3 license."
        " It may also contain code that are licensed under a different license."
        " Please see the LICENSE file for more information.",
        multiline=True,
    )
    tab.stretch()


def with_window(conf_window: ConfigWindow) -> None:
    conf_window.set_footer("Changes will take effect when you start a review session")


conf.use_custom_window()
conf.on_window_open(with_window)
conf.add_config_tab(general_tab)
conf.add_config_tab(formatting_tab)
conf.add_config_tab(fields_tab)
conf.add_config_tab(about_tab)
