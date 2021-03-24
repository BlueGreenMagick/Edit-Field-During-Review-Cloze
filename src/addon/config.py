from .configmanager import ConfigManager, ConfigWindow

conf = ConfigManager()


def generalTab(conf_window: ConfigWindow) -> None:
    tab = conf_window.addTab("General")
    layout = tab.layout()

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


conf_window = conf.enable_config_window()
generalTab(conf_window)
