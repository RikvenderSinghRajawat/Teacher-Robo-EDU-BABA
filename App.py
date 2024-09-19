# Import necessary libraries
import wikipediaapi
from gtts import gTTS
from flask import Flask, render_template, request
import os
import speech_recognition as sr
import openai
import pygame
import traceback

# Initialize Flask app
app = Flask(__name__)

# Set your OpenAI GPT-3 API key (this is your original key)
api_key = "eJWhD2YMiWlAmxW9FtPf8XxGJB5Any-8"  # Replace with your OpenAI API key

# Set a custom user agent for Wikipedia requests
HEADERS = {'User-Agent': 'YourUserAgent/1.0 (YourEmail@example.com)'}
wiki_wiki = wikipediaapi.Wikipedia('en', extract_format=wikipediaapi.ExtractFormat.WIKI, headers=HEADERS)

# Function to get a limited response from Wikipedia
def get_limited_wikipedia_response(topic, max_words=200):
    page = wiki_wiki.page(topic)
    if page.exists():
        summary = page.text
        words = summary.split()
        if len(words) > max_words:
            return ' '.join(words[:max_words])
        return summary
    return "I couldn't find any information on that topic."

# Function to get an answer from ChatGPT using OpenAI API
def get_gpt3_answer(question):
    openai.api_key = api_key
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Q: {question}\nA:",
        max_tokens=150
    )
    return response['choices'][0]['text'].strip()

# Function to speak text using gTTS and play audio with pygame
def speak(text):
    tts = gTTS(text, lang='en')
    tts.save("response.mp3")
    play_audio("response.mp3")

# Function to play an audio file using pygame
def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# Function to save question and answer to a text file
def save_to_text_file(question, answer):
    with open("question_answer.txt", "w") as file:
        file.write(f"Question: {question}\nAnswer: {answer}")

# Route to render the main webpage
@app.route('/')
def index():
    return render_template('combined.html')

# Route for Wikipedia search
@app.route('/test_wikipedia_search', methods=['POST'])
def test_wikipedia_search():
    try:
        topic = request.form['topic']
        topic_answer = get_limited_wikipedia_response(topic, max_words=200)
        if topic_answer:
            speak(topic_answer)
        return render_template('combined.html', result=topic_answer)
    except Exception as e:
        traceback.print_exc()
        return f"Internal Server Error: {e}", 500

# Route for voice-based ChatGPT interaction
@app.route('/test_chatgpt_voice', methods=['POST'])
def test_chatgpt_voice():
    try:
        # Initialize recognizer and microphone
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=15)  # Listen for up to 15 seconds

        try:
            question = recognizer.recognize_google(audio, show_all=False).lower()
            answer = get_gpt3_answer(question)

            save_to_text_file(question, answer)
            speak(answer)

        except sr.UnknownValueError:
            return "I couldn't understand the audio. Please try again."
        except sr.RequestError as e:
            return f"Speech recognition request error: {e}"

        return render_template('combined.html', result=answer)
    except Exception as e:
        traceback.print_exc()
        return f"Internal Server Error: {e}", 500

# Route for text-based ChatGPT interaction
@app.route('/test_chatgpt_text', methods=['POST'])
def test_chatgpt_text():
    try:
        question = request.form['question']
        answer = get_gpt3_answer(question)

        save_to_text_file(question, answer)
        speak(answer)

        return render_template('combined.html', result=answer)
    except Exception as e:
        traceback.print_exc()
        return f"Internal Server Error: {e}", 500

# Start the Flask app
if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)
