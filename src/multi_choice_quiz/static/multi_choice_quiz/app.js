// Add a log to confirm this script is running
console.log("app.js executing. Setting up quizApp component...");

// Register the component globally before Alpine.js loads
window.quizApp = function() {
    return {
        // --- State ---
        questions: [], // Initialize as empty; data will be loaded in init()
        currentQuestionIndex: 0,
        userAnswers: [], // Stores index of user's answer for each question
        selectedOptionIndex: null, // Index of the currently selected option (before confirming)
        isAnswered: false, // Has the current question been answered?
        quizCompleted: false, // Has the user finished all questions?
        score: 0, // User's score
        feedbackTimer: null, // Timer for feedback duration
        feedbackDuration: 2000, // Feedback duration in milliseconds (2 seconds)

        // --- Computed Properties (Getters) ---
        get currentQuestion() {
            // Return the current question object, or null if index is out of bounds
            return this.questions && this.questions.length > this.currentQuestionIndex
                ? this.questions[this.currentQuestionIndex]
                : null;
        },
        get isCorrect() {
            // Check if the selected answer for the *current* question is correct
            // Ensure currentQuestion is not null before accessing its properties
            return this.currentQuestion && this.selectedOptionIndex === this.currentQuestion.answerIndex;
        },

        // --- Methods ---
        init() {
            console.log("quizApp component init() called."); // Log init call
            // Load questions data from the embedded JSON in the HTML
            const dataElement = document.getElementById('quiz-data');
            if (dataElement) {
                try {
                    // Parse the JSON data from the script tag's text content
                    this.questions = JSON.parse(dataElement.textContent || '[]');
                    console.log("Quiz data loaded successfully:", this.questions);

                    // Initialize userAnswers array based on the *actual* number of questions loaded
                    this.userAnswers = Array(this.questions.length).fill(null);

                } catch (e) {
                    console.error("Failed to parse quiz data from #quiz-data:", e);
                    this.questions = []; // Set empty questions on error
                    this.userAnswers = [];
                }
            } else {
                console.warn("Quiz data element (#quiz-data) not found in HTML. Using empty questions array.");
                this.questions = []; // Fallback if element not found
                this.userAnswers = [];
            }

            // Reset other state variables regardless of data loading success
            this.currentQuestionIndex = 0;
            this.selectedOptionIndex = null;
            this.isAnswered = false;
            this.quizCompleted = false;
            this.score = 0;

            // Check if there are any questions to start with
            if (this.questions.length === 0) {
                console.warn("No questions loaded, quiz cannot start.");
                // Optionally display a message to the user here
            } else {
                console.log("Quiz initialized with", this.questions.length, "questions.");
            }
        },

        selectOption(index) {
            console.log(`Option selected: ${index}`); // Add logging
            
            // Prevent action if already answered or if there's no current question
            if (this.isAnswered || !this.currentQuestion) {
                console.log("Selection ignored - already answered or no current question");
                return;
            }

            this.selectedOptionIndex = index;
            this.isAnswered = true;

            // Ensure userAnswers array exists and has the correct index
            if (this.userAnswers && this.userAnswers.length > this.currentQuestionIndex) {
                this.userAnswers[this.currentQuestionIndex] = index; // Store the answer
            } else {
                console.error("userAnswers array issue at index:", this.currentQuestionIndex);
            }

            if (this.isCorrect) {
                this.score++;
            }

            // Clear any existing timer
            if (this.feedbackTimer) {
                clearTimeout(this.feedbackTimer);
            }

            // Set timer to move to next question after feedback duration
            this.feedbackTimer = setTimeout(() => {
                this.nextQuestion();
            }, this.feedbackDuration);
        },

        nextQuestion() {
            console.log("nextQuestion() called"); // Add logging
            
            // Check if there are more questions left
            if (this.currentQuestionIndex < this.questions.length - 1) {
                // Move to the next question
                this.currentQuestionIndex++;
                console.log(`Advanced to question ${this.currentQuestionIndex + 1}`);
                
                // Reset state for the new question
                this.isAnswered = false;
                this.selectedOptionIndex = null;
            } else {
                // End of quiz
                this.quizCompleted = true;
                console.log("Quiz completed. Final score:", this.score);
            }
        },

        restartQuiz() {
            console.log("Restarting quiz...");
            
            // Force clear any timers
            if (this.feedbackTimer) {
                clearTimeout(this.feedbackTimer);
                this.feedbackTimer = null;
            }
            
            // Re-initialize the component state
            this.currentQuestionIndex = 0;
            this.userAnswers = Array(this.questions.length).fill(null);
            this.selectedOptionIndex = null;
            this.isAnswered = false;
            this.quizCompleted = false;
            this.score = 0;
        },

        // --- Dynamic Class Logic ---
        getOptionClass(index) {
            // Ensure currentQuestion exists before proceeding
            if (!this.currentQuestion) {
                // Return default classes if no question is loaded
                return 'option-button grey-option'; // Added a fallback color class
            }

            const baseClasses = ['option-button'];
            const colorClasses = [ // Assign colors consistently
                'blue-option', 'teal-option', 'orange-option', 'red-option', 'turquoise-option'
            ];
            // Use modulo to cycle through colors if more options than colors
            baseClasses.push(colorClasses[index % colorClasses.length]);

            if (!this.isAnswered) {
                // Before answering, just return base + color
                return baseClasses.join(' ');
            } else {
                // After answering and during feedback period:
                if (index === this.currentQuestion.answerIndex) {
                    // This is the correct answer - always show and make it glow
                    baseClasses.push('correct-answer');
                } else if (index === this.selectedOptionIndex && index !== this.currentQuestion.answerIndex) {
                    // This is the incorrect answer the user selected - show in red
                    baseClasses.push('incorrect-answer');
                } else {
                    // This is an option the user did not select - make it disappear
                    baseClasses.push('disappear');
                }
                return baseClasses.join(' ');
            }
        }
    };
};

console.log("quizApp component registered globally");
