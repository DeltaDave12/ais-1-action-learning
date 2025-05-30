# Student Emotion Dataset Generation

A tool for generating balanced datasets of student emotional states during academic interactions, designed for training emotion recognition models.

## Project Structure
```
AL-Emotion/
├── data/
│   ├── datasets/          # Generated datasets
│   └── scripts/           # Python scripts
│       ├── student_emotion_dataset.py
│       └── emotion_data.py
└── README.md
```

## Dataset Details
- Training: 80,000 entries (20,000 conversations × 4 turns)
- Test: 20,000 entries (5,000 conversations × 4 turns)
- Perfect emotion balance across all entries

## Features
- 10 emotional states (excited, confident, satisfied, etc.)
- 6 academic subjects with complex topics
- Realistic query generation with context variations
- Comprehensive statistics and balance verification

## Usage
```bash
cd data/scripts
python student_emotion_dataset.py
```

## Output
Files are saved in `data/datasets/`:
- Training/test datasets (JSON/CSV)
- Statistics files with distribution analysis

## Customization
Modify `emotion_data.py` to adjust:
- Emotions and intensity levels
- Subjects and topics
- Query patterns
- Context scenarios

## Methods & Techniques
- Object-oriented design with modular architecture
- Pre-generated emotion pools for perfect distribution
- Dynamic weight adjustment using performance scores
- Template-based query generation with multiple variations
- JSON/CSV export with pandas
- Comprehensive statistics and balance verification

## References
1. D'Mello, S., & Graesser, A. (2012). "Dynamics of affective states during complex learning." Learning and Instruction, 22(2), 145-157.
2. Baker, R. S., et al. (2010). "Better to be frustrated than bored: The incidence, persistence, and impact of learners' cognitive-affective states during interactions with three different computer-based learning environments." International Journal of Human-Computer Studies, 68(4), 223-241.

## License
Open-source. Contributions welcome! 