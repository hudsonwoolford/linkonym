from nicegui import ui, app
import GameLogic
from CustomUI import ToggleButton
import Dictionary as WordDictionary
import asyncio

#UI variables
_ChainScrollArea: ui.scroll_area = None
_EmbedOptionKey: str = "Wikipedia2014" #default embed path
_InputWordBox: ui.input = None
_Seed: str = "Seed"
_UseSeed: bool = False
_Dialogs: dict = {}

#UI colours and parameters
GAME_NAME = "Lexichain"
BORDER_COLOR = '#AAAAAA'
BORDER_WIDTH = '0px'
BORDER_RADIUS = '10px'
BORDER_SETTINGS = f'border-color: {BORDER_COLOR}; border-width: {BORDER_WIDTH}; border-radius: {BORDER_RADIUS}'
TEXT_PRIMARY = 'white'
TEXT_BLACK = 'black'
TEXT_SECONDARY = '#777777'
TEXT_DARK_GREY = '#555555'
PRIMARY = '#5c0000'
# PRIMARY = '#5898d4'
SECONDARY =  '#26a69a'
ACCENT = '#9c27b0'
DARK = '#1d1d1d'
DARK_PAGE = '#121212'
POSITIVE = '#21ba45'
NEGATIVE = '#c10015'
INFO = '#31ccec'
WARNING = '#f2c037'
GAME_WIDTH_VALUE = 24
HEADER_HEIGHT = '4rem'
NUM_DEFINITIONS = 2


"""
DEFAULTS
primary:	Primary color (default: "#5898d4")
secondary:	Secondary color (default: "#26a69a")
accent:	Accent color (default: "#9c27b0")
dark:	Dark color (default: "#1d1d1d")
dark_page:	Dark page color (default: "#121212")
text_white: White text color (default: "#555555")
text_grey: Grey text color (default: "#777777")
border_white: White border color (default: "#AAAAAA")
positive:	Positive color (default: "#21ba45")
negative:	Negative color (default: "#c10015")
info:	Info color (default: "#31ccec")
warning:	Warning color (default: "#f2c037")
custom_colors:	Custom color definitions for branding (needs ui.colors to be called before custom color is ever used, added in version 2.2.0)
"""
EMBED_OPTIONS = {
    "Wikipedia2014" :
    {
        "words"  : "output/WikipediaWData.pt",
        "banned" : "output/WikipediaBData.pt"
    },
    "WikiNews2017" :
    {
        "words"  : "output/WikiNewsWData.pt",
        "banned" : "output/WikiNewsBData.pt"
    },
    "Google" :
    {
        "words"  : "output/GoogleNewsWData.pt",
        "banned" : "output/GoogleNewsBData.pt"
    },
    "LexVec" :
    {
        "words"  : "output/LexVecWData.pt",
        "banned" : "output/LexVecBData.pt"
    },
    "NumberBatch" :
    {
        "words"  : "output/NumberBatchWData.pt",
        "banned" : "output/NumberBatchBData.pt"
    }
}


""" 
-------------------------------------------------------------------------------

UTILITY FUNCTIONS

-------------------------------------------------------------------------------
"""

def OverlayCard() -> ui.card:
    return ui.card().style(f'{BORDER_SETTINGS}; width: 20rem; height: 28rem').classes(f'hidden-scroll no-shadow items-center hidden-scrollbar')

def CopyClipboardGame():
    chain = ""
    for word in GameLogic._WordChain:
        chain += f"||{word}||\n"

    ui.clipboard.write(f"""
----------
Check out my {GAME_NAME} game! 🙂

Here's my word chain from '{GameLogic._StartWord}' to '{GameLogic._TargetWord}': 🔗

{chain}

Score: {len(GameLogic._WordChain)-1} 🔥
Hints: {GameLogic._NumHints} 💡

You can play the same game here: {GAME_NAME}.me/{GameLogic._Seed}
----------
""")
    
    ui.notify("Copied game to clipboard")

async def GiveUp():
    notif = ui.notification(timeout=None)
    notif.message = 'Solving...'
    notif.spinner = True

    await asyncio.sleep(0.1)  #let the nicegui render the notification

    #run HintWord in a thread so it doesn't block
    loop = asyncio.get_running_loop()
    for i in range(0, 20):
        lastWord = GameLogic._WordChain[-1]
        hint = await loop.run_in_executor(None, GameLogic.HintWord, lastWord, GameLogic._TargetWord, 0.15)
        GameLogic.GuessWord(hint)
        WordChain.refresh(True)
        if(GameLogic.WordSim(hint, GameLogic._TargetWord) < GameLogic.DISTANCE_CUTOFF):
            GameLogic.GuessWord(GameLogic._TargetWord)
            GameLogic._NumHints += 1
            WordChain.refresh(True)
            break

    notif.spinner = False
    notif.message = 'Done!'
    notif.type = 'positive'
    await asyncio.sleep(0.5)
    notif.dismiss()
    
    GameLogic._GivenUp = True
    WinGame()


async def Hint():
    lastWord = GameLogic._WordChain[-1]

    notif = ui.notification(timeout=None)
    notif.message = 'Calculating hint...'
    notif.spinner = True

    if(GameLogic.WordSim(lastWord, GameLogic._TargetWord) < GameLogic.DISTANCE_CUTOFF):
        GameLogic.GuessWord(GameLogic._TargetWord)
        WinGame()
    else:
        await asyncio.sleep(0.1)  #let the nicegui render the notification
        
        #run HintWord in a thread so it doesn't block
        loop = asyncio.get_running_loop()
        hint = await loop.run_in_executor(None, GameLogic.HintWord, lastWord, GameLogic._TargetWord, 0.15)

        GameLogic.GuessWord(hint)

    WordChain.refresh(True)

    notif.spinner = False
    notif.message = 'Done!'
    notif.type = 'positive'
    await asyncio.sleep(0.5)
    notif.dismiss()


def ChangeSiteColor(color: str):
    global PRIMARY
    PRIMARY = color
    app.storage.browser['color'] = color
    ui.colors(primary=PRIMARY, secondary=SECONDARY, accent=ACCENT, positive=POSITIVE, negative=NEGATIVE, info=INFO, warning=WARNING, dark=DARK, dark_page=DARK_PAGE)
    ui.run_javascript(f'''
    document.documentElement.style.setProperty('--selection-color', '{PRIMARY}');
    ''')
    HeaderRow.refresh()
    ui.notify(f"Changed site color to {PRIMARY}", timeout=500)

def RestartBtn():
    ui.navigate.to('/'+_Seed if _UseSeed else str(GameLogic.random.randint(0, 50000)))
    # GameLogic.RestartGame(_Seed if _UseSeed else None)
    # DictionaryText.refresh()
    # StartTargetCards.refresh()
    # WordChain.refresh()
    # _Dialogs['win'].clear()

#when user inputs guess from textbox
def GuessInput(inputBox: ui.input):
    guess = inputBox.value
    
    valid, message, guess = GameLogic.ValidateGuess(guess) #if guess is valid/(if it is in possible values and not banned)
    if(valid):
        valid, message = GameLogic.GuessWord(guess) #get result of guessing the word, valid if it is within distance

        if(valid):
            WordChain.refresh(True)
            ui.notify(message, type='positive', timeout=1500, position='bottom', badgeColor=POSITIVE, badgeTextColor=TEXT_PRIMARY)
            if(guess == GameLogic._TargetWord):
                WinGame()
                
        else:
            ui.notify(message, type='warning', timeout=1500, position='bottom', badgeColor='warning', badgeTextColor=TEXT_BLACK)
    else:
        ui.notify(message, type='negative', timeout=1500, position='bottom', badgeColor=NEGATIVE, badgeTextColor=TEXT_PRIMARY)

    #reset and refocus box
    inputBox.value = ""
    ui.run_javascript(f"document.getElementById('{inputBox.id}').focus()")

def WinGame():
    #stop input
    _InputWordBox.props('disable')

    #store data
    StatsDialogElements.refresh()

    #show dialog
    WinDialogElements.refresh(_Dialogs['win'])
    _Dialogs['win'].open()


def SelectEmbedOption(option: str):
    global _EmbedOptionKey
    _EmbedOptionKey = option
    CreateEmbedDropdown.refresh()
    GameLogic.LoadWordData(EMBED_OPTIONS[_EmbedOptionKey]["words"], EMBED_OPTIONS[_EmbedOptionKey]["banned"])
    WordChain.refresh(False)

def UndoBtn():
    GameLogic._WordChain = GameLogic._WordChain[:-1] if len(GameLogic._WordChain) > 1 else GameLogic._WordChain
    WordChain.refresh(False)

""" 
-------------------------------------------------------------------------------

REFRESHABLE ELEMENTS

-------------------------------------------------------------------------------
"""
#dialog card when you win the game
@ui.refreshable
def StatsDialogElements():
    scores = [1, 2, 3, 4, 5, 6, 7]
    ui.echart({
    'xAxis' : {'type' : 'value'},
    'yAxis' : {'type' : 'value'},
    'legend': {'textStyle' : {'color' : 'gray'}},
    'series': [
        {'type' : 'bar', 
            'name' : 'Scores',
            'data' : scores,
            'color': f'{PRIMARY}' }
    ],
    })

@ui.refreshable
def WinDialogElements(dialog: ui.dialog):
    #disable input
    #store parameters
    #set all parameters
    with ui.row().classes('justify-center items-center gap-1.5'):
        ui.icon('sym_r_emoji_events' if not GameLogic._GivenUp else 'sym_r_flag', size="150%", color=TEXT_PRIMARY)
        ui.label("You won!" if not GameLogic._GivenUp else "Gave up!").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")

    with ui.row().classes('justify-center items-center gap-1.5'):
        ui.chip(f"{len(GameLogic._WordChain)-1} links", icon='sym_r_link')

        ui.chip(f"{GameLogic._NumHints} hint" + ('s' if GameLogic._NumHints != 1 else ''), icon='sym_r_lightbulb')

    with ui.scroll_area().style(f'border-color: {BORDER_COLOR}; border-radius: {BORDER_RADIUS}; border-width: 1px; width: 90%').classes('h-full') as scrollArea:
        with ui.timeline(side='right', layout='dense').classes('gap-0 p-0 h-full'):
            for i, w in enumerate(GameLogic._WordChain):
                GameLogic.WordSim(w, GameLogic._TargetWord, 3)
                ui.timeline_entry("",subtitle=w).style('height: 4rem').classes('p-0')
            scrollArea.scroll_to(percent=100, duration=1)

    with ui.row().style('width: 100%; height: 10%').classes('justify-center'):
        ui.button(icon='sym_r_navigate_next', on_click=lambda e: (dialog.close(), RestartBtn()))
        ui.button(icon='sym_r_ios_share', on_click=lambda e: CopyClipboardGame())

    

@ui.refreshable
def WordChain(fadeIn: bool = True):
    #create a card for each word
    with ui.column().classes("w-full gap-2"):
        for i, word in enumerate(GameLogic._WordChain):
            chainMessage = f"({GameLogic.WordSim(word, GameLogic._TargetWord, 3)}) to '{GameLogic._TargetWord}'"
            # if(not i == len(GameLogic._WordChain)-1):
            #     chainMessage = f"({GameLogic.WordSim(word, GameLogic._WordChain[i+1], 3)})"
            appendStyle = "" if i != len(GameLogic._WordChain) - 1 or not fadeIn  else "; animation: fade 0.3s"
            
            with ToggleButton(linkedId=word, col1=DARK, col2=PRIMARY, on_click= lambda e, wordPass=word:DictionaryText.refresh(wordPass if e._state else "")).style(f"width: 100%; {BORDER_SETTINGS}" + appendStyle).classes(f'custom-button-content'):
                with ui.row().style('width: 100%').classes('gap-4 h-full items-center justify-start text-left'):
                    ui.label(f'{i+1}').style(f'color: {TEXT_SECONDARY}')
                    ui.label(word).style(f'font-weight: normal; color: {TEXT_PRIMARY}')
                    ui.label(f'{chainMessage}').style(f'color: {TEXT_SECONDARY}').classes('ml-auto')

    
    ui.element().style("height: 8rem").classes('w-full')
    _ChainScrollArea.scroll_to(percent=100, axis='vertical', duration=0.5)
    
@ui.refreshable 
def StartTargetCards():
    #create cards for start and target
    with ui.row().classes('gap-0 items-center justify-between w-full'):
            ToggleButton(linkedId=GameLogic._StartWord, label=GameLogic._StartWord, col1=DARK, col2=PRIMARY, on_click= lambda e:DictionaryText.refresh(GameLogic._StartWord if e._state else "")).style(BORDER_SETTINGS+"; width: 40%")
            ui.icon("sym_r_keyboard_double_arrow_right", size="2rem", color=BORDER_COLOR)
            ToggleButton(linkedId=GameLogic._TargetWord, label=GameLogic._TargetWord, col1=DARK, col2=PRIMARY, on_click= lambda e: DictionaryText.refresh(GameLogic._TargetWord if e._state else "")).style(BORDER_SETTINGS+"; width: 40%")

@ui.refreshable
def CreateEmbedDropdown():
    with ui.dropdown_button(_EmbedOptionKey, icon="sym_r_storage", auto_close=True):
        for opt in EMBED_OPTIONS.keys():
            hexColor = PRIMARY if opt == _EmbedOptionKey else DARK
            ui.item(str(opt), on_click=lambda e, option = str(opt): SelectEmbedOption(option)).style(f"background-color: {hexColor}")

@ui.refreshable
def DictionaryText(word: str =""):
    if(word != ''):
        ui.separator().style(f'background-color: {BORDER_COLOR}; animation: fade 0.5s')            
        ui.element('div').classes('my-2')

        definitionNotFound = False
        definitions = WordDictionary.getRecordsAdvanced(word)
        if(definitions == None or len(definitions.keys())==0): 
            word = GameLogic._WordData['vocab'][word]['lemma']
            definitions = WordDictionary.getRecordsAdvanced(word)

        if(definitions == None or len(definitions.keys())==0):
            definitionNotFound = True
            definitions = {
                'definition_1' : f'https://www.google.com/search?q=define%20{word} to find the meaning',
                'pos_1' : 'No available definition'
            }
        
        ui.label(word).style(f'font-size: 250%; font-weight: bold; color: {TEXT_PRIMARY}; text-align: left; animation: fade 1s')
        total = min(NUM_DEFINITIONS, sum(1 for key in definitions if key.startswith("definition_")))
        for i in range(1, total+1):
            ui.element('div').classes('my-2')
            ui.label(f"{i}. {definitions[f'pos_{i}']}").style(f'color: {TEXT_PRIMARY}; text-align: left; animation: fade 1s').classes('text-italic')
            ui.element('div').classes('my-2')

            if(not definitionNotFound):
                ui.label(definitions[f'definition_{i}']).style(f' color: {TEXT_PRIMARY}; text-align: left; animation: fade 1s')
            else:
                ui.link(text = f"Please visit https://www.google.com/search?q=define%20{word} for the meaning", target=f'https://www.google.com/search?q=define%20{word}', new_tab=True).style(f' color: {TEXT_PRIMARY}; text-align: left; animation: fade 1s')
        
        ui.element('div').classes('my-4')
        ui.separator().style(f'background-color: {BORDER_COLOR}; animation: fade 0.5s')

@ui.refreshable
def HeaderRow():
    with ui.row().style(f'height: {HEADER_HEIGHT}').classes('justify-between items-center w-full'):
        with ui.row().classes('justify-start').style('width: 30%'):
            ui.button(icon='sym_r_undo', on_click=lambda e: UndoBtn()).style('width: 10%')
            ui.button(icon='sym_r_navigate_next', on_click=lambda e: RestartBtn()).style('width: 10%')

        ui.label(f'{GAME_NAME}').style(f'color: {TEXT_PRIMARY}; font-size: 250%; font-weight: bold').classes('absolute-center')
        with ui.row().classes('justify-end').style('width: 30%'):
            # CreateEmbedDropdown()
            with ui.dropdown_button().style('width: 10%').props('dropdown-icon=sym_r_more_vert no-icon-animation transition-show=jump-down transition-hide=jump-up') as dropdownButton:
                with ui.item(on_click= Hint) as specialHintItem:
                    specialHintItem.on_click(lambda e: dropdownButton.close())
                    with ui.row().classes('justify-center items-center gap-1.5'):
                        ui.icon('sym_r_lightbulb', color=TEXT_PRIMARY, size='125%')
                        ui.label("Hint").style(f"color: {TEXT_PRIMARY}")
                with ui.item(on_click=GiveUp) as specialGiveUpItem:
                    specialGiveUpItem.on_click(lambda e: dropdownButton.close())
                    with ui.row().classes('justify-center items-center gap-1.5'):
                        ui.icon('sym_r_flag', color=TEXT_PRIMARY, size='125%')
                        ui.label("Give up").style(f"color: {TEXT_PRIMARY}")
                with ui.item(on_click=lambda e: (_Dialogs['settings'].open(), dropdownButton.close())):
                    with ui.row().classes('justify-center items-center gap-1.5'):
                        ui.icon('sym_r_build', color=TEXT_PRIMARY, size='125%')
                        ui.label("Settings").style(f"color: {TEXT_PRIMARY}")
            ui.button(icon='sym_r_info', on_click=lambda e: _Dialogs['info'].open()).style('width: 10%')

""" 
-------------------------------------------------------------------------------

PAGES

-------------------------------------------------------------------------------
"""
def GlobalSetup():
    #global setup - colours
    ui.colors(primary=PRIMARY, secondary=SECONDARY, accent=ACCENT, positive=POSITIVE, negative=NEGATIVE, info=INFO, warning=WARNING, dark=DARK, dark_page=DARK_PAGE)
    ui.dark_mode().enable() 

    #global setup - html
    ui.add_head_html(
    r'''
    <style>
    @keyframes fade {from {opacity: 0;} to {opacity: 1.0;}}
    </style>
    ''') #fading

    ui.add_head_html(
    r'''
    <style>
    .hidden-scrollbar {
    overflow-y: scroll;
    scrollbar-width: none; /* Firefox */
    -ms-overflow-style: none;  /* Internet Explorer 10+ */
    }

    .hidden-scrollbar::-webkit-scrollbar { /* WebKit */
    width: 0;
    height: 0;
    }
    </style>
    <style>
    .custom-button-content .q-btn__content {
        width: 100% !important;
        padding: 0 !important;
        display: flex !important;
        align-items: stretch !important;
    }
    .no-backdrop-dialog .q-dialog__backdrop{
        background: rgba(0,0,0,0) !important; /* nothing - this better work */   
    }
    
    </style>
    ''')#other html

    ui.add_head_html(
    '''
    <style>
    :root {
    --selection-color:''' + PRIMARY + ''';
    }
    ::selection {
    background: var(--selection-color);
    }
    </style>
    ''') #selection color

    #global setup - dialogs
    global _Dialogs

    #stats dialog setup
    
    _Dialogs['stats'] = ui.dialog().props('transition-hide=fade transition-show=fade').style('backdrop-filter: none').classes('no-backdrop-dialog')
    statRadio = None
    with _Dialogs['stats'], OverlayCard().classes('justify-between'):
        StatsDialogElements()
        statRadio = ui.radio(['0', '1'], value='0', on_change= lambda e: _Dialogs['stats'].close()).props('inline size=xs')


    #winning dialogue setup
    _Dialogs['win'] = ui.dialog()
    with _Dialogs['win'] as dialog, OverlayCard():
        WinDialogElements(dialog)
        ui.radio(['0', '1'], value='0', on_change= lambda e: _Dialogs['stats'].open()).props('inline size=xs').bind_value(statRadio, 'value')


    #info dialogue setup
    _Dialogs['info'] = ui.dialog()
    with _Dialogs['info'], OverlayCard():

        descriptionCSS = f'color: #AAAAAA; font-style: normal; font-size: 90%'
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_info', size="150%", color=TEXT_PRIMARY)
            ui.label("Info").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")
        with ui.expansion(text="How do I play?").style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""Your goal is to create a chain of related words to reach a 'target' word. 
                        Start and ending words are determined randomly, and links must have a maximum
                        similarity of {GameLogic.DISTANCE_CUTOFF} from the previous.""").style(descriptionCSS)
        with ui.expansion(text='How are word similarities determined?').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""{GAME_NAME} queries a database of over 70000 words that each have a corresponding vector. These vectors
                        are tweaked through NLP models. A euclidean distance operation between two word vectors returns the similarity.
                        Since similarity is based upon similar contexts, it doesn't necessarily translate to similar meaning.""").style(descriptionCSS)
        with ui.expansion(text=f'Who created {GAME_NAME}?').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""Hudson Woolford programmed {GAME_NAME} in python for a Computer Science project at his school.""").style(descriptionCSS)
            ui.label("""Ted Boss acted as a playtester and provided valuable feedback throughout development""").style(descriptionCSS + f'; color: {TEXT_SECONDARY}')
        with ui.expansion(text='Have you made any other products?').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label("""Hudson Woolford was a developer on Swingularity, an indie space golf game. Check it out!""").style(descriptionCSS)
            ui.link(text="Swingularity on STEAM", target="https://store.steampowered.com/app/3272450/Swingularity/", new_tab=True).style(descriptionCSS)

    #settings tools dialog
    _Dialogs['settings'] = ui.dialog()
    with _Dialogs['settings'], OverlayCard().classes('gap-4 justify-start'):
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_build', size="150%", color=TEXT_PRIMARY)
            ui.label("Settings").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")
        ui.label('Site color:')
        picker = ui.element('q-color').props('default-view=palette no-header no-footer')
        picker.on('update:model-value', lambda color: ChangeSiteColor(color.args))
        # picker.q_color.props('default-view=palette no-header no-footer')
        
        ui.button(icon='sym_r_delete', text='Clear Data').classes('justify-center w-full')

            
@ui.page('/dev')
def DevPage():
    ui.dark_mode().enable() 
    ui.label('nice try')

@ui.page('/{seed}')
def GamePage(seed: str):
    global PRIMARY
    global _ChainScrollArea, _InputWordBox
    GlobalSetup()

    #load data and start game
    GameLogic.LoadWordData(EMBED_OPTIONS[_EmbedOptionKey]["words"], EMBED_OPTIONS[_EmbedOptionKey]["banned"])
    GameLogic.RestartGame(seed=seed)

    #header
    with ui.header().style(f'background-color: {DARK}').style(f'font-size: 24; height: {HEADER_HEIGHT}').classes('py-0 w-screen font-weight-bold'):
        HeaderRow()
    

    with ui.column().style(f'width: {GAME_WIDTH_VALUE}rem; justify-content: center; padding-top: 1rem').classes('h-full absolute-center'):
        with ui.element().style('display: flex').classes('w-full justify-center items-center'):
            ui.chip(f"Chain similar words to get to the target",icon="sym_r_link").props("outlined")

        #show start and target
        StartTargetCards()

        _InputWordBox = ui.input(placeholder="chain a word..."
                            ).props(f'autocomplete=off; autocapitalize=off; input-style="color: {BORDER_COLOR}"; autofocus'
                            ).classes(f' gap-0 items-center w-full')
        _InputWordBox.on('keydown', lambda e: GuessInput(_InputWordBox) if e.args['key'] == "Enter" else None)

        #word chain scroll area
        with ui.element().classes("h-screen w-full"):
            with ui.scroll_area().style(f"height: 60%; border-color: {BORDER_COLOR}; border-width: 1px; border-radius: {BORDER_RADIUS}").classes(f'rounded w-full') as scrollArea:
                _ChainScrollArea = scrollArea
                WordChain()
            ui.element('div').classes('my-4')
            DictionaryText()

@ui.page('/')
def HomePage():
    #redirect to daily / random game
    ui.navigate.to('/' + str(GameLogic.random.randint(0, 50000)))



""" 
-------------------------------------------------------------------------------

START OF AUTO-INDEX OR LOGIC

-------------------------------------------------------------------------------
"""

ui.run(reload=False, title=f"{GAME_NAME}", show=False, storage_secret='SWINGULARITY') #dont use reload (watch files) because leads to errors

