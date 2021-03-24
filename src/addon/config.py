from .configmanager import ConfigManager, ConfigWindow

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
    layout.spacing()

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


conf_window = conf.enable_config_window()
general_tab(conf_window)
formatting_tab(conf_window)
