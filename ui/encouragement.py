import random

def get_encouragement(emotion):
    encouragements = {
        'anxious': [
            "Take a deep breath—you're doing better than you think!",
            "It's okay to feel anxious. Step by step, you'll get there.",
            "Remember, every challenge is a chance to grow!"
        ],
        'confident': [
            "Your confidence is inspiring! Keep it up!",
            "You have what it takes—trust yourself!",
            "Keep believing in yourself and great things will happen!"
        ],
        'confused': [
            "It's okay to ask questions—curiosity leads to growth!",
            "Don't worry, confusion is the first step to understanding.",
            "Keep going, clarity is just around the corner!"
        ],
        'curious': [
            "Curiosity is the key to discovery—keep exploring!",
            "Your questions will lead you to new knowledge!",
            "Stay curious and keep learning!"
        ],
        'discouraged': [
            "Don't give up—every setback is a setup for a comeback!",
            "You are stronger than you think. Keep pushing forward!",
            "Remember, progress is progress, no matter how small."
        ],
        'excited': [
            "Your excitement is contagious! Enjoy the journey!",
            "Keep that enthusiasm alive—great things are ahead!",
            "Let your excitement fuel your success!"
        ],
        'frustrated': [
            "Take a moment to pause—you're doing your best!",
            "Frustration means you're trying. Keep going!",
            "Every challenge is an opportunity to improve."
        ],
        'neutral': [
            "Keep exploring and learning!",
            "Stay curious and keep moving forward!",
            "You're doing well—keep it up!"
        ],
        'overwhelmed': [
            "Take things one step at a time—you've got this!",
            "It's okay to take a break. You are making progress!",
            "Remember to be kind to yourself. You're doing great!"
        ],
        'satisfied': [
            "It's great to see your satisfaction! Keep up the good work!",
            "Celebrate your achievements—you've earned it!",
            "Satisfaction is a sign of progress. Well done!"
        ],
    }
    return random.choice(encouragements.get(emotion, encouragements['neutral'])) 