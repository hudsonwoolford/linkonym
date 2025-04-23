from nicegui import ui

class ToggleButton(ui.button):
    _ButtonsGroup = []

    def __init__(self, label, onChange = None, col1: str= "#000000", col2: str= "#111111",  *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._state = False
        self.label = label
        self.col1 = col1
        self.col2 = col2
        self.onChange = onChange
        self.on('click', self.toggle)
        ToggleButton._ButtonsGroup.append(self)
        with self.style(f"height: 3rem; width: 40%; box-shadow: none !important; text-transform: none; display: flex; justify-content: center; align-items: center;").props('unelevated'):
            ui.label(label).style(f'font-weight: normal')

    def toggle(self) -> None:
        """Toggle the button state."""
        if not self._state:
            # Only toggle this button on if it's currently off
            self._state = True
            for button in ToggleButton._ButtonsGroup:
                if button is not self:
                    button._state = False  # Turn off all other buttons
                    button.update()
            self.onChange(self.label) 
        else:
            self.onChange("") 
            self._state = False  # Allow the button to be turned off independently   

        self.update()

    
    def is_toggled(self) -> bool:
        return self._state

    def update(self) -> None:
        self.style(f'background-color: {self.col2 if self._state else self.col1} !important;')
        super().update()