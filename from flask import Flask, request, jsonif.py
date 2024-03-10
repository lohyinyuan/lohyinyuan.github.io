from flask import Flask, request, jsonify, render_template
import azure.cognitiveservices.speech as speechsdk
import base64
from flask_cors import CORS
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import re  # For splitting text into sentences

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('frontend.html')

def authenticate_text_analytics_client(subscription_key, endpoint):
    ta_credential = AzureKeyCredential(subscription_key)
    text_analytics_client = TextAnalyticsClient(endpoint=endpoint, credential=ta_credential)
    return text_analytics_client

def analyze_text_sentiment(client, documents):
    response = client.analyze_sentiment(documents=documents)
    return response

def text_to_speech(subscription_key, service_region, text, language, voice_name, style='general'):
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)
    speech_config.speech_synthesis_language = language
    speech_config.speech_synthesis_voice_name = voice_name
    ssml_text = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="{language}"><voice name="{voice_name}"><mstts:express-as style="{style}">{text}</mstts:express-as></voice></speak>'
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_ssml_async(ssml_text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        audio_data = result.audio_data
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        return audio_base64
    else:
        return None

@app.route('/synthesize', methods=['POST'])
def synthesize():
    data = request.json
    ta_subscription_key = '57b75d621d68450c88349f4947cd0b4e'
    ta_endpoint = 'https://lm20240309.cognitiveservices.azure.com/'
    tts_subscription_key = 'bc125dcc9afa408bb5f28f5f4882ca16'
    service_region = 'eastus'
    language = data['language']
    voice_name = data['voiceName']
    
    # Split text into sentences
    sentences = re.split(r'[.!?]+', data['text'])
    sentences = [sentence.strip() for sentence in sentences if sentence]
    
    # Authenticate Text Analytics Client
    client = authenticate_text_analytics_client(ta_subscription_key, ta_endpoint)
    
    # Analyze sentiment for each sentence
    sentiments = analyze_text_sentiment(client, sentences)
    
    # Synthesize speech for each sentence with appropriate style
    audio_segments = []
    audio_segments = []
    for sentence, sentiment in zip(sentences, sentiments):
        style = map_sentiment_to_style(sentiment.sentiment)
        audio_base64 = text_to_speech(tts_subscription_key, service_region, sentence, language, voice_name, style)
        
        if audio_base64:
            audio_segments.append(audio_base64)
        else:
            return jsonify({'error': 'Failed to synthesize speech for a segment'}), 500

    return jsonify({'audioSegments': audio_segments})

def map_sentiment_to_style(sentiment):
    if sentiment == 'positive':
        return 'cheerful'
    elif sentiment == 'negative':
        return 'sad'
    return 'general'

if __name__ == '__main__':
    app.run(debug=True)





