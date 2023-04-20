import speech_recognition as sr
import pyttsx3
import openai
import requests
from bs4 import BeautifulSoup
from googlesearch import search
from config import GOOGLE_API_KEY, OPEN_AI_KEY, SEARCH_ENGINE
import datetime
import re
import tkinter as tk
from tkinter import ttk

# Set your OpenAI API key
openai.api_key =  OPEN_AI_KEY

# Set your Google Custom Search API key and Search Engine ID
google_api_key = GOOGLE_API_KEY
search_engine_id = SEARCH_ENGINE
in_conversation = False


# Initialize the text-to-speech engine
engine = pyttsx3.init()

# ... (rest of the code for configuring voice and defining functions)

from googleapiclient.discovery import build

def search_web(query):
    service = build("customsearch", "v1", developerKey=google_api_key)
    result = service.cse().list(q=query, cx=search_engine_id, num=5).execute()

    urls = [item['link'] for item in result['items']]
    return urls


def scrape_web(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join([p.text for p in paragraphs][:5])
        return text
    except Exception as e:
        print(f"Error while scraping: {e}")
        return None

def get_web_info(query):
    search_results = search_web(query)
    if not search_results:
        return "I couldn't find any relevant information on the web."

    for url in search_results:
        scraped_text = scrape_web(url)
        if scraped_text:
            return scraped_text

    return "I couldn't find any relevant information on the web."

def get_input_mode():
    while True:
        mode = input("Choose input mode (text/voice): ").lower()
        if mode == "text" or mode == "voice":
            return mode
        else:
            print("Invalid input. Please enter 'text' or 'voice'.")

def respond(text, input_mode):
    print("Jarvis: ", text)
    if input_mode == "voice":
        engine.say(text)
        engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        recognized_text = recognizer.recognize_google(audio)
        print(f"You said: {recognized_text}")
        return recognized_text
    except sr.UnknownValueError:
        print("I couldn't understand what you said. Please try again.")
    except sr.RequestError as e:
        print(f"Error: {e}")
    
    return None

class JarvisUI:
    def __init__(self, master):
        self.master = master
        master.title("Jarvis")

        self.input_mode = tk.StringVar(master)
        self.input_mode.set("text")

        self.mode_label = ttk.Label(master, text="Input mode:")
        self.mode_label.grid(column=0, row=0)

        self.mode_combobox = ttk.Combobox(master, values=("text", "voice"), textvariable=self.input_mode)
        self.mode_combobox.grid(column=1, row=0)

        self.user_input_label = ttk.Label(master, text="Enter your message:")
        self.user_input_label.grid(column=0, row=1)

        self.user_input = ttk.Entry(master)
        self.user_input.grid(column=1, row=1)

        self.submit_button = ttk.Button(master, text="Submit", command=self.submit)
        self.submit_button.grid(column=1, row=2)

        self.output_label = ttk.Label(master, text="Jarvis' response:")
        self.output_label.grid(column=0, row=3)

        self.output = ttk.Label(master, text="")
        self.output.grid(column=1, row=3)

    def submit(self):
        input_mode = self.input_mode.get()
        if input_mode == "voice":
            user_text = listen()
        else:
            user_text = self.user_input.get()

        response = chat_with_jarvis(user_text, input_mode)
        self.output.configure(text=response)

def chat_with_jarvis(user_input, input_mode):
    global in_conversation

    # Initial prompt for ChatGPT to make it talk like Jarvis
    chat_history = [{
        "role": "system",
        "content": "You are Jarvis, an AI assistant with a multitude of capabilities, always ready to assist your user."
    }]

    if user_input is None:
        response_text = "I couldn't understand what you said. Please try again."
    else:
        if not in_conversation and "jarvis" not in user_input:
            return ""

        if "jarvis" in user_input:
            user_input = user_input.replace("jarvis", "").strip()

        if "goodbye" in user_input or "bye" in user_input:
            in_conversation = False
            response_text = "Goodbye!"
        else:
            chat_history.append({"role": "user", "content": user_input})
            
            if re.search(r'\btime\b', user_input):
                now = datetime.datetime.now()
                response_text = now.strftime("It's %I:%M %p.")
            elif re.search(r'\bdate\b', user_input) or re.search(r'\bday\b', user_input):
                now = datetime.datetime.now()
                response_text = now.strftime("Today is %A, %B %d, %Y.")
            else:
                in_conversation = True
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=chat_history,
                    max_tokens=150,
                    n=1,
                    stop=None,
                    temperature=0.8,
                )

                response_text = response['choices'][0]['message']['content'].strip()
                if "as an AI language model, I don't have access to real-time information" in response_text:
                    query = user_input
                    response_text = get_web_info(query)
                    chat_history.pop()  # Remove the previous AI response
                    
                chat_history.append({"role": "assistant", "content": response_text})

    if input_mode == "voice":
        engine.say(response_text)
        engine.runAndWait()

    return response_text


if __name__ == "__main__":
    root = tk.Tk()
    gui = JarvisUI(root)
    root.mainloop()
