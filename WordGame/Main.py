from nicegui import ui
import GameLogic
import time
import math
import asyncio

#UI variables
_WinDialog: ui.dialog = None

#UI functions
def RestartBtn():
    GameLogic.RestartGame()
    StartTargetCards.refresh()
    WordChain.refresh()

def GuessInput(inputBox: ui.input):
    guess = inputBox.value
    valid, message = GameLogic.ValidateGuess(guess)
    if(valid):
        valid, message = GameLogic.GuessWord(guess)

        if(valid):
            WordChain.refresh()
            ui.notify(message, type='positive', timeout=1000)
            if(guess == GameLogic._TargetWord):
                WinDialog(_WinDialog)
        else:
            ui.notify(message, type='warning', timeout=1000)
    else:
        ui.notify(message, type='negative', timeout=1000)

    inputBox.value = ""
    ui.run_javascript(f"document.getElementById('{inputBox.id}').focus()")

def WinDialog(dialog: ui.dialog):
    with dialog, ui.card().classes('w-64 h-108 no-shadow border-[1px] items-center'):
        ui.label("You won!").style("font-weight: bold; font-size: 150%")
        ui.label(f"Score: {len(GameLogic._WordChain)-1}").style('color: #555555')
        ui.label(f"Chain")
        with ui.scroll_area().classes('border rounded justify-center items-center'):
            for w in GameLogic._WordChain:
                ui.label(w)
        ui.button(icon='r_refresh', on_click=lambda e: (dialog.close(), RestartBtn()))
    dialog.open()


@ui.refreshable
def WordChain():
    for i, word in enumerate(GameLogic._WordChain):
        with ui.card(align_items='left').classes('border-[1px] no-shadow w-full'):
            with ui.row().classes('gap-4'):
                ui.label(f'{i}').style('color: #555555')
                ui.label(word).style('font-weight: bold')
                
        
@ui.refreshable 
def StartTargetCards():
    with ui.row():
            with ui.card(align_items='center').classes('w-32 no-shadow border-[1px]'):
                ui.label(GameLogic._StartWord)
            with ui.card(align_items='center').classes('w-32 no-shadow border-[1px]'):
                ui.label(GameLogic._TargetWord)

#start of program
if(__name__ == "__main__"):
    GameLogic.InitializeGame() #start game / processors

    #start of UI
    ui.dark_mode().enable()
    
    #winning dialogue setup
    _WinDialog = ui.dialog()
    _WinDialog.close()

    with ui.header().style('background-color: #555555').style('font-size: 24').classes('h-16 font-weight-bold'):
        ui.button(icon='r_refresh', on_click=lambda e: RestartBtn()).classes('flat')
        ui.label('Chainle').classes('absolute-center')

    #show start and target
    with ui.column().classes('w-full h-full justify-center items-center'):
        StartTargetCards()
        
        #word box
        inputText = ui.input(placeholder="chain a word...").props('outlined dense autocomplete=off autocapitalize=off').classes('w-64')
        inputText.on('keydown', lambda e: GuessInput(inputText) if e.args['key'] == "Enter" else None)

        with ui.scroll_area().classes('border rounded w-64 gap-3') as scrollArea:
            _ChainScrollArea = scrollArea
            WordChain()
    
    
ui.run(reload=False)

