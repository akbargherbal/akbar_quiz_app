# src/multi_choice_quiz/views.py
from django.shortcuts import render
import json


def home(request):
    # Quiz data that was previously hardcoded in app.js
    quiz_data = [
        {
            "text": "What is the capital of France?",
            "options": ["London", "Paris", "Berlin", "Madrid", "Rome"],
            "answerIndex": 1,
        },
        {
            "text": "Which river is the longest in the world?",
            "options": ["Amazon", "Nile", "Mississippi", "Yangtze", "Congo"],
            "answerIndex": 1,  # Traditionally Nile, sometimes debated with Amazon
        },
        {
            "text": "What is the highest mountain peak in the world?",
            "options": ["K2", "Kangchenjunga", "Makalu", "Mount Everest", "Lhotse"],
            "answerIndex": 3,
        },
    ]

    # Convert quiz data to JSON for use in the template
    context = {"quiz_data": json.dumps(quiz_data)}

    return render(request, "multi_choice_quiz/index.html", context)
