from typing import Annotated

import cyclopts
from cyclopts import Parameter
from rich.text import Text

from fly.console import console
from fly.data.cmd import cmd as data_cmd
from fly.local.cmd import cmd as local_bootstrap
from fly.remote.cmd import cmd as remote_bootstrap

LOGO_FULL = r"""
   _____                               ___________.__  .__       .__     __   
  /  _  \______________  ______  _  __ \_   _____/|  | |__| ____ |  |___/  |_ 
 /  /_\  \_  __ \_  __ \/  _ \ \/ \/ /  |    __)  |  | |  |/ ___\|  |  \   __\
/    |    \  | \/|  | \(  <_> )     /   |     \   |  |_|  / /_/  >   Y  \  |  
\____|__  /__|   |__|   \____/ \/\_/    \___  /   |____/__\___  /|___|  /__|  
        \/                                  \/           /_____/      \/      
"""

LOGO_SPLIT = r"""
   _____                               
  /  _  \______________  ______  _  __ 
 /  /_\  \_  __ \_  __ \/  _ \ \/ \/ / 
/    |    \  | \/|  | \(  <_> )     /  
\____|__  /__|   |__|   \____/ \/\_/   
        \/                             
___________.__  .__       .__     __   
\_   _____/|  | |__| ____ |  |___/  |_ 
 |    __)  |  | |  |/ ___\|  |  \   __\
 |     \   |  |_|  / /_/  >   Y  \  |  
 \___  /   |____/__\___  /|___|  /__|  
     \/           /_____/      \/         
"""

LOGO_MINIMAL = "[ Arrow  Flight ]\n  >>==========>".strip()

app = cyclopts.App(
    help_prologue="A CLI to manage the Arrow Flight tutorial", console=console
)


def get_logo() -> str | None:
    if not console.is_terminal:
        return None  # skip in CI / piped output
    w = console.width
    if w >= 82:
        return LOGO_FULL
    elif w >= 42:
        return LOGO_SPLIT
    elif w >= 32:
        return LOGO_MINIMAL
    else:
        return "Arrow Flight"


@app.meta.default()
def meta(*tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)]):
    if logo := get_logo():
        app.console.print(
            Text(
                logo,
                style="bold cyan",
            )
        )
    app(tokens)


app.command(local_bootstrap)
app.command(remote_bootstrap)
app.command(data_cmd)

if __name__ == "__main__":
    app.meta()
