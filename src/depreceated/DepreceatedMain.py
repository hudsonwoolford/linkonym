from nicegui import ui, app
import src.GameLogic as GameLogic
from src.CustomUI import ToggleButton
from src.CustomUI import ToggleButtonManager
import src.Dictionary as WordDictionary
import asyncio
import random
import src.FileManager as FileManager
import datetime
import os

#UI variables

#UI colours and parameters
GAME_NAME = "Linkonym"
BORDER_COLOR = '#AAAAAA'
BORDER_WIDTH = '0px'
BORDER_RADIUS = '10px'
BORDER_SETTINGS = f'border-color: {BORDER_COLOR}; border-width: {BORDER_WIDTH}; border-radius: {BORDER_RADIUS}'
TEXT_PRIMARY = 'white'
TEXT_BLACK = 'black'
TEXT_SECONDARY = '#777777'
TEXT_DARK_GREY = '#555555'
PRIMARY = '#5c0000'
SECONDARY =  '#26a69a'
ACCENT = '#9c27b0'
DARK = '#1d1d1d'
DARK_PAGE = '#121212'
POSITIVE = '#21ba45'
NEGATIVE = '#c10015'
INFO = '#31ccec'
WARNING = '#f2c037'
GAME_WIDTH= '22rem'
HEADER_HEIGHT = '4rem'
NUM_DEFINITIONS = 2
PORT = 8080
MAX_TRACK_GAMES = 50
WEBSITE_RANDOMIZE = random.Random()


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
        "words"  : "./output/WikipediaWData.pt",
        "banned" : "./output/WikipediaBData.pt"
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
    wordChain = app.storage.tab.get('word-chain')
    terminalWords = app.storage.tab.get('terminal-words')
    numHints = app.storage.tab.get('num-hints')

    chain = ""
    for word in wordChain:
        chain += f"||{word}||\n"

    ui.clipboard.write(f"""
----------
Check out my {GAME_NAME} game! 🙂

Here's my word chain from '{terminalWords[0]}' to '{terminalWords[1]}': 🔗

{chain}

Score: {len(wordChain)-1} 🔥
Hints: {numHints} 💡

You can play the same game here: http://{GAME_NAME}.com/{app.storage.tab.get('seed')}
----------
""")
    
    ui.notify("Copied game to clipboard")


""" 
-------------------------------------------------------------------------------

REFRESHABLE ELEMENTS

-------------------------------------------------------------------------------
"""
#dialog card when you win the game

""" 
-------------------------------------------------------------------------------

PAGES

-------------------------------------------------------------------------------
"""
def CustomHTMTL():
    color = app.storage.user.get('color')

    #global setup - colours
    ui.colors(primary=color, secondary=SECONDARY, accent=ACCENT, positive=POSITIVE, negative=NEGATIVE, info=INFO, warning=WARNING, dark=DARK, dark_page=DARK_PAGE)
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
    --selection-color:''' + color + ''';
    }
    ::selection {
    background: var(--selection-color);
    }
    </style>
    ''') #selection color
    ui.add_css("""
        body {
            font-size: 16px; !important
        }
        .q-btn, .q-label, .q-input, .q-chip{
            font-size: 16px; !important
        }
    """)
    ui.add_css("""
        body {
            overflow-y: auto;  /* Ensures vertical scrolling */
        }
    """)


            
@ui.page('/dev')
def DevPage():
    ui.dark_mode().enable() 
    ui.label('nice try')

async def GamePage(_Seed: str, mode: str):
    pass

@ui.page('/{_Seed}')
async def DailyPage(_Seed):
    async def GiveUp():
        wordChain = app.storage.tab.get('word-chain')
        numHints = app.storage.tab.get('num-hints')
        terminalWords = app.storage.tab.get('terminal-words')

        notif = ui.notification(timeout=None)
        notif.message = 'Solving...'
        notif.spinner = True

        await asyncio.sleep(0.1)  #let the nicegui render the notification

        #run HintWord in a thread so it doesn't block
        loop = asyncio.get_running_loop()
        for i in range(0, 20):
            lastWord = wordChain[-1]
            hint = await loop.run_in_executor(None, GameLogic.HintWord, lastWord, terminalWords[1], wordChain, 0.15)
            GuessInput(hint)
            wordChain = app.storage.tab.get('word-chain')
            WordChain.refresh(True)
            numHints += 1
            if(GameLogic.WordSim(hint, terminalWords[1]) < GameLogic.DISTANCE_CUTOFF):
                await asyncio.sleep(0.25)  #wait a bit for clarity
                GuessInput(terminalWords[1])
                numHints += 1
                WordChain.refresh(True)
                break

        notif.dismiss()
        
        app.storage.tab['given-up'] = True
        app.storage.tab['num-hints'] = numHints
        WinGame()


    async def Hint():
        wordChain = app.storage.tab.get('word-chain')
        numHints = app.storage.tab.get('num-hints')
        terminalWords = app.storage.tab.get('terminal-words')

        lastWord = wordChain[-1]

        notif = ui.notification(timeout=None)
        notif.message = 'Calculating hint...'
        notif.spinner = True

        if(GameLogic.WordSim(lastWord, terminalWords[1]) < GameLogic.DISTANCE_CUTOFF):
            GuessInput(terminalWords[1])
            WinGame()
        else:
            await asyncio.sleep(0.1)  #let the nicegui render the notification
            
            #run HintWord in a thread so it doesn't block
            loop = asyncio.get_running_loop()
            hint = await loop.run_in_executor(None, GameLogic.HintWord, lastWord, terminalWords[1], wordChain, 0.15)

            GuessInput(hint)

        WordChain.refresh(True)

        notif.dismiss()

        numHints +=1
        app.storage.tab['num-hints'] = numHints

    def ChangeMode(mode: str):
        app.storage.tab['mode'] = mode
        if(mode == 'practice'):
            ui.navigate.to('/practice/'+str(WEBSITE_RANDOMIZE.randint(0, 50000000)))
        elif(mode=='daily'):
            ui.navigate.to('/daily')

    def ClearUserData():
        app.storage.user['color'] = PRIMARY
        app.storage.user['game-scores'] = []
        app.storage.user['games-played'] = 0

    def ChangeSiteColor(color: str):
        app.storage.user['color'] = color
        ui.colors(primary=color, secondary=SECONDARY, accent=ACCENT, positive=POSITIVE, negative=NEGATIVE, info=INFO, warning=WARNING, dark=DARK, dark_page=DARK_PAGE)
        ui.run_javascript(f'''
        document.documentElement.style.setProperty('--selection-color', '{color}');
        ''')
        HeaderRow.refresh()
        WordChain.refresh()
        TerminalCards.refresh()
        ui.notify(f"Changed site color to {color}", timeout=500)

    def PracticeBtn():
        ui.navigate.to('/practice/'+str(WEBSITE_RANDOMIZE.randint(0, 50000000)))
        # GameLogic.RestartGame(_Seed if _UseSeed else None)
        # DictionaryText.refresh()
        # StartTargetCards.refresh()
        # WordChain.refresh()
        # _Dialogs['win'].clear()

    #when user inputs guess from textbox
    def GuessInput(guess: str):
        wordChain = app.storage.tab.get('word-chain')
        terminalWords = app.storage.tab.get('terminal-words')

        valid, message, guess = GameLogic.ValidateGuess(guess, wordChain) #if guess is valid/(if it is in possible values and not banned)
        if(valid):
            valid, message = GameLogic.ValidateWordDist(guess, wordChain) #get result of guessing the word, valid if it is within distance

            if(valid):
                wordChain.append(guess)
                app.storage.tab['word-chain'] = wordChain
                WordChain.refresh(True)
                ui.notify(message, type='positive', timeout=1500, position='bottom', badgeColor=POSITIVE, badgeTextColor=TEXT_PRIMARY)
                if(guess == terminalWords[1]):
                    WinGame()
                    
            else:
                ui.notify(message, type='warning', timeout=1500, position='bottom', badgeColor='warning', badgeTextColor=TEXT_BLACK)
        else:
            ui.notify(message, type='negative', timeout=1500, position='bottom', badgeColor=NEGATIVE, badgeTextColor=TEXT_PRIMARY)

        #reset and refocus box

    def ClickToggleButton(word: str, tglBtn: ToggleButton):
        btns = app.storage.client.get('toggle-btns')
        tglBtn.enable(not tglBtn._state)
        for b in btns:
            if(b.link == tglBtn.link):
                b.enable(tglBtn._state)
            else:
                b.enable(False)
        app.storage.client['selected-word'] = word if tglBtn._state else ''
        DictionaryText.refresh()

    def WinGame():
        seed = app.storage.tab.get('seed')
        wordChain = app.storage.tab.get('word-chain')
        score = len(wordChain)-1
        gameScores = app.storage.user.get('game-scores')
        gamesPlayed = app.storage.user.get('games-played')

        #store data
        gameScores.append({
            'score' : score,
            'seed' : seed,
            'date' : str(datetime.datetime.now().date().strftime('%d/%m/%y'))
        })
        if(len(gameScores) > MAX_TRACK_GAMES):
            gameScores = gameScores[-MAX_TRACK_GAMES:]
        app.storage.user['game-scores'] = gameScores
        gamesPlayed += 1
        app.storage.user['games-played'] = gamesPlayed
        StatsDialogElements.refresh()

        #show dialog
        dialogs = app.storage.client.get('dialogs')
        WinDialogElements.refresh(dialogs['win'])
        dialogs['win'].open()

    def UndoBtn():
        wordChain = app.storage.tab.get('word-chain')

        wordChain = wordChain[:-1] if len(wordChain) > 1 else wordChain
        app.storage.tab['word-chain'] = wordChain
        WordChain.refresh(False)

    @ui.refreshable
    def StatsDialogElements():
        gameScores: list = app.storage.user.get('game-scores')
        gamesPlayed: int = app.storage.user.get('games-played')
        with ui.row().classes('justify-center items-center gap-1.5'):
                ui.icon('sym_r_bar_chart', size="150%", color=TEXT_PRIMARY)
                ui.label("Stats").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")

        if(len(gameScores) > 0):
            ui.echart({
            'height' : '60%',
            'title': {
                'text': 'Previous scores',  #title text
                'subtext': f'Maxes at {MAX_TRACK_GAMES} games',  #subtitle
                'left': 'center', 
                'top': 'top', 
                'textStyle': {
                    'color': TEXT_PRIMARY,
                    'fontSize': 16
                },
            },
            'tooltip': {
                'trigger': 'item', 
                ':formatter': """
                    function(params) {
                        return 'Score: ' + params.value + '<br>' +
                            'Seed: ' + params.name + '<br>' +
                            'Date: ' + params.data.date;
                    }
                """
            },
            'xAxis' : {'show' : False, 'type' : 'category', 'data' : [score['seed'] for score in gameScores]},
            'yAxis' : {'type' : 'value', 'splitLine' : {
                'lineStyle': {
                    'type' : 'dashed',
                    'color': TEXT_SECONDARY
                }
            }, ''
            'interval': 2},
            'legend': {'show' :  False },
            'series': [
                {
                    'type' : 'bar',
                    'data': [{'name': score['seed'], 'value': score['score'], 'date': score['date']} for score in gameScores],
                    'name' : 'Score',
                    'color': app.storage.user.get('color')
                }
            ]
            })

            avgScore = 0
            bestScore = -1
            prevDate = ""
            streak = 0
            for gs in gameScores:
                if(gs['seed'] == 'daily'):
                    gameDate = datetime.datetime.strptime(gs['date'], '%d/%m/%y')
                    if(prevDate == ""):
                        prevDate = gameDate
                        streak = 1
                    elif(prevDate != gameDate):
                        if((gameDate - prevDate).days == 1):
                            streak +=1
                        else:
                            streak = 0
                    prevDate = gameDate
                    
                avgScore += gs['score']
                bestScore = max(bestScore, gs['score'])
                

            numGameScore = len(gameScores) if(len(gameScores)) != 0 else 1
            avgScore = round(avgScore / numGameScore, 2)

            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Average chain length')
                ui.label(avgScore).style(f'color: {TEXT_SECONDARY}')

            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Shortest chain length')
                ui.label(bestScore).style(f'color: {TEXT_SECONDARY}')

            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Daily streak')   
                ui.label(streak).style(f'color: {TEXT_SECONDARY}')
            
            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Games played')   
                ui.label(gamesPlayed).style(f'color: {TEXT_SECONDARY}')
            
        else:
            ui.markdown('**No data yet!**').classes('absolute-center')

    @ui.refreshable
    def WinDialogElements(dialog: ui.dialog):
        wordChain = app.storage.tab.get('word-chain')
        givenUp = app.storage.tab.get('given-up')
        numHints = app.storage.tab.get('num-hints')
        terminalWords = app.storage.tab.get('terminal-words')

        #store parameters
        #set all parameters
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_emoji_events' if not givenUp else 'sym_r_flag', size="150%", color=TEXT_PRIMARY)
            ui.label("You won!" if not givenUp else "Gave up!").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")

        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.chip(f"{len(wordChain)-1} links", icon='sym_r_link')

            ui.chip(f"{numHints} hint" + ('s' if numHints != 1 else ''), icon='sym_r_lightbulb')

        with ui.scroll_area().style(f'border-color: {BORDER_COLOR}; border-radius: {BORDER_RADIUS}; border-width: 1px; width: 90%').classes('h-full') as scrollArea:
            with ui.timeline(side='right', layout='dense').classes('gap-0 p-0 h-full'):
                for i, w in enumerate(wordChain):
                    GameLogic.WordSim(w, terminalWords[1], 3)
                    ui.timeline_entry("",subtitle=w).style('height: 4rem').classes('p-0')
                scrollArea.scroll_to(percent=100, duration=1)

        with ui.row().style('width: 100%; height: 10%').classes('justify-center'):
            ui.button(icon='sym_r_all_inclusive', on_click=lambda e: (dialog.close(), PracticeBtn()))
            ui.button(icon='sym_r_ios_share', on_click=lambda e: CopyClipboardGame())
    
    

        

    @ui.refreshable
    def WordChain(fadeIn: bool = True):
        terminalWords = app.storage.tab.get('terminal-words')
        wordChain = app.storage.tab.get('word-chain')
        color = app.storage.user.get('color')

        #create a card for each word
        with ui.column().classes("w-full gap-2"):
            for i, word in enumerate(wordChain):
                chainMessage = f"({GameLogic.WordSim(word, terminalWords[1], 3)}) to '{terminalWords[1]}'"
                # if(not i == len(GameLogic._WordChain)-1):
                #     chainMessage = f"({GameLogic.WordSim(word, GameLogic._WordChain[i+1], 3)})"
                appendStyle = "" if i != len(wordChain) - 1 or not fadeIn  else "; animation: fade 0.3s"
                
                tglBtn = ToggleButton(linkedId=word, col1=DARK, col2=color).style(f"width: 100%; {BORDER_SETTINGS}" + appendStyle).classes(f'custom-button-content')
                tglBtn.on_click(lambda e, wordPass = word, tb=tglBtn: ClickToggleButton(wordPass, tb))
                tglBtns = app.storage.client.get('toggle-btns')
                tglBtns.append(tglBtn) #register button
                app.storage.client['toggle-btns'] = tglBtns
                with tglBtn:
                    with ui.row().style('width: 100%').classes('gap-4 h-full items-center justify-start text-left'):
                        ui.label(f'{i+1}').style(f'color: {TEXT_SECONDARY}')
                        ui.label(word).style(f'font-weight: normal; color: {TEXT_PRIMARY}')
                        ui.label(f'{chainMessage}').style(f'color: {TEXT_SECONDARY}').classes('ml-auto')

        
        ui.element().style("height: 8rem").classes('w-full')
        
    @ui.refreshable 
    def TerminalCards():
        terminalWords = app.storage.tab.get('terminal-words')
        color = app.storage.user.get('color')

        #create cards for start and target
        with ui.row().classes('gap-0 items-center justify-between w-full'):
            start = ToggleButton(linkedId=terminalWords[0], label=terminalWords[0], col1=DARK, col2=color, on_click= lambda e:ClickToggleButton(terminalWords[0], start)).style(BORDER_SETTINGS+"; width: 40%")
            ui.icon("sym_r_keyboard_double_arrow_right", size="2rem", color=BORDER_COLOR)
            end = ToggleButton(linkedId=terminalWords[1], label=terminalWords[1], col1=DARK, col2=color, on_click= lambda e: ClickToggleButton(terminalWords[1], end)).style(BORDER_SETTINGS+"; width: 40%")
            tglBtns = app.storage.client.get('toggle-btns')
            tglBtns.append(start) #register button
            tglBtns.append(end) #register button
            app.storage.client['toggle-btns'] = tglBtns

    @ui.refreshable
    def DictionaryText():
        word = app.storage.client.get('selected-word')
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
    def HeaderRow(dialogs: dict):
        mode = app.storage.tab.get('mode')
        icon = 'sym_r_today' if mode == 'daily' else 'sym_r_all_inclusive'

        with ui.row().style(f'height: {HEADER_HEIGHT}').classes('justify-between items-center w-full'):
            with ui.row().classes('justify-start').style('width: 30%'):
                with ui.dropdown_button().props(f'dropdown-icon={icon} no-icon-animation transition-show=jump-down transition-hide=jump-up') as dropdownButton:
                    with ui.item(on_click= lambda e: ChangeMode('daily')) as specialItem:
                        specialItem.on_click(lambda e: dropdownButton.close())
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_today', color=TEXT_PRIMARY, size='125%')
                            ui.label("Daily").style(f"color: {TEXT_PRIMARY}")
                    with ui.item(on_click= lambda e: ChangeMode('practice')) as specialItem:
                        specialItem.on_click(lambda e: dropdownButton.close())
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_all_inclusive', color=TEXT_PRIMARY, size='125%')
                            ui.label("Practice").style(f"color: {TEXT_PRIMARY}")
                ui.button(icon='sym_r_undo', on_click=lambda e: UndoBtn()).style('width: 10%')

                # ui.button(icon='sym_r_add_circle', on_click=lambda e: RestartBtn()).style('width: 10%')

            ui.label(f'{GAME_NAME}').style(f'color: {TEXT_PRIMARY}; font-size: 200%; font-weight: bold').classes('absolute-center')
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
                    with ui.item(on_click=lambda e: (dialogs['stats'].open(), dropdownButton.close())):
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_bar_chart', color=TEXT_PRIMARY, size='125%')
                            ui.label("Stats").style(f"color: {TEXT_PRIMARY}")
                    with ui.item(on_click=lambda e: (dialogs['settings'].open(), dropdownButton.close())):
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_build', color=TEXT_PRIMARY, size='125%')
                            ui.label("Settings").style(f"color: {TEXT_PRIMARY}")
                ui.button(icon='sym_r_info', on_click=lambda e: dialogs['info'].open()).style('width: 10%')

    random.seed(_Seed)

    #initialize user storage
    if(app.storage.user.get('color') == None):
        app.storage.user['color'] = PRIMARY
    if(app.storage.user.get('game-scores') == None):
        app.storage.user['game-scores'] = []
    if(app.storage.user.get('games-played') == None):
        app.storage.user['games-played'] = 0
    

    await ui.context.client.connected()
    #inject custom html
    CustomHTMTL()

    #define temporary game variables (marked with an '_')
    if(_Seed!='daily'):
        _StartWord, _TargetWord = GameLogic.GenerateStartEndWords(minDistance=0.5)
    else:
        terminals = GameLogic._DailyData[str(datetime.datetime.now().date())].split(', ')
        _StartWord, _TargetWord = (terminals[0], terminals[1])
    #storage temp vars
    app.storage.tab['seed'] = _Seed
    app.storage.tab['terminal-words'] = [_StartWord, _TargetWord] #store start and end words for optimisation
    app.storage.tab['word-chain'] = [_StartWord] #store a chain of words in the tab
    app.storage.tab['num-hints'] = 0 #store a number tracking hints in the tab
    app.storage.tab['given-up'] = False #store a boolean for given up in the tab
    app.storage.tab['mode'] = 'daily' #store a string for the users mode
    app.storage.client['toggle-btns'] = []
    app.storage.client['selected-word'] = ''

    #DEBUG
    # print(f"""
    # {app.storage.tab.get('terminal-words')},
    # {app.storage.tab.get('word-chain')},
    # {app.storage.tab.get('num-hints')},
    # {app.storage.tab.get('given-up')},
    # """)

    #global setup - dialogs
    _Dialogs = {}
    #stats dialog setup

    #stat dialog only
    _Dialogs['stats'] = ui.dialog()
    statRadio = None
    with _Dialogs['stats'], OverlayCard().classes('justify-start items-center gap-0'):
        StatsDialogElements()

    #stat dialog combined with win dialog
    _Dialogs['stats-win'] = ui.dialog().props('transition-hide=fade transition-show=fade').style('backdrop-filter: none').classes('no-backdrop-dialog')
    statRadio = None
    with _Dialogs['stats-win'], OverlayCard().classes('justify-start items-center gap-0'):
        StatsDialogElements()
        statRadio = ui.radio([' ', ''], value=' ', on_change= lambda e: _Dialogs['stats-win'].close()).props('inline size=xs')

    #winning dialogue setup
    _Dialogs['win'] = ui.dialog()
    with _Dialogs['win'] as dialog, OverlayCard():
        WinDialogElements(dialog)
        ui.radio([' ', ''], value=' ', on_change= lambda e: _Dialogs['stats-win'].open()).props('inline size=xs').bind_value(statRadio, 'value')

    #info dialogue setup
    _Dialogs['info'] = ui.dialog()
    with _Dialogs['info'], OverlayCard():

        descriptionCSS = f'color: #AAAAAA; font-style: normal; font-size: 90%'
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_info', size="150%", color=TEXT_PRIMARY)
            ui.label("Info").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")
        with ui.expansion(text="How do I play?", icon='sym_r_help_outline').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""Your goal is to create a chain of related words to reach a 'target' word. 
                        Start and ending words are determined randomly, and links must have a maximum
                        similarity of {GameLogic.DISTANCE_CUTOFF} from the previous.""").style(descriptionCSS)
        with ui.expansion(text='How are word similarities determined?', icon='sym_r_help_outline').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""{GAME_NAME} queries a database of over 70000 words that each have a corresponding vector. These vectors
                        are tweaked through NLP models. A euclidean distance operation between two word vectors returns the similarity.
                        Since similarity is based upon similar contexts, it doesn't necessarily translate to similar meaning.""").style(descriptionCSS)
        with ui.expansion(text=f'Who created {GAME_NAME}?', icon='sym_r_help_outline').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""Hudson Woolford programmed {GAME_NAME} in python for a Computer Science project at his school.""").style(descriptionCSS)
            ui.label("""Ted Boss acted as a playtester and provided valuable feedback throughout development""").style(descriptionCSS + f'; color: {TEXT_SECONDARY}')
        with ui.expansion(text='Have you made any other products?', icon='sym_r_help_outline').style(f"color: {TEXT_PRIMARY}; width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label("""Hudson Woolford was a developer on Swingularity, an indie space golf game. Check it out!""").style(descriptionCSS)
            ui.link(text="Swingularity on STEAM", target="https://store.steampowered.com/app/3272450/Swingularity/", new_tab=True).style(descriptionCSS)

    #settings tools dialog
    _Dialogs['settings'] = ui.dialog()
    with _Dialogs['settings'], OverlayCard().style('height: 26.5rem').classes('gap-3 justify-start !important items-between'):
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_build', size="150%", color=TEXT_PRIMARY)
            ui.label("Settings").style(f"color: {TEXT_PRIMARY}; font-weight: bold; font-size: 150%")
        picker = ui.element('q-color').props('default-view=palette no-header no-footer').classes('w-full')
        picker.on('update:model-value', lambda color: ChangeSiteColor(color.args))
        # picker.q_color.props('default-view=palette no-header no-footer')
        
        ui.button(icon='sym_r_delete', text='Clear Data', on_click= lambda e: ClearUserData()).classes('justify-center w-full')

    
    app.storage.client['dialogs'] = _Dialogs

    #header
    with ui.header().style(f'background-color: {DARK}').style(f'font-size: 24; height: {HEADER_HEIGHT}').classes('py-0 w-screen font-weight-bold'):
        HeaderRow(_Dialogs)

    with ui.column().style(f'width: {GAME_WIDTH}; justify-content: center; padding-top: 1rem').classes('h-full absolute-center'):
        with ui.row().classes('justify-center items-center w-full'):
            ui.chip(f"Chain similar words to get to the target",icon="sym_r_link").props("outlined")


        #show start and target
        TerminalCards()
        
        inputWordBox = ui.input(placeholder="chain a word..."
                            ).props(f'autocomplete=off; autocapitalize=off; input-style="color: {BORDER_COLOR}"; autofocus'
                            ).classes(f' gap-0 items-center w-full')
        inputWordBox.on('keydown', lambda e: GuessInput(inputWordBox.value) if e.args['key'] == "Enter" else None)
        def OnEnterWord():
            inputWordBox.value = ""
            ui.run_javascript(f"document.getElementById('{inputWordBox.id}').focus()")
        inputWordBox.on('keydown', lambda e: OnEnterWord() if e.args['key'] == "Enter" else None)
    

        #word chain scroll area
        with ui.element().classes("h-screen w-full"):
            with ui.scroll_area().style(f"height: 60%; border-color: {BORDER_COLOR}; border-width: 1px; border-radius: {BORDER_RADIUS}").classes(f'rounded w-full') as scrollArea:
                WordChain(scrollArea)
                inputWordBox.on('keydown', lambda e: scrollArea.scroll_to(percent=100, axis='vertical', duration=0.5) if e.args['key'] == "Enter" else None)
            ui.element('div').classes('my-4')
            DictionaryText()

@ui.page('/practice/{_Seed}')
async def SeedPage(_Seed: str):
    await GamePage(_Seed, 'practice')
    

@ui.page('/')
def HomePage():
    #redirect to daily / random game
    ui.navigate.to('/daily')



""" 
-------------------------------------------------------------------------------

START OF AUTO-INDEX OR LOGIC

-------------------------------------------------------------------------------
"""
ui.run(
    reload=False,
    title=f"{GAME_NAME}",
    show=False,
    storage_secret='SWINGULARITY',
    favicon='<svg xmlns="http://www.w3.org/2000/svg" enable-background="new 0 0 24 24" height="24px" viewBox="0 0 24 24" width="24px" fill="#e3e3e3"><g><rect fill="none" height="24" width="24"/></g><g><path d="M15,16v1.26l-6-3v-3.17L11.7,8H16V2h-6v4.9L7.3,10H3v6h5l7,3.5V22h6v-6H15z M12,4h2v2h-2V4z M7,14H5v-2h2V14z M19,20h-2v-2 h2V20z"/></g></svg>' #figure out how to scale this correctly
)

