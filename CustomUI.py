from nicegui import ui
from typing import Callable, Optional

class ToggleButton(ui.button):
    def __init__(self, linkedId, label: str = None, on_click: Optional[Callable]= None, col1: str= "#000000", col2: str= "#111111",  *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._state = False
        self.link = linkedId
        self.label = label
        self.col1 = col1
        self.col2 = col2
        self.classes('c-toggle__btn')
        self.enable(False)
        if(on_click != None):
            self.on('click', lambda: on_click(self))
        
        with self.style(f"height: 3rem; box-shadow: none !important; text-transform: none;").props('unelevated'):
            if(label != None):
                ui.label(label).style(f'font-weight: normal')
                

    def enable(self, enable: bool) -> None:
        self._state = enable
        self.update()
    
    def is_toggled(self) -> bool:
        return self._state

    def update(self) -> None:
        self.style(f'background-color: {self.col2 if self._state else self.col1} !important;')
        super().update()