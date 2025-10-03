import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import (
Flask, render_template, request, current_app, send_from_directory, redirect, url_for, flash
)
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import validators