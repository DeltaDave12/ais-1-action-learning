# Emotion categories with intensity levels
EMOTIONS = {
    'frustrated': ['slightly frustrated', 'frustrated', 'very frustrated'],
    'confused': ['slightly confused', 'confused', 'very confused'],
    'anxious': ['slightly anxious', 'anxious', 'very anxious'],
    'excited': ['slightly excited', 'excited', 'very excited'],
    'confident': ['somewhat confident', 'confident', 'very confident'],
    'neutral': ['neutral'],
    'curious': ['curious', 'very curious'],
    'discouraged': ['slightly discouraged', 'discouraged', 'very discouraged'],
    'satisfied': ['satisfied', 'very satisfied'],
    'overwhelmed': ['somewhat overwhelmed', 'overwhelmed', 'very overwhelmed']
}

# Core academic subjects
SUBJECTS = ['mathematics', 'science', 'english', 'history', 'programming', 'physics', 'chemistry', 'biology']
DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced']
TIME_CONTEXTS = ['morning', 'afternoon', 'evening', 'before_exam', 'after_exam', 'homework_time']

# Complex topic hierarchies with specific subtopics for each subject
COMPLEX_TOPICS = {
    'mathematics': {
        'algebra': [
            'quadratic equations with complex coefficients',
            'systems of linear inequalities',
            'polynomial factorization techniques',
            'exponential and logarithmic functions',
            'rational expressions and asymptotes',
            'matrix operations and determinants',
            'abstract algebra and group theory',
            'linear transformations in vector spaces'
        ],
        'calculus': [
            'limits involving indeterminate forms',
            'implicit differentiation of parametric equations',
            'integration by partial fractions',
            'multivariable chain rule applications',
            'Taylor and Maclaurin series expansions',
            'optimization problems with constraints',
            'differential equations with boundary conditions',
            'line integrals and Green\'s theorem'
        ],
        'statistics': [
            'hypothesis testing with multiple variables',
            'regression analysis and correlation coefficients',
            'probability distributions and moment generating functions',
            'Bayesian inference and prior distributions',
            'time series analysis and forecasting models',
            'multivariate statistical analysis',
            'non-parametric statistical methods',
            'experimental design and ANOVA'
        ]
    },
    'science': {
        'physics': [
            'quantum mechanical wave functions',
            'electromagnetic field theory and Maxwell\'s equations',
            'thermodynamic cycles and entropy calculations',
            'special relativity and time dilation',
            'oscillatory motion and damped harmonic oscillators',
            'particle physics and the Standard Model',
            'solid state physics and band theory',
            'fluid dynamics and Navier-Stokes equations'
        ],
        'chemistry': [
            'organic synthesis and reaction mechanisms',
            'chemical kinetics and activation energy',
            'electrochemistry and galvanic cells',
            'molecular orbital theory and hybridization',
            'acid-base equilibria and buffer systems',
            'thermochemistry and Hess\'s law',
            'coordination compounds and crystal field theory',
            'polymer chemistry and macromolecular structures'
        ],
        'biology': [
            'protein folding and enzyme kinetics',
            'gene expression and transcriptional regulation',
            'cellular respiration and electron transport chains',
            'evolutionary biology and phylogenetic analysis',
            'neurotransmitter signaling pathways',
            'immunology and adaptive immune responses',
            'molecular genetics and CRISPR technology',
            'ecological succession and population dynamics'
        ]
    },
    'programming': {
        'algorithms': [
            'dynamic programming optimization techniques',
            'graph traversal algorithms and shortest path problems',
            'recursive backtracking and constraint satisfaction',
            'sorting algorithms and computational complexity',
            'machine learning algorithms and neural networks',
            'cryptographic algorithms and hash functions',
            'parallel processing and concurrent programming',
            'data compression and information theory'
        ],
        'data_structures': [
            'balanced binary search trees and AVL rotations',
            'hash tables with collision resolution strategies',
            'priority queues and heap data structures',
            'graph representations and adjacency matrices',
            'trie structures for string matching',
            'segment trees and range query optimization',
            'disjoint set data structures with path compression',
            'persistent data structures and functional programming'
        ]
    },
    'engineering': {
        'electrical': [
            'digital signal processing and Fourier transforms',
            'control systems and feedback loop stability',
            'power electronics and switching circuits',
            'antenna theory and electromagnetic propagation',
            'VLSI design and semiconductor fabrication',
            'renewable energy systems and grid integration',
            'communication protocols and network topology',
            'embedded systems and microcontroller programming'
        ],
        'mechanical': [
            'finite element analysis and stress concentration',
            'fluid mechanics and computational fluid dynamics',
            'heat transfer and thermal system design',
            'machine design and mechanical vibrations',
            'materials science and failure analysis',
            'robotics and kinematic chain analysis',
            'manufacturing processes and quality control',
            'aerospace engineering and propulsion systems'
        ]
    }
}

# Interdisciplinary topics connecting multiple fields
INTERDISCIPLINARY_TOPICS = [
    'bioinformatics and computational biology',
    'econometrics and mathematical modeling',
    'cognitive science and artificial intelligence',
    'environmental engineering and sustainability',
    'biomedical engineering and medical devices',
    'financial mathematics and risk analysis',
    'computational linguistics and natural language processing',
    'quantum computing and information theory',
    'systems biology and network analysis',
    'data science and machine learning applications',
    'cybersecurity and cryptographic protocols',
    'renewable energy systems and smart grids',
    'nanotechnology and materials engineering',
    'behavioral economics and decision theory',
    'digital humanities and text mining'
]

# Technical terminology specific to each field
TECHNICAL_TERMINOLOGY = {
    'mathematics': [
        'eigenvalues and eigenvectors', 'Jacobian matrices', 'gradient descent optimization',
        'stochastic processes', 'Fourier analysis', 'measure theory', 'topological spaces',
        'homomorphisms', 'isomorphisms', 'metric spaces', 'Banach spaces', 'Hilbert spaces'
    ],
    'science': [
        'spectroscopic analysis', 'chromatographic separation', 'electrophoretic mobility',
        'crystallographic structure', 'thermodynamic equilibrium', 'kinetic energy barriers',
        'molecular dynamics simulations', 'quantum mechanical tunneling', 'phase transitions'
    ],
    'programming': [
        'object-oriented polymorphism', 'functional programming paradigms', 'asynchronous programming',
        'microservices architecture', 'containerization and orchestration', 'distributed computing',
        'API design patterns', 'database normalization', 'version control workflows'
    ],
    'engineering': [
        'finite element modeling', 'computational fluid dynamics', 'signal processing algorithms',
        'control theory applications', 'system identification techniques', 'optimization algorithms',
        'reliability engineering', 'failure mode analysis', 'design of experiments'
    ]
}

# Query patterns for different emotional states
QUERY_PATTERNS = {
    'frustrated': [
        "I don't understand this at all", "This makes no sense to me", "Why is this so hard?",
        "I've been trying for hours", "This is impossible", "I give up on this problem",
        "Nothing I try works", "I'm stuck and can't move forward", "This is driving me crazy",
        "I keep getting the wrong answer", "Why won't this work?", "I'm so tired of this",
        "This doesn't make any logical sense", "I've read this ten times and still don't get it",
        "Every approach I try fails", "I'm completely lost here", "This is beyond frustrating",
        "I can't figure out what I'm doing wrong", "Why is this concept so difficult?",
        "I feel like I'm hitting a wall", "This problem is defeating me", "I'm ready to quit",
        "Nothing clicks for me", "I'm getting nowhere with this", "This is hopeless",
        "I've wasted so much time on this", "Why can't I get this right?", "This is infuriating"
    ],
    'confused': [
        "Can you explain this again?", "I'm not sure what this means", "What does this word mean?",
        "How do I solve this?", "I don't get the connection", "This step doesn't make sense",
        "Could you clarify this part?", "I'm mixed up about the process", "What am I missing here?",
        "The instructions are unclear to me", "I don't follow the logic", "Can you break this down?",
        "Which method should I use?", "What's the difference between these two?",
        "I'm not sure where to begin", "The explanation went over my head", "I need more details",
        "What does this symbol represent?", "How do these concepts relate?", "I'm puzzled by this",
        "Could you rephrase that?", "I don't see how this works", "What's the reasoning behind this?",
        "I'm having trouble understanding", "This doesn't align with what I learned before",
        "Can you walk me through this?", "I need help connecting the dots", "This seems contradictory"
    ],
    'anxious': [
        "Is this going to be on the test?", "Am I doing this right?", "What if I fail?",
        "I'm worried about the deadline", "This seems really important", "I don't want to get this wrong",
        "Will this affect my grade?", "I'm nervous about the exam", "What if I can't finish in time?",
        "I'm scared I'm behind everyone else", "This looks really complicated", "I hope I can handle this",
        "What if I mess up the presentation?", "I'm worried I'm not prepared enough",
        "Will there be questions like this on the quiz?", "I don't want to disappoint my teacher",
        "What if I fail the assignment?", "I'm stressed about getting this perfect",
        "Am I understanding this correctly?", "I'm concerned about my performance",
        "What if this is harder than I think?", "I'm worried about making mistakes",
        "Is my approach completely wrong?", "I hope I'm not falling behind",
        "What if I can't meet expectations?", "I'm anxious about the final result",
        "Will I be able to remember this during the test?", "I'm worried about the time pressure"
    ],
    'excited': [
        "This is really cool!", "I want to learn more about this", "Can we do another example?",
        "This is my favorite subject", "I think I'm getting it!", "What else can this be used for?",
        "This is fascinating!", "I love how this works!", "Can we explore this further?",
        "This is so interesting!", "I want to try more problems like this", "This is amazing!",
        "I'm really enjoying this topic", "Can you show me advanced applications?",
        "This is exactly what I wanted to learn", "I'm excited to practice more",
        "This opens up so many possibilities", "I can't wait to use this knowledge",
        "This is incredibly useful", "I'm thrilled to understand this concept",
        "Can we dive deeper into this?", "This is better than I expected",
        "I'm passionate about this subject", "This makes everything click!",
        "I want to become an expert in this", "This is so much fun to learn",
        "Can you recommend more resources on this?", "I'm motivated to study more"
    ],
    'confident': [
        "I think I understand now", "Let me try this problem", "I got the previous one right",
        "This seems straightforward", "I can handle this", "I'm ready for the next step",
        "I feel good about my approach", "I'm comfortable with this concept",
        "This makes perfect sense to me", "I can solve this on my own",
        "I'm confident in my understanding", "I've got the hang of this",
        "This is within my capabilities", "I know exactly what to do",
        "I'm prepared for this challenge", "I trust my knowledge here",
        "This aligns with what I learned", "I can build on this foundation",
        "I'm ready to tackle harder problems", "I feel competent with this material",
        "I can explain this to someone else", "I'm sure of my method",
        "This confirms what I thought", "I have a solid grasp of this",
        "I'm comfortable moving forward", "I can apply this principle",
        "I feel prepared and ready", "This is definitely manageable"
    ],
    'neutral': [
        "What's the next step?", "Can you give me an example?", "How do I start this?",
        "What's the formula for this?", "What should I do here?", "Can you check my work?",
        "What tools do I need for this?", "How long should this take?", "What's the standard approach?",
        "Can you provide some guidance?", "What are the requirements?", "How is this typically done?",
        "What's the best practice here?", "Can you outline the process?", "What resources are available?",
        "How do I organize my work?", "What's the expected format?", "Can you clarify the instructions?",
        "What information do I need?", "How should I structure this?", "What's the timeline?",
        "Can you point me in the right direction?", "What are the key points?", "How do I proceed?",
        "What's the methodology?", "Can you suggest a starting point?", "What's the framework?",
        "How do I document this?", "What are the deliverables?"
    ],
    'curious': [
        "Why does this work?", "What's the theory behind this?", "How was this discovered?",
        "Are there other ways to do this?", "What are the real-world applications?", "Can you show me more examples?",
        "What's the historical context?", "Who developed this concept?", "How does this relate to other topics?",
        "What are the implications of this?", "Can this be extended further?", "What are the limitations?",
        "How is this used in industry?", "What research is being done on this?",
        "Are there controversial aspects to this?", "What are the current developments?",
        "How does this connect to my other subjects?", "What would happen if we changed this variable?",
        "What are the philosophical implications?", "How has this evolved over time?",
        "What are the practical benefits?", "Can you recommend related topics?",
        "What are the ethical considerations?", "How does this impact society?",
        "What are the future possibilities?", "Can this be automated?", "What are the alternatives?",
        "How do experts view this?", "What are the cutting-edge applications?"
    ],
    'discouraged': [
        "I'm not good at this", "Everyone else seems to get it", "Maybe I should just skip this",
        "I always struggle with this topic", "I don't think I'll ever understand", "This is too advanced for me",
        "I'm the slowest one in class", "I keep making the same mistakes", "I feel like giving up",
        "I'm not smart enough for this", "This is beyond my abilities", "I'll never be good at this subject",
        "I should probably drop this course", "I'm holding everyone back", "I don't belong here",
        "I'm terrible at problem-solving", "I lack the natural talent for this", "I'm disappointing myself",
        "Maybe this isn't for me", "I feel defeated", "I'm losing motivation",
        "I can't compete with my classmates", "I'm not cut out for this", "I'm falling further behind",
        "I feel like a failure", "I'm questioning my abilities", "I don't see the point anymore",
        "I'm losing confidence", "I feel inadequate", "I'm considering switching majors"
    ],
    'satisfied': [
        "That makes sense now", "I'm happy with my progress", "That was a good explanation",
        "I feel good about this", "Thank you for the help", "I think I've got it",
        "I'm pleased with my understanding", "That cleared things up nicely", "I'm content with this result",
        "This feels right to me", "I'm satisfied with my work", "That was exactly what I needed",
        "I feel accomplished", "This gives me closure", "I'm happy with how this turned out",
        "That was a productive session", "I feel like I made progress", "This meets my expectations",
        "I'm glad I stuck with it", "That was worth the effort", "I feel more confident now",
        "This is a good stopping point", "I'm comfortable with this level", "That resolved my concerns",
        "I'm pleased with the outcome", "This feels complete", "I'm happy with my grasp of this",
        "That was helpful and clear", "I feel ready to move on"
    ],
    'overwhelmed': [
        "There's so much to learn", "I don't know where to start", "This is a lot of information",
        "Can we break this down?", "I feel lost in all these details", "This is too much at once",
        "I'm drowning in information", "There are too many concepts to grasp", "I feel buried under all this material",
        "My head is spinning from all this", "I can't process all of this", "This is information overload",
        "I'm struggling to keep up with everything", "There's too much complexity here",
        "I feel swamped by all these requirements", "I can't see the forest for the trees",
        "This is mentally exhausting", "I'm getting lost in the details", "There's too much to remember",
        "I feel like I'm in over my head", "This is cognitively demanding", "I need to slow down",
        "I'm having trouble prioritizing", "Everything seems equally important", "I can't focus on so much",
        "This is sensory overload", "I need to take breaks", "I feel mentally saturated",
        "This is too intensive for me right now"
    ]
}

# Subject-specific terminology and contexts
SUBJECT_CONTEXTS = {
    'mathematics': {
        'topics': ['algebra', 'calculus', 'geometry', 'statistics', 'trigonometry', 'probability', 'derivatives', 'integrals', 'equations', 'functions'],
        'terms': ['solve', 'calculate', 'prove', 'graph', 'equation', 'variable', 'coefficient', 'theorem', 'formula', 'expression'],
        'problems': ['word problems', 'proofs', 'graphing', 'optimization', 'limits', 'series', 'matrices', 'vectors']
    },
    'science': {
        'topics': ['biology', 'chemistry', 'physics', 'ecology', 'genetics', 'evolution', 'cells', 'atoms', 'molecules', 'energy'],
        'terms': ['experiment', 'hypothesis', 'theory', 'observation', 'data', 'analysis', 'conclusion', 'variable', 'control', 'measurement'],
        'problems': ['lab reports', 'experiments', 'classifications', 'calculations', 'predictions', 'analysis']
    },
    'english': {
        'topics': ['literature', 'grammar', 'writing', 'poetry', 'essays', 'novels', 'plays', 'rhetoric', 'composition', 'analysis'],
        'terms': ['analyze', 'interpret', 'theme', 'character', 'plot', 'metaphor', 'symbolism', 'argument', 'evidence', 'thesis'],
        'problems': ['essays', 'analysis papers', 'creative writing', 'presentations', 'discussions', 'interpretations']
    },
    'history': {
        'topics': ['ancient civilizations', 'wars', 'revolutions', 'politics', 'culture', 'economics', 'social movements', 'treaties', 'empires', 'dates'],
        'terms': ['analyze', 'compare', 'contrast', 'cause', 'effect', 'significance', 'context', 'perspective', 'primary source', 'secondary source'],
        'problems': ['research papers', 'timelines', 'comparisons', 'analysis', 'debates', 'presentations']
    },
    'programming': {
        'topics': ['algorithms', 'data structures', 'loops', 'functions', 'variables', 'debugging', 'syntax', 'logic', 'databases', 'web development'],
        'terms': ['code', 'compile', 'debug', 'function', 'variable', 'loop', 'condition', 'array', 'object', 'method'],
        'problems': ['coding assignments', 'debugging', 'algorithms', 'projects', 'testing', 'optimization']
    },
    'physics': {
        'topics': ['mechanics', 'thermodynamics', 'electricity', 'magnetism', 'waves', 'optics', 'quantum', 'relativity', 'forces', 'energy'],
        'terms': ['calculate', 'measure', 'force', 'velocity', 'acceleration', 'energy', 'momentum', 'frequency', 'wavelength', 'field'],
        'problems': ['problem solving', 'calculations', 'experiments', 'lab work', 'derivations', 'applications']
    },
    'chemistry': {
        'topics': ['atoms', 'molecules', 'reactions', 'bonds', 'periodic table', 'solutions', 'acids', 'bases', 'organic', 'stoichiometry'],
        'terms': ['balance', 'react', 'bond', 'electron', 'proton', 'neutron', 'molecule', 'compound', 'solution', 'concentration'],
        'problems': ['balancing equations', 'calculations', 'lab work', 'synthesis', 'analysis', 'predictions']
    },
    'biology': {
        'topics': ['cells', 'genetics', 'evolution', 'ecology', 'anatomy', 'physiology', 'DNA', 'proteins', 'organisms', 'systems'],
        'terms': ['classify', 'identify', 'compare', 'analyze', 'observe', 'cell', 'gene', 'protein', 'organism', 'species'],
        'problems': ['lab work', 'classifications', 'experiments', 'observations', 'analysis', 'research']
    }
}

# Student personality patterns for language variation
PERSONALITY_PATTERNS = {
    'formal': ['Could you please', 'I would appreciate', 'Would it be possible', 'I respectfully request'],
    'casual': ['Can you', 'Hey', 'So like', 'Um'],
    'direct': ['I need', 'Show me', 'Tell me', 'Give me'],
    'tentative': ['I think maybe', 'Perhaps', 'I wonder if', 'It seems like'],
    'enthusiastic': ['Wow', 'Amazing', 'Awesome', 'Incredible'],
    'technical': ['According to', 'Based on', 'In terms of', 'Regarding']
}

# Context scenarios for different learning situations
CONTEXT_SCENARIOS = {
    'homework_help': "Student is working on homework assignment",
    'test_prep': "Student is preparing for an upcoming test",
    'concept_clarification': "Student needs clarification on a concept taught in class",
    'project_work': "Student is working on a project",
    'review_session': "Student is reviewing previously learned material",
    'new_topic': "Student is learning a new topic for the first time",
    'remedial_help': "Student needs additional help on a challenging topic",
    'advanced_exploration': "Student wants to explore beyond basic curriculum"
} 