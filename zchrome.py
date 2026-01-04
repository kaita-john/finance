import requests

def get_open_chrome_tabs():
    try:
        response = requests.get('http://localhost:9222/json')
        tabs = response.json()
        for tab in tabs:
            print(tab.get('title'), '-', tab.get('url'))
    except Exception as e:
        print("Error:", e)
        print("Make sure Chrome was launched with --remote-debugging-port=9222")


get_open_chrome_tabs()