from nicegui import ui
from typing import Callable, Optional

class ToggleButton(ui.button):
    _WordButtons = {    }

    def __init__(self, linkedId, label: str = None, on_click: Optional[Callable]= None, col1: str= "#000000", col2: str= "#111111",  *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._state = False
        self.link = linkedId
        self.label = label
        self.col1 = col1
        self.col2 = col2
        self.on('click', self.toggle)
        if(on_click != None):
            self.on('click', lambda: on_click(self))
        
        if(linkedId in ToggleButton._WordButtons.keys()):
            ToggleButton._WordButtons[linkedId].append(self)
        else:
            ToggleButton._WordButtons[linkedId] = [self]
        with self.style(f"height: 3rem; box-shadow: none !important; text-transform: none;").props('unelevated'):
            if(label != None):
                ui.label(label).style(f'font-weight: normal')
                

    def toggle(self) -> None:
        """Toggle the button state."""
        if not self._state:
            # print(self.link)
            #only toggle this button on if it's currently off
            for link in ToggleButton._WordButtons.keys():
                enable = link == self.link
                for btn in ToggleButton._WordButtons[link]:
                    # print(enable)
                    btn._state = enable  #enable or disable buttons
                    btn.update()
        else:
            for btn in ToggleButton._WordButtons[self.link]:
                    btn._state = False  #turn off btns
                    btn.update()


    
    def is_toggled(self) -> bool:
        return self._state

    def update(self) -> None:
        self.style(f'background-color: {self.col2 if self._state else self.col1} !important;')
        super().update()