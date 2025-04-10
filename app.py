from flask import Flask, render_template, jsonify, request,redirect,url_for
import requests
from deep_translator import GoogleTranslator
from api import news_api_key,groq_api_key
from groq import Groq
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq

app = Flask(__name__)
global preferred_language 

@app.route('/prefer')
def prefer_page():
    return render_template('prefer.html')

@app.route('/prefer', methods=['POST', 'GET'])
def prefer():
    if request.method == 'POST':
        global preferred_language
        preferred_language = request.form.get('language')
        print(preferred_language)
        return redirect(url_for('home_page'))

@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

chat_history = []

def filter_response(response):
    allowed_topics = ['government orders', 'local news', 'services', 'articles', 'laws','constitution','opportunity','Rights']
    for topic in allowed_topics:
        if topic in response.lower():
            return response
    return "Sorry, I can only answer questions related to government orders, local news, and services."

@app.route('/chat', methods=['POST'])
def chat():
    global preferred_language
    data = request.json
    user_question = data.get('question')

    groq_chat = ChatGroq(groq_api_key=groq_api_key, model_name='llama-3.1-70b-versatile')
    memory = ConversationBufferWindowMemory(k=5)

    conversation = ConversationChain(
        llm=groq_chat,
        memory=memory
    )

    translator = GoogleTranslator(source='auto', target='en')
    translated_question = translator.translate(user_question)

    response = conversation(translated_question)
    filtered_response = filter_response(response['response'])
    translated_response = GoogleTranslator(source='en', target=preferred_language).translate(filtered_response)

    message = {'human': user_question, 'AI': translated_response}
    chat_history.append(message)

    return jsonify({'response': translated_response, 'history': chat_history})

@app.route('/news')
def news():
    global preferred_language
    api_key = news_api_key
    url = f'https://newsapi.org/v2/top-headlines?sources=google-news-in&apiKey={api_key}'
    
    try:
        response = requests.get(url)
        news_data = response.json()
        articles = [
            {"author": "author :" +article.get("author"), "title": "title :" + article.get("title"), "url":article.get("url")}
            for article in news_data.get("articles", [])
        ]

        translator = GoogleTranslator(source='auto', target=preferred_language)

        for article in articles:
            article["title"] = translator.translate(article["title"])
            article["author"] = translator.translate(article["author"])

        return render_template("news.html", articles=articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
