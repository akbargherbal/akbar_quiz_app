document.addEventListener('alpine:init', () => {
    Alpine.data('quizApp', () => ({
        // --- State ---
        questions: [
            {
                text: 'What is the capital of France?',
                options: ['London', 'Paris', 'Berlin', 'Madrid', 'Rome'],
                answerIndex: 1
            },
            {
                text: 'Which river is the longest in the world?',
                options: ['Amazon', 'Nile', 'Mississippi', 'Yangtze', 'Congo'],
                answerIndex: 1 // Traditionally Nile, sometimes debated with Amazon
            },
            {
                text: 'What is the highest mountain peak in the world?',
                options: ['K2', 'Kangchenjunga', 'Makalu', 'Mount Everest', 'Lhotse'],
                answerIndex: 3
            }
        ],
        currentQuestionIndex: 0,
        userAnswers: [], // Stores index of user's answer for each question
        selectedOptionIndex: null, // Index of the currently selected option (before confirming)
        isAnswered: false, // Has the current question been answered?
        showModal: false, // Show correct/incorrect feedback modal?
        quizCompleted: false, // Has the user finished all questions?
        score: 0, // User's score

        // --- Computed Properties (Getters) ---
        get currentQuestion() {
            return this.questions[this.currentQuestionIndex];
        },
        get isCorrect() {
            // Check if the selected answer for the *current* question is correct
            return this.selectedOptionIndex === this.currentQuestion.answerIndex;
        },

        // --- Methods ---
        init() {
            // Initialize userAnswers array with nulls when component loads
            this.userAnswers = Array(this.questions.length).fill(null);
            // Reset other state just in case
            this.currentQuestionIndex = 0;
            this.selectedOptionIndex = null;
            this.isAnswered = false;
            this.showModal = false;
            this.quizCompleted = false;
            this.score = 0;
        },

        selectOption(index) {
            if (this.isAnswered) return; // Prevent changing answer after selection

            this.selectedOptionIndex = index;
            this.isAnswered = true;
            this.userAnswers[this.currentQuestionIndex] = index; // Store the answer

            if (this.isCorrect) {
                this.score++;
            }

            this.showModal = true; // Show feedback modal
        },

        nextQuestion() {
            this.showModal = false; // Hide modal

            if (this.currentQuestionIndex < this.questions.length - 1) {
                // Move to the next question
                this.currentQuestionIndex++;
                // Reset state for the new question
                this.isAnswered = false;
                this.selectedOptionIndex = null;
            } else {
                // End of quiz
                this.quizCompleted = true;
            }
        },

        restartQuiz() {
            this.init(); // Re-initialize the component state
        },

        // --- Dynamic Class Logic ---
        getOptionClass(index) {
            const baseClasses = ['option-button'];
            const colorClasses = [ // Assign colors consistently
                'blue-option', 'teal-option', 'orange-option', 'red-option', 'turquoise-option'
            ];
            baseClasses.push(colorClasses[index % colorClasses.length]);

            if (!this.isAnswered) {
                // Before answering, just return base + color
                return baseClasses.join(' ');
            } else {
                // After answering:
                if (index === this.currentQuestion.answerIndex) {
                    // This is the correct answer
                    baseClasses.push('correct-answer');
                } else if (index === this.selectedOptionIndex) {
                    // This is the incorrect answer the user selected
                    baseClasses.push('incorrect-answer');
                } else {
                    // This is an incorrect option the user did *not* select
                     baseClasses.push('disabled-option'); // Visually disable it
                }
                return baseClasses.join(' ');
            }
        }
    }));
});

// Add a fallback initialization in case Alpine.js is already loaded
// This helps catch race conditions where Alpine.js might initialize before our listener is set up
if (window.Alpine) {
    // Alpine.js is already available
    console.log("Alpine.js already loaded, initializing quizApp directly");
    if (!window.Alpine.data('quizApp')) {
        // Initialize quizApp if it doesn't exist yet
        document.dispatchEvent(new CustomEvent('alpine:init'));
    }
}