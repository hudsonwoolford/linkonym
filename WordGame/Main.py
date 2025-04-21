from nicegui import ui
import GameLogic
import time
import math
import asyncio

#UI variables
_ChainScrollArea: ui.scroll_area = None

#UI functions
def RestartBtn():
    GameLogic.RestartGame()
    StartTargetCards.refresh()
    TimelineChain.refresh()

def GuessInput(inputBox: ui.input):
    guess = inputBox.value
    valid, message = GameLogic.ValidateGuess(guess)
    if(valid):
        valid, message = GameLogic.GuessWord(guess)

        if(valid):
            TimelineChain.refresh()
            ui.notify(message, type='positive', timeout=1000)
        else:
            ui.notify(message, type='warning', timeout=1000)
    else:
        ui.notify(message, type='negative', timeout=1000)

    inputBox.value = ""
    ui.run_javascript(f"document.getElementById('{inputBox.id}').focus()")

@ui.refreshable
def TimelineChain():
    for i, word in enumerate(GameLogic._WordChain):
        with ui.card(align_items='left').classes('flat no-shadow w-full'):
            with ui.row().classes('gap-4'):
                ui.label(f'{i}').style('color: #555555')
                ui.label(word).style('font-weight: bold')
                
        
def Lerp(val1: float, val2: float, time: float):
    return round((val2-val1) * time + val1, 2)
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
            TimelineChain()
    
ui.run(reload=False)

