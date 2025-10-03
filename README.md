# Flask APOD 

A secure, hacker-themed Flask web application that fetches NASA's Astronomy Picture of the Day (APOD) and displays it with a modern neon-green terminal-style UI.

## Features

* Fetches NASA APOD images and videos
* Hacker/terminal-inspired UI with neon green text
* Local caching of images to reduce API calls
* Rate limiting to prevent abuse
* Security headers via Flask-Talisman
* Optional HTTPS support with self-signed SSL certificates
* Robust error handling for API requests

## Requirements

* Python 3.9+
* pip
* OpenSSL (if using HTTPS locally)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/FairozAhmadSheikh/NASA_Apod
cd NASA_Apod
```

2. Create a virtual environment and install dependencies (Windows PowerShell):

```powershell
python -m venv venv; .\venv\Scripts\Activate; pip install --upgrade pip; pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example` and fill in your NASA API key and Flask secret key.

4. (Optional) Generate SSL certificates for HTTPS:

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

## Running the App

* Without HTTPS:

```powershell
flask run
```

* With HTTPS (self-signed certs):

```powershell
python app.py
```

Visit: [http://127.0.0.1:5000](http://127.0.0.1:5000) or [https://127.0.0.1:5000](https://127.0.0.1:5000)

## File Structure

```
flask-apod-hacker/
├─ app.py
├─ requirements.txt
├─ .env.example
├─ templates/
│  ├─ layout.html
│  └─ index.html
├─ static/
│  ├─ css/
│  │  └─ style.css
│  └─ cache/   # image cache
└─ README.md
```

## Security Notes

* Never commit `.env`, `cert.pem`, or `key.pem` to GitHub.
* Use `.gitignore` to ignore sensitive files.
* Rate limiting and caching protect the app from abuse.

## Credits

Built with ❤️ · Secure · Cached · by [Fairoz Ahmad Sheikh](https://github.com/FairozAhmadSheikh)
