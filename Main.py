from nicegui import ui, app
import GameLogic
import WordManager as wm
from CustomUI import ToggleButton
from CustomUI import ToggleButtonManager
import Dictionary as WordDictionary
import asyncio
import random
import FileManager
import datetime
import os
import math
import ValueRemapping

#region PARAMETERS
#Colors

#light mode (L_[color-description])
L_BACKGROUND = '#f7f4ea' #floral white
L_ELEMENT = '#e7e4da' #floral white
L_TEXT = 'black'
L_TEXT_SECONDARY = 'grey'
L_BORDER = 'black'
L_SCHEMES = [
    '#b2b2b2', '#cdcdcd',
    '#ffccff','#ccccff', '#cce6ff', '#ccffff', '#ccffcc', '#ffffcc', '#ffe6cc', '#ffcccc',
]

#dark mode (D_[color-description])
D_BACKGROUND = '#121212' #floral white
D_ELEMENT = '#1d1d1d' #ivory
D_TEXT = 'white'
D_TEXT_SECONDARY = 'grey'
D_BORDER = 'white'
D_SCHEMES = [
    '#191919', '#333333',
    '#5c005c', '#2e005c', '#002e5c', '#005c5c', '#005c00', '#5c5c00', '#5c2e00', '#5c0000',
]

#constant colors
PRIMARY = '#005c2e'
POSITIVE = '#21ba45'
NEGATIVE = '#c10015'
INFO = '#31ccec'
WARNING = '#f2c037'

#width and radius
BORDER_WIDTH = '0px'
BORDER_RADIUS = '10px'
GAME_WIDTH= '24rem'
HEADER_HEIGHT = '4rem'

#other
GAME_NAME = "Linkonym"
BORDER_SETTINGS = f'border-color: {D_BORDER}; border-width: {BORDER_WIDTH}; border-radius: {BORDER_RADIUS}'
NUM_DEFINITIONS = 2
MAX_TRACK_GAMES = 50
PORT = 8000

#other globals (not constant)
_WebRandom = random.Random()
#endregion

#region PAGES
#stat page
@ui.page('/pistats')
def PiStatsPage():
    ui.markdown(f"""
{os.popen('vcgencmd measure_temp').readline()}
{os.popen("df -h /").read()}
{os.popen('free').read()}
{os.popen('uptime').readline()}
""")

#root page
@ui.page('/')
def RootPage():
    HeaderHTML()
    ui.navigate.to('/daily')

#daily game page
@ui.page('/daily')
async def DailyPage():
    await GamePage('daily', mode='daily')

#random game page
@ui.page('/random/{seed}')
async def DailyPage(seed: str):
    await GamePage(seed, mode='random')

#shared game page for rendering everything
async def GamePage(seed: str, mode: str = 'daily'):
#endregion

    #region REFRESHABLES
    def RefreshAll():
        """
        Used to refresh all elements, typically during site-wide colour changes
        """
        HeaderRow.refresh()
        StatsElements.refresh()
        WinElements.refresh()
        TerminalCards.refresh()
        WordChain.refresh(False)
        DictionaryText.refresh()

    @ui.refreshable
    def HeaderRow():
        """
        Creates all the objects seen in the website header. Should be a child of a header element.
        """

        dialogs = app.storage.client.get('dialogs')
        mobile = app.storage.client.get('mobile')
        modeIcon = 'sym_r_today' if mode == 'daily' else 'sym_r_all_inclusive'

        buttonWidth = '2rem' if mobile else '3rem'
        #row for the entire header
        with ui.row().style(f'height: {HEADER_HEIGHT}').classes('justify-between items-center w-full'):
            #first 30%
            with ui.row().classes('justify-start').style('width: 30%'):
                with ui.dropdown_button().props(f'dropdown-icon={modeIcon} no-icon-animation transition-show=jump-down transition-hide=jump-up').style(f'width: {buttonWidth}; color: var(--q-text) !important;') as dropdownButton:
                    with ui.item(on_click=lambda: ChangeMode('daily')).style('background-color: var(--q-element)') as specialItem:
                        specialItem.on_click(lambda: dropdownButton.close())
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_today', size='125%').style(f"color: var(--q-text)")
                            ui.label("Daily").style(f"color: var(--q-text)")
                    with ui.item(on_click= lambda: ChangeMode('random')).style('background-color: var(--q-element)') as specialItem:
                        specialItem.on_click(lambda: dropdownButton.close())
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_all_inclusive', size='125%').style(f"color: var(--q-text)")
                            ui.label("Random").style(f"color: var(--q-text)")
                ui.button(icon='sym_r_undo', on_click=lambda: (RemoveLastLink(), WordChain.refresh(False))).style(f'width: {buttonWidth}; color: var(--q-text) !important;')

                # ui.button(icon='sym_r_add_circle', on_click=lambda e: RestartBtn()).style('width: 10%')

            #game name
            ui.label(f'{GAME_NAME}').style(f'color: var(--q-text); font-family: "Righteous"; font-size: {"200%" if mobile else "250%"};').classes('absolute-center')

            async def HintLocal():
                await Hint(WordChain.refresh)
            async def GiveUpLocal():
                await GiveUp(WordChain.refresh)

            #last 30%
            with ui.row().classes('justify-end').style('width: 30%'):
                with ui.dropdown_button().props('dropdown-icon=sym_r_more_vert no-icon-animation transition-show=jump-down transition-hide=jump-up text-color=var(--q-text)').style(f'width: {buttonWidth}; color: var(--q-text) !important;') as dropdownButton:
                    with ui.item(on_click=HintLocal).style('background-color: var(--q-element)') as specialHintItem:
                        specialHintItem.on_click(lambda: dropdownButton.close())
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_lightbulb', size='125%').style(f"color: var(--q-text)")
                            ui.label("Hint").style(f"color: var(--q-text)")
                    with ui.item(on_click=GiveUpLocal).style('background-color: var(--q-element)') as specialGiveUpItem:
                        specialGiveUpItem.on_click(lambda: dropdownButton.close())
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_flag', size='125%').style(f"color: var(--q-text)")
                            ui.label("Give up").style(f"color: var(--q-text)")
                    with ui.item(on_click=lambda: (dialogs['stats'].open(), dropdownButton.close())).style('background-color: var(--q-element)'):
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_bar_chart', size='125%').style(f"color: var(--q-text)")
                            ui.label("Stats").style(f"color: var(--q-text)")
                    with ui.item(on_click=lambda: (dialogs['settings'].open(), dropdownButton.close())).style('background-color: var(--q-element)'):
                        with ui.row().classes('justify-center items-center gap-1.5'):
                            ui.icon('sym_r_build', size='125%').style(f"color: var(--q-text)")
                            ui.label("Settings").style(f"color: var(--q-text)")
                ui.button(icon='sym_r_info', on_click=lambda: dialogs['info'].open()).style(f'width: {buttonWidth}; color: var(--q-text) !important;')
    
    @ui.refreshable
    def StatsElements():
        """
        Creates all the elements found in the stats dialog. Should be a child of the dialog element.
        """

        gameScores: list = app.storage.user.get('game-scores')
        gamesPlayed: int = app.storage.user.get('games-played')
        with ui.row().classes('justify-center items-center gap-1.5'):
                ui.icon('sym_r_bar_chart', size="150%").style(f"color: var(--q-text)")
                ui.label("Stats").style(f"color: var(--q-text); font-weight: bold; font-size: 150%")

        if(len(gameScores) > 0):
            ui.echart({
            'height' : '60%',
            'title': {
                'text': 'Previous scores',  #title text
                'subtext': f'Maxes at {MAX_TRACK_GAMES} games',  #subtitle
                'left': 'center', 
                'top': 'top', 
                'textStyle': {
                    'color': 'var(--q-text)',
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
                    'color': 'var(--q-text-secondary)'
                }
            }, ''
            'interval': 2},
            'legend': {'show' :  False },
            'series': [
                {
                    'type' : 'bar',
                    'data': [{'name': score['seed'], 'value': score['score'], 'date': score['date']} for score in gameScores],
                    'name' : 'Score',
                    'color': CurrentColorScheme()[app.storage.user.get('color-index')]
                }
            ]
            })

            avgScore = 0
            bestScore = 1000
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
                bestScore = min(bestScore, gs['score'])
                

            numGameScore = len(gameScores) if(len(gameScores)) != 0 else 1
            avgScore = round(avgScore / numGameScore, 2)

            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Average chain length').style(f"color: var(--q-text)")
                ui.label(avgScore).style(f'color: var(--q-text-secondary)')

            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Shortest chain length').style(f"color: var(--q-text)")
                ui.label(bestScore).style(f'color: var(--q-text-secondary)')

            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Daily streak').style(f"color: var(--q-text)")   
                ui.label(streak).style(f'color: var(--q-text-secondary)')
            
            with ui.row().classes('w-full justify-between items-center'):
                ui.markdown(f'Games played').style(f"color: var(--q-text)")   
                ui.label(gamesPlayed).style(f'color: var(--q-text-secondary)')
            
        else:
            ui.markdown('**No data yet!**').classes('absolute-center').style(f"color: var(--q-text)")
    
    @ui.refreshable
    def WinElements():
        """
        Creates all the elements for the win dialog. Should be a child of a dialog element.
        """

        wordChain = app.storage.tab.get('word-chain')
        givenUp = app.storage.tab.get('given-up')
        numHints = app.storage.tab.get('num-hints')
        terminalWords = app.storage.tab.get('terminal-words')

        #store parameters
        #set all parameters
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_emoji_events' if not givenUp else 'sym_r_flag', size="150%").style(f"color: var(--q-text)")
            ui.label("You won!" if not givenUp else "Gave up!").style(f"color: var(--q-text); font-weight: bold; font-size: 150%")

        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.chip(f"{len(wordChain)-1} links", icon='sym_r_link')

            ui.chip(f"{numHints} hint" + ('s' if numHints != 1 else ''), icon='sym_r_lightbulb')

        with ui.scroll_area().style(f'border-color: var(--q-border); border-radius: {BORDER_RADIUS}; border-width: 1px; width: 90%').classes('h-full') as scrollArea:
            with ui.timeline(side='right', layout='dense').classes('gap-0 p-0 h-full'):
                for i, w in enumerate(wordChain):
                    wm.WordSim(w, terminalWords[1], 3)
                    ui.timeline_entry("",subtitle=w).style('height: 4rem').classes('p-0')
                scrollArea.scroll_to(percent=0)
                ui.run_javascript(f"getElement('{scrollArea.id}').setScrollPercentage('vertical', 1, 750)")

        with ui.row().style('width: 100%; height: 10%').classes('justify-center'):
            ui.button(icon='sym_r_add_circle', on_click=lambda e: (ui.navigate.to(f'/random/{_WebRandom.randint(0, 50000000)}'))).style('color: var(--q-text) !important;')
            ui.button(icon='sym_r_ios_share', on_click=lambda e: CopyClipboardGame()).style('color: var(--q-text) !important;')
    
    @ui.refreshable 
    def TerminalCards():
        """
        Creates the start and target cards (terminals)
        """

        terminalWords = app.storage.tab.get('terminal-words')

        #create cards for start and target
        with ui.row().classes('gap-0 items-center justify-between w-full'):
            start = ToggleButton(linkedId=terminalWords[0], label=terminalWords[0], col1='element', col2='primary', on_enable=lambda e: DictionaryText.refresh()).style(BORDER_SETTINGS+"; width: 40%")
            ui.icon("sym_r_keyboard_double_arrow_right", size="2rem", color='element')
            end = ToggleButton(linkedId=terminalWords[1], label=terminalWords[1], col1='element', col2='primary', on_enable=lambda e: DictionaryText.refresh()).style(BORDER_SETTINGS+"; width: 40%")
            RegisterTglBtn(start)
            RegisterTglBtn(end)
    
    @ui.refreshable
    def WordChain(fadeIn: bool = True):
        """
        Creates the elements for the word chain. Should be a child of a scroll area.
            Also calls win game if target word is the last word
        """
        
        terminalWords = app.storage.tab.get('terminal-words')
        wordChain = app.storage.tab.get('word-chain')

        #create a card for each word
        with ui.column().classes("w-full gap-2"):
            for i, word in enumerate(wordChain):
                dist = ValueRemapping.BezierApproximation(wm.WordSim(word, terminalWords[1], 3))
                appendStyle = "" if i != len(wordChain) - 1 or not fadeIn  else "; animation: fade 0.3s"
                
                tglBtn = ToggleButton(linkedId=word, col1='element', col2='primary', on_enable=lambda e: DictionaryText.refresh()).style(f"width: 100%; {BORDER_SETTINGS}" + appendStyle).classes(f'custom-button-content')
                RegisterTglBtn(tglBtn)
                with tglBtn:
                    with ui.row().style('width: 100%').classes('gap-4 h-full items-center justify-start text-left'):
                        ui.label(f'{i+1}').style(f'color: var(--q-text-secondary)')
                        ui.label(word).style(f'font-weight: normal; color: var(--q-text)')

                        with ui.element('div').style('position: relative; width: 30%; height: 50%;').classes('ml-auto'):
                            lightness = '100%' if app.storage.user['dark-mode'] else '-100%'
                            with ui.linear_progress(value=dist, show_value=False).props('rounded').style(f'width: 100%; height: 100%; color: {"primary" if dist > GameLogic.SIM_CUTOFF else f"hsla(0,0%,{lightness},.5)"} !important'):
                                #visualize cutoff
                                 ui.element('div').classes('q-linear-progress__model absolute-full q-linear-progress__model--with-transition q-linear-progress__model--determinate').style(f'transform: scale3d({GameLogic.SIM_CUTOFF},1,1); color: hsla(0, 0%, {lightness}, 0.1) !important')
                            ui.badge(f'{math.floor(dist*100)}%').style(
                                f'position: absolute; top: 0; left: 0; transform: translate(-30%, -35%); z-index: 1; color: var(--q-text);'
                            )
                            
                
                if(word == terminalWords[1]):
                    WinGame(StatsElements.refresh, WinElements.refresh)

        
        ui.element().style("height: 8rem").classes('w-full')
    
    @ui.refreshable
    def DictionaryText():
        word = app.storage.client.get('selected-word')
        if(word != None and word != ''):
            ui.separator().style(f'background-color: var(--q-border); animation: fade 0.5s')            
            ui.element('div').classes('my-2')

            #retrieve definition
            definitionNotFound = False
            definitions = WordDictionary.getRecordsAdvanced(word)
            if(definitions == None or len(definitions.keys())==0): 
                word = wm._WordData['vocab'][word]['lemma']
                definitions = WordDictionary.getRecordsAdvanced(word)

            if(definitions == None or len(definitions.keys())==0):
                definitionNotFound = True
                definitions = {
                    'definition_1' : f'https://www.google.com/search?q=define%20{word} to find the meaning',
                    'pos_1' : 'No available definition'
                }
            
            #dictionary entry
            ui.label(word).style(f'font-size: 250%; font-weight: bold; color: var(--q-text); text-align: left; animation: fade 1s')
            total = min(NUM_DEFINITIONS, sum(1 for key in definitions if key.startswith("definition_")))
            for i in range(1, total+1):
                ui.element('div').classes('my-2')
                ui.label(f"{i}. {definitions[f'pos_{i}']}").style(f'color:  var(--q-text); text-align: left; animation: fade 1s').classes('text-italic')
                ui.element('div').classes('my-2')

                if(not definitionNotFound):
                    ui.label(definitions[f'definition_{i}']).style(f' color:  var(--q-text); text-align: left; animation: fade 1s')
                else:
                    ui.link(text = f"Please visit https://www.google.com/search?q=define%20{word} for the meaning", target=f'https://www.google.com/search?q=define%20{word}', new_tab=True).style(f' color: var(--q-text); text-align: left; animation: fade 1s')
            
            ui.element('div').classes('my-4')
            ui.separator().style(f'background-color:  var(--q-border); animation: fade 0.5s')
    #endregion

    #region INITIALIZATION
    await ui.context.client.connected()
    userAgent = ui.context.client.request.headers['user-agent']
    mobile = 'iPhone' in userAgent or 'Android' in userAgent

    random.seed(seed)
    startWord, targetWord = GetStartEndWords(seed, mode)

    InitializeStorage(seed, startWord, targetWord, mobile, refreshAll=RefreshAll) #initialize all storage variables
    HeaderHTML() #inject custom html to header
    dialogs = CreateDialogs(StatsElements, WinElements) #get dialogs
    app.storage.client['dialogs'] = dialogs #store dialogs

    #endregion
    #region ELEMENTS
    
    #header
    with ui.header().style(f'background-color: var(--q-element)').style(f'font-size: 24; height: {HEADER_HEIGHT}').classes('py-0 w-screen font-weight-bold'):
        HeaderRow()

    #main game column
    gameWidth = '22rem' if mobile else GAME_WIDTH
    with ui.column().style(f'width: {gameWidth}; padding-top: 1rem').classes('h-screen items-center mx-auto'):
        with ui.row().classes('justify-center items-center w-full'):
            ui.chip(f"Chain similar words to get to the target",icon="sym_r_link").props("outlined")


        #show start and target
        TerminalCards()
        
        inputWordBox = ui.input(placeholder="chain a word..."
                            ).props(f'autocomplete=off; autocapitalize=off; input-style="color: var(--q-border)"; autofocus'
                            ).classes(f' gap-0 items-center w-full')

        #word chain scroll area
        scrollArea = None
        with ui.scroll_area().style(f"height: 40%; border-color: var(--q-border); border-width: 1px; border-radius: {BORDER_RADIUS}; scroll-behaviour: smooth").classes(f'rounded w-full') as sa:

            scrollArea = sa
            WordChain(False)

        with ui.element().style('height: 30%').classes('justify-start w-full'):
            DictionaryText()

        #wrapper function for what happens when the user enters a word
        def OnEnterWord(wordBox: ui.input):
            GuessInput(wordBox.value, WordChain.refresh)
            if(app.storage.tab.get('won')):
                wordBox.props('disable')
                app.storage.tab['seed'] = None #THIS IS TEMPORARY TO MAKE IT SO THAT RELOADING ON A WIN RESETS 
            wordBox.value = ""
            ui.run_javascript(f"getElement('{wordBox.id}').focus()")
            ui.run_javascript(f"getElement('{scrollArea.id}').setScrollPercentage('vertical', 1, 400)")
            scrollArea.scroll_to(percent=100, axis='vertical')


        inputWordBox.on('keydown', lambda e: OnEnterWord(inputWordBox) if e.args['key'] == "Enter" else None) #call wrapper if key is enter

    
    #endregion

#region UTILITY
def HeaderHTML():
    """
    Add custom head html for global custom classes, font-sizes, etc
        Requires site color and dark mode storage to be set
    """
    siteColor = CurrentColorScheme()[app.storage.user.get('color-index')]
    
    #Important stuff
    ui.add_head_html("""
    <!-- Light mode favicon (dark icon) -->
    <link rel="icon" type="image/svg+xml" media="(prefers-color-scheme: light)" href='data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" height="24" width="24" fill="%23111"><path d="M15,16v1.26l-6-3v-3.17L11.7,8H16V2h-6v4.9L7.3,10H3v6h5l7,3.5V22h6v-6H15z M12,4h2v2h-2V4z M7,14H5v-2h2V14z M19,20h-2v-2 h2V20z"/></svg>'>
    <!-- Dark mode favicon (light icon) -->
    <link rel="icon" type="image/svg+xml" media="(prefers-color-scheme: dark)" href='data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" height="24" width="24" fill="%23e3e3e3"><path d="M15,16v1.26l-6-3v-3.17L11.7,8H16V2h-6v4.9L7.3,10H3v6h5l7,3.5V22h6v-6H15z M12,4h2v2h-2V4z M7,14H5v-2h2V14z M19,20h-2v-2 h2V20z"/></svg>'>
    """)
    ui.add_head_html('<link rel="canonical" href="https://linkonym.com/daily">')
    ui.add_head_html('<meta name="description" content="Linkonym is a word game where you chain similar words together to reach a target word.">')

    #Global site colors
    def ModeRefresh():
        ui.colors(primary=CurrentColorScheme()[app.storage.user.get('color-index')])
        app.storage.client.get('refresh-all')()

    ui.colors(primary=siteColor, positive=POSITIVE, negative=NEGATIVE, info=INFO, warning=WARNING)
    darkMode = ui.dark_mode().bind_value_from(app.storage.user, 'dark-mode')
    darkMode.on_value_change(lambda: ModeRefresh())
    ui.add_head_html('''
    <style>
        .body--light{''' + f"""
            background: {L_BACKGROUND};
            --q-element: {L_ELEMENT};
            --q-border: {L_BORDER};
            --q-text: {L_TEXT};
            --q-text-secondary: {L_TEXT_SECONDARY};
            """ +
        '''
        }             
    ''') #light mode
    ui.add_head_html('''
    <style>
        .body--dark{''' + f"""
            --q-background: {D_BACKGROUND};
            --q-element: {D_ELEMENT};
            --q-border: {D_BORDER};
            --q-text: {D_TEXT};
            --q-text-secondary: {D_TEXT_SECONDARY};
            """ +
        '''
        }             
    ''') #dark mode


    #Fade animation
    ui.add_head_html('''
    <style>
    @keyframes fade {from {opacity: 0;} to {opacity: 1.0;}}
    </style>
    ''')
    
    #Hidden scrollbar custom class
    ui.add_head_html('''
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
    ''')
    
    #Custom button content for max width
    ui.add_head_html('''
    <style>
    .custom-button-content .q-btn__content {
        width: 100% !important;
        padding: 0 !important;
        display: flex !important;
        align-items: stretch !important;
    }
    </style>
    ''')

    #Dialog without backdrop class
    ui.add_head_html('''
    <style>
    .no-backdrop-dialog .q-dialog__backdrop{
        background: rgba(0,0,0,0) !important;
    }
    </style>
    ''')

    #Site selection color / highlight color
    ui.add_head_html('''
    <style>
    :root {
    --selection-color:''' + siteColor + ''';
    }
    ::selection {
    background: var(--selection-color);
    }
    </style>
    ''') 
    
    #16px global font size - Cutoff for phone not auto zooming in
    ui.add_head_html("""
    <style>
        body {
            font-size: 16px; !important
        }
        .q-btn, .q-label, .q-input, .q-chip{
            font-size: 16px; !important
        }
    </style>
    """)

    #Site scrolling
    ui.add_head_html("""
    <style>
        body {
            overflow-y: auto;  /* Ensures vertical scrolling */
        }
    </style>
    """)

    #Custom font
    ui.add_head_html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Righteous&display=swap');
    .righteous-regular {
        font-family: "Righteous", sans-serif;
        font-weight: 400;
        font-style: normal;
    }
    """)

def OverlayCard() -> ui.card:
    """
    Creates an overlay card with global settings, useful for dialogs like win, stats, settings etc
    """
    
    return ui.card().style(f'{BORDER_SETTINGS}; width: 20rem; height: 28rem; background-color: var(--q-element) !important').classes(f'hidden-scroll no-shadow items-center hidden-scrollbar')

def CreateDialogs(statElementsF, winElementsF) -> dict:
    """
    Creates all the dialogs and stores them in a dictionary
    """

    dialogs = {}

    #stat dialog only
    dialogs['stats'] = ui.dialog()
    statRadio = None
    with dialogs['stats'], OverlayCard().classes('justify-start items-center gap-0'):
        statElementsF()

    #stat dialog combined with win dialog
    dialogs['stats-win'] = ui.dialog().props('transition-hide=fade transition-show=fade').style('backdrop-filter: none').classes('no-backdrop-dialog')
    statRadio = None
    with dialogs['stats-win'], OverlayCard().classes('justify-start items-center gap-0'):
        statElementsF()
        statRadio = ui.radio([' ', ''], value=' ', on_change= lambda e: dialogs['stats-win'].close()).props('inline size=xs')

    #winning dialogue setup
    dialogs['win'] = ui.dialog()
    with dialogs['win'] as dialog, OverlayCard():
        winElementsF()
        ui.radio([' ', ''], value=' ', on_change= lambda e: dialogs['stats-win'].open()).props('inline size=xs').bind_value(statRadio, 'value')
    

    #info dialogue setup
    dialogs['info'] = ui.dialog()
    with dialogs['info'], OverlayCard():

        descriptionCSS = f'color: var(--q-text); font-style: normal; font-size: 90%'
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_info', size="150%").style(f"color: var(--q-text)")
            ui.label("Info").style(f"color:  var(--q-text); font-weight: bold; font-size: 150%")
        with ui.expansion(text="How do I play?", icon='sym_r_help_outline').style(f"color:  var(--q-text); width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""Your goal is to create a chain of related words to reach a 'target' word. 
                        Start and ending words are determined randomly, and links must have a minimum
                        similarity of {GameLogic.SIM_CUTOFF} from the previous.""").style(descriptionCSS)
        with ui.expansion(text='How are word similarities determined?', icon='sym_r_help_outline').style(f"color:  var(--q-text); width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""{GAME_NAME} queries a database of over 70000 words that each have a corresponding vector. These vectors
                        are tweaked through NLP models. A euclidean distance operation between two word vectors returns the similarity.
                        Since similarity is based upon similar contexts, it doesn't necessarily translate to similar meaning.""").style(descriptionCSS)
        with ui.expansion(text=f'Who created {GAME_NAME}?', icon='sym_r_help_outline').style(f"color: var(--q-text); width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label(f"""Hudson Woolford programmed {GAME_NAME} in python for a Computer Science project at his school.""").style(descriptionCSS)
            ui.label("""Ted Boss acted as a playtester and provided valuable feedback throughout development""").style(descriptionCSS + f'; color:  var(--q-text-secondary)')
        with ui.expansion(text='Have you made any other products?', icon='sym_r_help_outline').style(f"color:  var(--q-text); width: 100%; font-style: oblique; border-radius: {BORDER_RADIUS}"):
            ui.label("""Hudson Woolford was a developer on Swingularity, an indie space golf game. Check it out!""").style(descriptionCSS)
            ui.link(text="Swingularity on STEAM", target="https://store.steampowered.com/app/3272450/Swingularity/", new_tab=True).style(descriptionCSS)

    #settings tools dialog
    @ui.refreshable
    def ColorPicker():
        picker = ui.element('q-color').props(f'''default-view=palette no-header no-footer :palette="{D_SCHEMES if app.storage.user.get('dark-mode') else L_SCHEMES}"''')
        picker.on('update:model-value', lambda color: ChangeSiteColor(color.args))

    dialogs['settings'] = ui.dialog()
    with dialogs['settings'], OverlayCard().style('height: 26.5rem').classes('gap-3'):
        with ui.row().classes('justify-center items-center gap-1.5'):
            ui.icon('sym_r_build', size="150%").style(f"color: var(--q-text)")
            ui.label("Settings").style(f"color: var(--q-text); font-weight: bold; font-size: 150%")

        with ui.row().classes('justify-between items-center w-full'):
            ui.label('Dark mode').style('color: var(--q-text)')
            ui.switch(on_change=lambda e: (ChangeSiteMode(e.value), ColorPicker.refresh())).bind_value(app.storage.user, 'dark-mode')
        
        with ui.row().classes('justify-between items-center w-full'):
            ui.label('Randomize color').style('color: var(--q-text)')
            ui.switch().bind_value(app.storage.user, 'randomize-color')

        with ui.row().classes('justify-between items-center w-full'):
            ui.label('Color').style('color: var(--q-text)')
            ColorPicker()
    
        ui.button(icon='sym_r_delete', text='Clear Data', on_click= lambda e: ClearUserData()).classes('justify-center w-full').style('color: var(--q-text) !important')

    return dialogs

def InitializeStorage(seed: str, startWord: str, targetWord: str, mobile: bool, refreshAll):
    """
    Initializes all tab, user, and client storage. User storage will not be overwritten, but will be initialized if they don't exist.
    """

    #ensure user storage exists
    if(app.storage.user.get('color-index') == None):
        app.storage.user['color-index'] = 6
    if(app.storage.user.get('randomize-color') == None):
        app.storage.user['randomize-color'] = False
    if(app.storage.user.get('dark-mode') == None):
        app.storage.user['dark-mode'] = True
    if(app.storage.user.get('game-scores') == None):
        app.storage.user['game-scores'] = []
    if(app.storage.user.get('games-played') == None):
        app.storage.user['games-played'] = 0
    
    #randomize color (if selected)
    if(app.storage.user.get('randomize-color')):
        app.storage.user['color-index'] = _WebRandom.randrange(0, len(CurrentColorScheme()))

    #temp tab storage - if needs to be renewed
    if(app.storage.tab.get('seed') != seed):
        app.storage.tab['seed'] = seed
        app.storage.tab['terminal-words'] = [startWord, targetWord] #store start and end words for optimisation
        app.storage.tab['word-chain'] = [startWord] #store a chain of words in the tab
        app.storage.tab['num-hints'] = 0 #store a number tracking hints in the tab
        app.storage.tab['given-up'] = False #store a boolean for given up in the tab
        app.storage.tab['mode'] = 'daily' #store a string for the users mode
        app.storage.tab['won'] = False

    #temp client storage
    app.storage.client['toggle-btns'] = []
    app.storage.client['selected-word'] = ''
    app.storage.client['refresh-all'] = refreshAll
    app.storage.client['mobile'] = mobile

def ChangeMode(mode: str):
    app.storage.tab['mode'] = mode
    if(mode == 'random'):
        ui.navigate.to(f'/random/{_WebRandom.randint(0, 50000000)}')
    elif(mode=='daily'):
        ui.navigate.to('/daily')

def ChangeSiteMode(dark: bool):
    app.storage.user['dark-mode'] = dark

def ChangeSiteColor(color: str):
    """
    Changes the primary color of the site to specified paremeter
    """

    app.storage.user['color-index'] = int(CurrentColorScheme().index(color))
    ui.colors(primary=CurrentColorScheme()[app.storage.user.get('color-index')])
    ui.run_javascript(f'''
    document.documentElement.style.setProperty('--selection-color', '{color}');
    ''')
    ui.notify(f"Changed site color to {color}", timeout=500, position='top' if app.storage.client.get('mobile') else 'bottom')
    app.storage.client.get('refresh-all')() #refresh all elements

def ClearUserData():
    """
    Resets all storage for the user, equivalent to clearing.
    """
    app.storage.user['color-index'] = 6
    app.storage.user['game-scores'] = None
    app.storage.user['games-played'] = None
    app.storage.user['randomize-color'] = None
    app.storage.user['dark-mode'] = None

    ui.navigate.reload()

def RemoveLastLink():
    if(app.storage.tab.get('won')): return #cant modify if already won

    wordChain = app.storage.tab.get('word-chain')
    wordChain = wordChain[:-1] if len(wordChain) > 1 else wordChain
    app.storage.tab['word-chain'] = wordChain

def GetStartEndWords(seed: str, mode: str) -> tuple[str, str]:
    """
    Returns the start and end words for the corresponding seed and mode
    """

    if(mode == 'daily'):
        #daily word retrieval
        terminals = wm._DailyData[str(datetime.datetime.now().date())].split(', ')
        return terminals[0], terminals[1]
    else:
        return GameLogic.GenerateStartEndWords(maxSimilarity=0.5
                                               )

def CopyClipboardGame():
    """
    Copies a share message of the game to the users clipboard.
    """

    wordChain = app.storage.tab.get('word-chain')
    terminalWords = app.storage.tab.get('terminal-words')
    numHints = app.storage.tab.get('num-hints')

    #spoiler formatted chain
    chain = ""
    for word in wordChain:
        chain += f"||{word}||\n"

    url = 'http://linkonym.com/daily' if app.storage.tab.get('mode') == 'daily' else f'http://linkonym.com/random/{app.storage.tab.get("seed")}'
    #write to clipboard
    ui.clipboard.write(f"""----------
Check out my {GAME_NAME} game! 🙂

Here's my word chain from '{terminalWords[0]}' to '{terminalWords[1]}': 🔗

{chain}

Score: {len(wordChain)-1} 🔥
Hints: {numHints} 💡

You can play the same game here: {url}
----------""")
    
    ui.notify("Copied game to clipboard", position='top' if app.storage.client.get('mobile') else 'bottom')

def GuessInput(guess: str, refreshWordChain):
    """
    Guesses the word, validates it, checks distance, notifies user on status, and appends to word chain if valid 
    """
    pos = 'top' if app.storage.client.get('mobile') else 'bottom'

    wordChain = app.storage.tab.get('word-chain')

    valid, message, guess = GameLogic.ValidateGuess(guess, wordChain) #if guess is valid/(if it is in possible values and not banned)
    if(valid):
        valid, message = GameLogic.ValidateWordSim(guess, wordChain) #get result of guessing the word, valid if it is within distance

        if(valid):
            wordChain.append(guess)
            app.storage.tab['word-chain'] = wordChain
            refreshWordChain(True)
            ui.notify(message, type='positive', timeout=1500, position=pos, badgeColor=POSITIVE, badgeTextColor='text')
        else:
            ui.notify(message, type='warning', timeout=1500, position=pos, badgeColor='warning', badgeTextColor='black')
    else:
        ui.notify(message, type='negative', timeout=1500, position=pos, badgeColor=NEGATIVE, badgeTextColor='text')

def WinGame(refreshStats, refreshWin):
    seed = app.storage.tab.get('seed')
    wordChain = app.storage.tab.get('word-chain')
    score = len(wordChain)-1
    gameScores = app.storage.user.get('game-scores')
    gamesPlayed = app.storage.user.get('games-played')
    dialogs = app.storage.client.get('dialogs')

    #update stats
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

    refreshStats()

    #show dialog
    refreshWin()
    dialogs['win'].open()
    app.storage.tab['won'] = True

def RegisterTglBtn(btn: ToggleButton):
    btns = app.storage.client.get('toggle-btns')
    btns.append(btn)
    app.storage.client['toggle-btns'] = btns

    btn.on_click(lambda: ToggleLink(btn))

def ToggleLink(btn: ToggleButton):
    enable = not btn._state
    app.storage.client['selected-word'] = btn.link if enable else ''

    btns = app.storage.client.get('toggle-btns')
    for b in btns:
        if(b.link == btn.link):
            b.enable(enable)
        else:
            b.enable(False)

async def Hint(refreshWordChain):
    """
    Queries gamelogic to determine and guess a hint
    """
    if(app.storage.tab.get('won')): return #cant give hint if already won

    wordChain = app.storage.tab.get('word-chain')
    numHints = app.storage.tab.get('num-hints')
    terminalWords = app.storage.tab.get('terminal-words')

    lastWord = wordChain[-1]

    notif = ui.notification(timeout=None)
    notif.message = 'Thinking...'
    notif.spinner = True

    await asyncio.sleep(0.1)  #let the nicegui render the notification
    
    loop = asyncio.get_running_loop()
    hint = await loop.run_in_executor(None, GameLogic.HintWord, lastWord, terminalWords[1], wordChain)
    GuessInput(hint, refreshWordChain)

    refreshWordChain(True)

    notif.dismiss()

    numHints +=1
    app.storage.tab['num-hints'] = numHints

async def GiveUp(refreshWordChain):
    """
    The equivalent of looping hint until solved
    """
    if(app.storage.tab.get('won')): return #cant give hint if already won

    wordChain = app.storage.tab.get('word-chain')
    numHints = app.storage.tab.get('num-hints')
    terminalWords = app.storage.tab.get('terminal-words')

    lastWord = wordChain[-1]

    notif = ui.notification(timeout=None)
    notif.message = 'Solving...'
    notif.spinner = True

    await asyncio.sleep(0.1)  #let the nicegui render the notification

    #run HintWord in a thread so it doesn't block
    loop = asyncio.get_running_loop()
    solutionPath = await loop.run_in_executor(None, GameLogic.SolutionPath, lastWord, terminalWords[1], wordChain)
    solutionPath = solutionPath[1:]

    notif.message = 'Solution found'
    notif.spinner = False
    notif.type = 'positive'

    await asyncio.sleep(0.1)  #let the nicegui render the notification
    notif.dismiss()

    for guess in solutionPath:
        GuessInput(guess, refreshWordChain)
        numHints += 1
        await asyncio.sleep(0.2)
    
    app.storage.tab['num-hints'] = numHints
    app.storage.tab['given-up'] = True

def CurrentColorScheme():
    return D_SCHEMES if app.storage.user.get('dark-mode') else L_SCHEMES

#region LOGIC
"""

START OF AUTO INDEX PAGE / SCRIPT LOGIC

"""

#RUN UI
ui.run(
    reload=False, #watch files causes issues
    title=GAME_NAME,
    show=False, #dont reload
    storage_secret='SWINGULARITY',
    favicon='''<svg xmlns="http://www.w3.org/2000/svg" height="24" width="24" fill="#111">
  <path d="M15,16v1.26l-6-3v-3.17L11.7,8H16V2h-6v4.9L7.3,10H3v6h5l7,3.5V22h6v-6H15z M12,4h2v2h-2V4z M7,14H5v-2h2V14z M19,20h-2v-2 h2V20z"/>
</svg>''',
    port= PORT
)


#endregion