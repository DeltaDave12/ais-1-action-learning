import json
import random
import csv
from datetime import datetime, timedelta
import uuid
import os
import sys

# Add the scripts directory to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from emotion_data import (
    EMOTIONS, SUBJECTS, DIFFICULTY_LEVELS, TIME_CONTEXTS,
    COMPLEX_TOPICS, INTERDISCIPLINARY_TOPICS, TECHNICAL_TERMINOLOGY,
    QUERY_PATTERNS, SUBJECT_CONTEXTS, PERSONALITY_PATTERNS,
    CONTEXT_SCENARIOS
)

# Set up paths - assuming we're running from inside the data folder
DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'datasets')

class StudentEmotionDatasetGenerator:
    def __init__(self):
        # Initialize data structures from emotion_data.py
        self.emotions = EMOTIONS
        self.subjects = SUBJECTS
        self.difficulty_levels = DIFFICULTY_LEVELS
        self.time_contexts = TIME_CONTEXTS
        self.complex_topics = COMPLEX_TOPICS
        self.interdisciplinary_topics = INTERDISCIPLINARY_TOPICS
        self.technical_terminology = TECHNICAL_TERMINOLOGY
        self.query_patterns = QUERY_PATTERNS
        self.subject_contexts = SUBJECT_CONTEXTS
        self.personality_patterns = PERSONALITY_PATTERNS
        self.context_scenarios = CONTEXT_SCENARIOS
        
        # Initialize emotion balancing system for perfect distribution
        self.emotion_pool = []  # Pre-generated pool of emotions for perfect distribution
        self.emotion_index = 0  # Current index in the emotion pool

    def create_balanced_emotion_pool(self, total_entries):
        """Create a perfectly balanced pool of emotions for the entire dataset"""
        emotion_list = list(self.emotions.keys())
        num_emotions = len(emotion_list)
        entries_per_emotion = total_entries // num_emotions
        remainder = total_entries % num_emotions
        
        # Create emotion pool with exact equal distribution
        emotion_pool = []
        
        # Add base count for each emotion
        for emotion in emotion_list:
            emotion_pool.extend([emotion] * entries_per_emotion)
        
        # Distribute remainder entries randomly among emotions
        if remainder > 0:
            remaining_emotions = random.sample(emotion_list, remainder)
            emotion_pool.extend(remaining_emotions)
        
        # Shuffle the pool to randomize order while maintaining perfect balance
        random.shuffle(emotion_pool)
        
        return emotion_pool

    def get_next_balanced_emotion(self):
        """Get the next emotion from the balanced pool"""
        if self.emotion_index >= len(self.emotion_pool):
            # Reset if we've used all emotions (shouldn't happen in normal usage)
            self.emotion_index = 0
        
        emotion = self.emotion_pool[self.emotion_index]
        self.emotion_index += 1
        return emotion

    def get_complex_topic(self, subject):
        """Get a random complex topic for the given subject"""
        topic_options = []
        
        if subject in self.complex_topics:
            for category, topics in self.complex_topics[subject].items():
                topic_options.extend(topics)
        
        topic_options.extend(self.interdisciplinary_topics)
        
        if subject in self.technical_terminology:
            topic_options.extend(self.technical_terminology[subject])
        
        if not topic_options:
            topic_options = [
                f"advanced {subject} concepts",
                f"theoretical {subject} applications",
                f"computational {subject} methods",
                f"applied {subject} research"
            ]
        
        return random.choice(topic_options)

    def generate_complex_topic_context(self, subject, difficulty):
        """Generate contextual description for a complex topic based on difficulty"""
        base_topic = self.get_complex_topic(subject)
        
        complexity_modifiers = {
            'beginner': ['introduction to', 'basic concepts of', 'fundamentals of'],
            'intermediate': ['applications of', 'analysis of', 'implementation of'],
            'advanced': ['theoretical foundations of', 'advanced applications of', 'research in']
        }
        
        modifier = random.choice(complexity_modifiers.get(difficulty, ['']))
        
        variations = [
            f"{modifier} {base_topic}",
            f"{base_topic} in {subject}",
            f"practical applications of {base_topic}",
            f"problem-solving with {base_topic}",
            f"theoretical aspects of {base_topic}",
            f"computational methods for {base_topic}"
        ]
        
        return random.choice(variations)

    def generate_comprehensive_query(self, emotion, subject, difficulty, turn_number, performance_score, context_scenario):
        """Generate comprehensive queries ensuring all patterns are used"""
        base_queries = self.query_patterns[emotion]
        
        # Ensure we use different base queries for variety
        base_query = random.choice(base_queries)
        
        complex_topic = self.get_complex_topic(subject)
        topic_context = self.generate_complex_topic_context(subject, difficulty)
        
        subject_info = self.subject_contexts.get(subject, {})
        terms = subject_info.get('terms', [])
        problems = subject_info.get('problems', [])
        
        # Define emotion categories for better query generation
        positive_emotions = ['excited', 'confident', 'satisfied', 'curious']
        negative_emotions = ['frustrated', 'anxious', 'discouraged', 'overwhelmed']
        neutral_emotions = ['neutral', 'confused']
        
        # Generate multiple query variations to ensure comprehensive coverage
        query_variations = []
        
        # Basic emotion-based queries
        query_variations.append(base_query)
        
        # Subject-specific queries
        if emotion in negative_emotions:
            query_variations.extend([
                f"I'm struggling with {complex_topic} - {base_query.lower()}",
                f"This {topic_context} is confusing me - {base_query.lower()}",
                f"The concept of {complex_topic} has me stumped - {base_query.lower()}",
                f"I can't grasp how {complex_topic} works - {base_query.lower()}",
                f"The textbook section on {complex_topic} doesn't make sense - {base_query.lower()}",
                f"My professor's explanation of {complex_topic} was unclear - {base_query.lower()}",
                f"I keep failing at problems involving {complex_topic} - {base_query.lower()}"
            ])
        elif emotion in positive_emotions:
            query_variations.extend([
                f"I'm exploring {complex_topic} and {base_query.lower()}",
                f"Working on {topic_context} - {base_query.lower()}",
                f"I want to understand {complex_topic} better - {base_query.lower()}",
                f"The topic of {complex_topic} interests me - {base_query.lower()}",
                f"I'm diving deeper into {complex_topic} - {base_query.lower()}",
                f"I find {complex_topic} fascinating - {base_query.lower()}",
                f"I want to master {complex_topic} - {base_query.lower()}"
            ])
        else:  # neutral emotions
            query_variations.extend([
                f"{base_query} with {complex_topic}",
                f"When working on {complex_topic}, {base_query.lower()}",
                f"My professor mentioned {complex_topic} and {base_query.lower()}",
                f"I'm studying {topic_context} - {base_query.lower()}",
                f"Can you help me with {complex_topic}?",
                f"I need guidance on {complex_topic}"
            ])
        
        # Technical terminology variations
        if subject in self.technical_terminology and random.random() < 0.5:
            tech_term = random.choice(self.technical_terminology[subject])
            if emotion in negative_emotions:
                query_variations.extend([
                    f"I'm confused about {tech_term} - {base_query.lower()}",
                    f"The concept of {tech_term} is difficult - {base_query.lower()}",
                    f"I can't understand how {tech_term} applies - {base_query.lower()}"
                ])
            elif emotion in positive_emotions:
                query_variations.extend([
                    f"I'm learning about {tech_term} - {base_query.lower()}",
                    f"The concept of {tech_term} is interesting - {base_query.lower()}",
                    f"I want to explore {tech_term} further - {base_query.lower()}"
                ])
            else:
                query_variations.extend([
                    f"When dealing with {tech_term}, {base_query.lower()}",
                    f"Regarding {tech_term}, {base_query.lower()}",
                    f"How does {tech_term} work?"
                ])
        
        # Performance-based variations
        if emotion in negative_emotions and performance_score < 70:
            query_variations.extend([
                f"I keep getting low scores and {base_query.lower()}",
                f"My performance is suffering because {base_query.lower()}",
                f"I'm struggling academically with {subject} - {base_query.lower()}",
                f"My grades in {subject} are disappointing - {base_query.lower()}"
            ])
        elif emotion in positive_emotions and performance_score > 75:
            query_variations.extend([
                f"I'm doing well but {base_query.lower()}",
                f"Despite my good performance, {base_query.lower()}",
                f"I want to improve even more in {subject} - {base_query.lower()}",
                f"I'm excelling in {subject} and {base_query.lower()}"
            ])
        
        # Difficulty-based variations
        if difficulty == 'beginner':
            if emotion in negative_emotions:
                query_variations.extend([
                    f"As a beginner in {subject}, I'm finding this really hard - {base_query.lower()}",
                    f"I'm new to {subject} and {base_query.lower()}",
                    f"Since I'm just starting with {subject}, {base_query.lower()}"
                ])
            elif emotion in positive_emotions:
                query_variations.extend([
                    f"As a beginner in {subject}, I'm eager to learn - {base_query.lower()}",
                    f"I'm new to {subject} but {base_query.lower()}",
                    f"Starting out in {subject} - {base_query.lower()}"
                ])
        elif difficulty == 'advanced':
            if emotion in negative_emotions:
                query_variations.extend([
                    f"Even at an advanced level in {subject}, {base_query.lower()}",
                    f"This advanced {subject} topic is challenging - {base_query.lower()}",
                    f"Despite my experience in {subject}, {base_query.lower()}"
                ])
            elif emotion in positive_emotions:
                query_variations.extend([
                    f"At this advanced level in {subject}, I'm excited to {base_query.lower()}",
                    f"These advanced {subject} concepts are fascinating - {base_query.lower()}",
                    f"I love the complexity of advanced {subject} - {base_query.lower()}"
                ])
        
        # Context scenario variations
        scenario_contexts = {
            'homework_help': "working on my homework assignment",
            'test_prep': "preparing for my upcoming test",
            'concept_clarification': "trying to understand a concept from class",
            'project_work': "working on my project",
            'review_session': "reviewing material",
            'new_topic': "learning this new topic",
            'remedial_help': "getting extra help",
            'advanced_exploration': "exploring beyond the curriculum"
        }
        
        if context_scenario in scenario_contexts:
            scenario_text = scenario_contexts[context_scenario]
            query_variations.extend([
                f"While {scenario_text}, {base_query.lower()}",
                f"I'm {scenario_text} and {base_query.lower()}",
                f"During {scenario_text}, {base_query.lower()}"
            ])
        
        # Turn-based variations for multi-turn conversations
        if turn_number > 1:
            if emotion in negative_emotions:
                query_variations.extend([
                    f"I'm still struggling - {base_query.lower()}",
                    f"Following up on my previous question, I still {base_query.lower()}",
                    f"I need more help because {base_query.lower()}",
                    f"That didn't help much - {base_query.lower()}"
                ])
            elif emotion in positive_emotions:
                query_variations.extend([
                    f"Building on what we discussed, {base_query.lower()}",
                    f"Following up on that, {base_query.lower()}",
                    f"I want to continue exploring - {base_query.lower()}",
                    f"That was helpful, now {base_query.lower()}"
                ])
            else:
                query_variations.extend([
                    f"Continuing from before, {base_query.lower()}",
                    f"Following up on my previous question, {base_query.lower()}",
                    f"Next, {base_query.lower()}"
                ])
        
        # Select and validate final query
        final_query = random.choice(query_variations)
        final_query = self.validate_query_coherence(final_query, emotion)
        
        return final_query

    def validate_query_coherence(self, query, emotion):
        """Ensure query maintains emotional consistency"""
        positive_emotions = ['excited', 'confident', 'satisfied', 'curious']
        negative_emotions = ['frustrated', 'anxious', 'discouraged', 'overwhelmed']
        
        negative_indicators = ['struggling', 'confused', 'difficult', 'hard', 'can\'t', 'don\'t understand', 'failing', 'stuck']
        positive_indicators = ['excited', 'love', 'fascinating', 'eager', 'want to explore', 'interested', 'enjoy']
        
        query_lower = query.lower()
        
        # Fix mismatched emotional indicators
        if emotion in positive_emotions:
            # Replace negative terms with more neutral/positive ones
            replacements = {
                'struggling with': 'working on',
                'confused about': 'learning about',
                'difficult': 'challenging',
                'can\'t understand': 'want to understand better',
                'failing at': 'practicing with',
                'stuck on': 'exploring'
            }
            for neg_term, pos_term in replacements.items():
                query = query.replace(neg_term, pos_term)
        
        elif emotion in negative_emotions:
            # Replace overly positive terms with more neutral ones
            replacements = {
                'excited to': 'trying to',
                'love': 'need to work on',
                'fascinating': 'complex',
                'eager to': 'attempting to',
                'enjoy': 'am working on'
            }
            for pos_term, neu_term in replacements.items():
                query = query.replace(pos_term, neu_term)
        
        return query

    def calculate_urgency(self, emotion):
        """Calculate urgency level based on emotion"""
        high_urgency = ['frustrated', 'anxious', 'overwhelmed', 'discouraged']
        medium_urgency = ['confused']
        
        if emotion in high_urgency:
            return 'high'
        elif emotion in medium_urgency:
            return 'medium'
        else:
            return 'low'

    def needs_intervention(self, emotion, performance_score):
        """Determine if intervention is needed based on emotion and performance"""
        critical_emotions = ['very frustrated', 'very anxious', 'very overwhelmed', 'very discouraged']
        return emotion in critical_emotions or performance_score < 50

    def generate_conversation_sequence(self, num_turns=3):
        """Generate a sequence of conversation turns with evolving emotions"""
        conversation = []
        student_id = str(uuid.uuid4())[:8]
        session_id = str(uuid.uuid4())[:12]
        
        # Select consistent context for the conversation
        subject = random.choice(self.subjects)
        difficulty = random.choice(self.difficulty_levels)
        scenario = random.choice(list(self.context_scenarios.keys()))
        time_context = random.choice(self.time_contexts)
        
        for turn in range(num_turns):
            # Get perfectly balanced emotion
            current_emotion = self.get_next_balanced_emotion()
            
            # Generate realistic performance and interaction data
            performance_score = random.randint(40, 95)
            response_time = random.randint(10, 300)
            attempts_count = random.randint(1, 5)
            
            # Generate comprehensive query
            current_query = self.generate_comprehensive_query(
                current_emotion, subject, difficulty, turn + 1, 
                performance_score, scenario
            )
            
            # Get previous queries for context
            previous_queries = [conv['current_query'] for conv in conversation[-2:]]
            
            # Build context description
            context_desc = f"{self.context_scenarios[scenario]}. Subject: {subject}. Difficulty: {difficulty}. Time: {time_context}."
            if turn > 0:
                context_desc += f" Previous interaction showed {conversation[-1]['emotion']} emotion."
            
            conversation_entry = {
                'student_id': student_id,
                'session_id': session_id,
                'turn_number': turn + 1,
                'timestamp': (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                'previous_queries': previous_queries,
                'current_query': current_query,
                'context': context_desc,
                'subject': subject,
                'difficulty_level': difficulty,
                'scenario': scenario,
                'time_context': time_context,
                'emotion': current_emotion,
                'emotion_intensity': random.choice(self.emotions[current_emotion]),
                'urgency_level': self.calculate_urgency(current_emotion),
                'performance_score': performance_score,
                'response_time_seconds': response_time,
                'attempts_count': attempts_count,
                'needs_intervention': self.needs_intervention(current_emotion, performance_score)
            }
            
            conversation.append(conversation_entry)
        
        return conversation

    def generate_dataset(self, num_conversations=100, turns_per_conversation=3):
        """Generate dataset with perfectly balanced emotion distribution"""
        print(f"Generating dataset with {num_conversations} conversations and {turns_per_conversation} turns each...")
        
        total_entries = num_conversations * turns_per_conversation
        print(f"Total entries: {total_entries}")
        
        # Create perfectly balanced emotion pool
        self.emotion_pool = self.create_balanced_emotion_pool(total_entries)
        self.emotion_index = 0
        
        print(f"Created balanced emotion pool with {len(self.emotion_pool)} emotions")
        
        # Generate dataset
        dataset = []
        for i in range(num_conversations):
            if (i + 1) % 1000 == 0:
                print(f"Generated {i + 1}/{num_conversations} conversations...")
            
            conversation = self.generate_conversation_sequence(turns_per_conversation)
            dataset.extend(conversation)
        
        return dataset

    def save_dataset(self, dataset, filename='student_emotion_dataset', format='json'):
        """Save dataset to file in specified format"""
        os.makedirs(DATASET_DIR, exist_ok=True)
        filepath = os.path.join(DATASET_DIR, f'{filename}.{format}')
        
        if format == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        elif format == 'csv':
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if dataset:
                    writer = csv.DictWriter(f, fieldnames=dataset[0].keys())
                    writer.writeheader()
                    writer.writerows(dataset)
        
        print(f"Dataset saved as {filepath}")
        print(f"Total records: {len(dataset)}")

    def get_dataset_statistics(self, dataset):
        """Calculate and return detailed dataset statistics"""
        emotions = {}
        subjects = {}
        urgency_levels = {}
        difficulty_levels = {}
        scenarios = {}
        
        for record in dataset:
            # Count emotions
            emotion = record['emotion']
            emotions[emotion] = emotions.get(emotion, 0) + 1
            
            # Count subjects
            subject = record['subject']
            subjects[subject] = subjects.get(subject, 0) + 1
            
            # Count urgency levels
            urgency = record['urgency_level']
            urgency_levels[urgency] = urgency_levels.get(urgency, 0) + 1
            
            # Count difficulty levels
            difficulty = record['difficulty_level']
            difficulty_levels[difficulty] = difficulty_levels.get(difficulty, 0) + 1
            
            # Count scenarios
            scenario = record['scenario']
            scenarios[scenario] = scenarios.get(scenario, 0) + 1
        
        return {
            'total_records': len(dataset),
            'emotion_distribution': emotions,
            'subject_distribution': subjects,
            'urgency_distribution': urgency_levels,
            'difficulty_distribution': difficulty_levels,
            'scenario_distribution': scenarios,
            'unique_students': len(set(record['student_id'] for record in dataset)),
            'unique_sessions': len(set(record['session_id'] for record in dataset))
        }

    def save_dataset_statistics(self, dataset, filename='dataset_statistics'):
        """Save detailed dataset statistics to a text file"""
        os.makedirs(DATASET_DIR, exist_ok=True)
        filepath = os.path.join(DATASET_DIR, f'{filename}.txt')
        
        stats = self.get_dataset_statistics(dataset)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("Dataset Statistics\n")
            f.write("=================\n\n")
            
            f.write(f"Total Records: {stats['total_records']}\n")
            f.write(f"Unique Students: {stats['unique_students']}\n")
            f.write(f"Unique Sessions: {stats['unique_sessions']}\n\n")
            
            # Emotion distribution with balance verification
            f.write("Emotion Distribution (Perfect Balance Check)\n")
            f.write("------------------------------------------\n")
            emotion_counts = list(stats['emotion_distribution'].values())
            is_balanced = len(set(emotion_counts)) <= 2  # Allow for +/- 1 difference due to rounding
            f.write(f"Distribution Status: {'BALANCED' if is_balanced else 'UNBALANCED'}\n")
            
            for emotion, count in sorted(stats['emotion_distribution'].items()):
                percentage = (count / stats['total_records']) * 100
                f.write(f"{emotion}: {count} ({percentage:.2f}%)\n")
            f.write(f"Min count: {min(emotion_counts)}, Max count: {max(emotion_counts)}\n\n")
            
            # Other distributions
            distributions = [
                ('Subject Distribution', 'subject_distribution'),
                ('Urgency Level Distribution', 'urgency_distribution'),
                ('Difficulty Level Distribution', 'difficulty_distribution'),
                ('Scenario Distribution', 'scenario_distribution')
            ]
            
            for title, key in distributions:
                f.write(f"{title}\n")
                f.write("-" * len(title) + "\n")
                for item, count in sorted(stats[key].items()):
                    percentage = (count / stats['total_records']) * 100
                    f.write(f"{item}: {count} ({percentage:.2f}%)\n")
                f.write("\n")
        
        print(f"Statistics saved to {filepath}")
        
        # Print balance verification to console
        emotion_counts = list(stats['emotion_distribution'].values())
        print(f"\nEmotion Balance Verification:")
        print(f"Min count: {min(emotion_counts)}")
        print(f"Max count: {max(emotion_counts)}")
        print(f"Difference: {max(emotion_counts) - min(emotion_counts)}")
        print(f"Status: {'BALANCED' if max(emotion_counts) - min(emotion_counts) <= 1 else 'UNBALANCED'}")

if __name__ == "__main__":
    generator = StudentEmotionDatasetGenerator()
    
    print("Generating training dataset with 80,000 entries...")
    training_dataset = generator.generate_dataset(num_conversations=20000, turns_per_conversation=4)
    
    print("\nGenerating test dataset with 20,000 entries...")
    test_dataset = generator.generate_dataset(num_conversations=5000, turns_per_conversation=4)
    
    # Save training dataset
    print("\nSaving training dataset...")
    generator.save_dataset(training_dataset, 'student_emotion_dataset_80k_balanced', 'json')
    generator.save_dataset(training_dataset, 'student_emotion_dataset_80k_balanced', 'csv')
    generator.save_dataset_statistics(training_dataset, 'training_dataset_statistics_balanced')
    
    # Save test dataset
    print("\nSaving test dataset...")
    generator.save_dataset(test_dataset, 'student_emotion_dataset_test_20k_balanced', 'json')
    generator.save_dataset(test_dataset, 'student_emotion_dataset_test_20k_balanced', 'csv')
    generator.save_dataset_statistics(test_dataset, 'test_dataset_statistics_balanced')
    
    print(f"\n✅ Datasets generated successfully with perfect emotion balance!")
    print("Training dataset: 80,000 entries")
    print("Test dataset: 20,000 entries")
    print("\nFiles saved:")
    print("- student_emotion_dataset_80k_balanced.json and .csv")
    print("- student_emotion_dataset_test_20k_balanced.json and .csv")
    print("- training_dataset_statistics_balanced.txt")
    print("- test_dataset_statistics_balanced.txt")