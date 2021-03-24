from .configmanager import ConfigManager, ConfigWindow

conf = ConfigManager()


def generalTab(conf_window: ConfigWindow) -> None:
    tab = conf_window.addTab("General")
    layout = tab.layout()

    layout.checkbox(
        "ctrl_click", "Ctrl + Click to edit card (Cmd on mac)"
    ).setToolTip("If not checked, there is no need to press Ctrl")

    hlayout = layout.hlayout()
    hlayout.label("HTML tag to use for editable field:")
    tab_options = ["div", "span"]
    hlayout.dropdown(
        "tag", tab_options, tab_options
    )
    hlayout.stretch()

    layout.stretch()


conf_window = conf.enable_config_window()
generalTab(conf_window)
