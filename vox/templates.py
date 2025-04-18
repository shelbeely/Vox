import os
from fastapi.templating import Jinja2Templates

templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../templates"))
templates = Jinja2Templates(directory=templates_dir)
