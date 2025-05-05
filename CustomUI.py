from nicegui import ui
from typing import Callable, Optional

class ToggleButtonManager():
    def __init__(self):
        self.buttons = []
    
    def register(self, button):
        self.buttons.append(button)
    
    def enable_link(self, link: str, enable: bool):
        for b in self.buttons:
            if(b.link == link):
                b.enable(enable)
            else:
                b.enable(False)

class ToggleButton(ui.button):
    def __init__(self, linkedId, label: str = None, on_enable: Optional[Callable[[bool], None]]= None, col1: str= "#000000", col2: str= "#111111",  *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._state = False
        self.link = linkedId
        self.label = label
        self.col1 = col1
        self.col2 = col2
        self.classes('c-toggle__btn')
        self.onEnable = on_enable
        self.update()
    
        with self.style(f"height: 3rem; box-shadow: none !important; text-transform: none;").props('unelevated'):
            if(label != None):
                ui.label(label).style(f'font-weight: normal; color: var(--q-text)')
                

    def enable(self, enable: bool) -> None:
        self._state = enable
        if(self.onEnable != None):
            self.onEnable(enable)
        self.update()
    
    def is_toggled(self) -> bool:
        return self._state

    def update(self) -> None:
        self.style(f'background-color: var(--q-{self.col2 if self._state else self.col1}) !important;')
        super().update()