from src.core.app import TosokuApp
from src.states.editor import EditorState
from src.states.game import GameState
from src.states.settings import SettingsState
from src.states.stats import StatsState
from src.states.workshop import WorkshopState
from src.states.credits import CreditsState
from src.states.links import LinksState

if __name__ == "__main__":
    app = TosokuApp({}, 'EDITOR')
    
    app.state_dict = {
        'EDITOR': EditorState(app),
        'GAME': GameState(app),
        'SETTINGS': SettingsState(app),
        'STATS': StatsState(app),
        'WORKSHOP': WorkshopState(app),
        'CREDITS': CreditsState(app),
        'LINKS': LinksState(app)
    }
    
    app.state = app.state_dict['EDITOR']
    app.run()