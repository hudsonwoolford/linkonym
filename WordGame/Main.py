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
    _WinDialog.clear()

def GuessInput(inputBox: ui.input):
    guess = inputBox.value
    valid, message = GameLogic.ValidateGuess(guess)
    if(valid):
        valid, message = GameLogic.GuessWord(guess)

        if(valid):
            WordChain.refresh()
            ui.notify(message, type='positive', timeout=1000, position='top')
            if(guess == GameLogic._TargetWord):
                WinDialog(_WinDialog)
        else:
            ui.notify(message, type='warning', timeout=1000, position='top')
    else:
        ui.notify(message, type='negative', timeout=1000, position='top')

    inputBox.value = ""
    ui.run_javascript(f"document.getElementById('{inputBox.id}').focus()")

def WinDialog(dialog: ui.dialog):
    with dialog, ui.card().classes('w-64 h-108 no-shadow border-[1px] items-center justify-center'):
        ui.label("You won!").style("font-weight: bold; font-size: 150%")
        ui.label(f"Score: {len(GameLogic._WordChain)-1} links").style('color: #777777')
        ui.label(f"Chain:")
        with ui.scroll_area().classes('border rounded'):
            with ui.list().classes('gap-2 justify-center'):
                for w in GameLogic._WordChain:
                    ui.label(w)
        ui.button(icon='r_refresh', on_click=lambda e: (dialog.close(), RestartBtn()))
    dialog.open()


@ui.refreshable
def WordChain():
    for i, word in enumerate(GameLogic._WordChain):
        distToTarget = GameLogic.WordSim(word, GameLogic._TargetWord, 3)

        with ui.card(align_items='left').classes('border-[1px] no-shadow w-full'):
            with ui.row().classes('gap-4 w-full'):
                ui.label(f'{i+1}').style('color: #555555')
                ui.label(word).style('font-weight: bold')
                ui.label(f'({distToTarget}) to {GameLogic._TargetWord}').style('color: #777777').classes('ml-auto')
    
@ui.refreshable 
def StartTargetCards():
    with ui.row().classes('gap-0'):
            with ui.card(align_items='center').classes('w-48 no-shadow border-[1px]'):
                ui.label(GameLogic._StartWord)
            with ui.card(align_items='center').classes('w-48 no-shadow border-[1px]'):
                ui.label(GameLogic._TargetWord)

#start of program
if(__name__ == "__main__"):
    GameLogic.InitializeGame() #start game / processors

    #start of UI
    ui.dark_mode().enable()
    
    #winning dialogue setup
    _WinDialog = ui.dialog()
    _WinDialog.close()

    with ui.header().style('background-color: #222222').style('font-size: 24').classes('h-16 font-weight-bold'):
        ui.button(icon='r_refresh', on_click=lambda e: RestartBtn()).classes('flat')
        ui.label('Linkedle').style('font-size: 250%; font-weight: bold').classes('absolute-center')

    #show start and target
    with ui.column().classes('w-full h-full justify-center items-center'):
        StartTargetCards()
        
        #word box
        inputText = ui.input(placeholder="chain a word...").props('outlined dense autocomplete=off autocapitalize=off').classes('w-96')
        inputText.on('keydown', lambda e: GuessInput(inputText) if e.args['key'] == "Enter" else None)

        with ui.scroll_area().classes('border rounded w-96 h-256 gap-3') as scrollArea:
            WordChain()
    
    
ui.run(reload=False)

