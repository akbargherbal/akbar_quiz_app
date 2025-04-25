// src/multi_choice_quiz/static/multi_choice_quiz/app.js

// Add a log to confirm this script is running
console.log("app.js executing. Setting up quizApp component...");

// Custom event emitter function - can be safely removed without affecting normal functionality
function emitQuizEvent(eventName, data = {}) {
  // DEBUG: Log event emission attempt
  console.log("DEBUG: emitQuizEvent called for:", eventName, "TESTING_MODE:", window.TESTING_MODE);
  // Only emit events if in testing mode
  if (typeof window.TESTING_MODE !== "undefined" && window.TESTING_MODE) {
    const event = new CustomEvent(`quiz:${eventName}`, {
      detail: { ...data, timestamp: Date.now() },
    });
    document.dispatchEvent(event);
    console.log(`DEBUG: Emitted event quiz:${eventName}`, data);
  }
}


// Correct Answer Effects
const glowSize = 2;
const glowBlur = glowSize * 4;
const glowOpacity = 0.8;
const scaleFactor = 105;
const pulseDuration = 1.5; // seconds

// KEEP the scale and shadow here to set the base state
const correctFeedbackEffect = `
  visible
  !bg-green-500  /* This is correct for setting the base color */
  !text-black
  scale-[${scaleFactor}%] /* Sets the base larger size */
  shadow-[0_0_${glowBlur}px_${glowSize}px_rgba(255,255,255,${glowOpacity})] /* Sets the base glow */
  animate-[pulse-glow-scale_${pulseDuration}s_ease-in-out_infinite] /* Use the NEW animation name */
`.trim().replace(/\s+/g, ' '); // Make sure to replace the animation name


// Register the component globally before Alpine.js loads
window.quizApp = function () {
  return {
    // --- State ---
    questions: [],
    currentQuestionIndex: 0,
    userAnswers: [], // Stores index of user's answer for each question
    selectedOptionIndex: null, // Index of the currently selected option (before confirming)
    isAnswered: false, // Has the current question been answered?
    quizCompleted: false, // Has the user finished all questions?
    score: 0, // User's score
    wrongAnswers: 0, // Track wrong answers for star rating
    feedbackTimer: null, // Timer for feedback duration
    correctFeedbackDuration: 3000, // Feedback duration for correct answers (milliseconds)
    incorrectFeedbackDuration: 5000, // Feedback duration for incorrect answers (milliseconds)
    startTime: null, // Time when quiz started
    endTime: null, // Time when quiz ended
    quizTime: 0, // Total time spent on quiz in seconds

    // --- Computed Properties (Getters) ---
    get currentQuestion() {
      // Return the current question object, or null if index is out of bounds
      return this.questions && this.questions.length > this.currentQuestionIndex
        ? this.questions[this.currentQuestionIndex]
        : null;
    },
    get isCorrect() {
      // Check if the user's selected answer (selectedOptionIndex) is the correct one
      // Returns true/false or null if not answered/no question
      return this.currentQuestion && this.selectedOptionIndex !== null
        ? this.selectedOptionIndex === this.currentQuestion.answerIndex
        : null;
    },
    get starRatingDisplay() {
      const totalQuestions = this.questions.length;
      if (totalQuestions === 0) return "☆☆☆☆☆"; // Default empty stars if no questions

      // Formula: Math.ceil((totalQuestions - wrongAnswers) / 2) / 2
      // This formula seems complex, ensure it gives the desired 0-5 star range mapping.
      // Consider simplifying if needed. e.g., direct mapping based on percentage or wrong answers.
      const numericRating =
        Math.ceil((totalQuestions - this.wrongAnswers) / 2) / 2;

      // Scale the numeric rating to a 0-5 range more directly
      const maxPossibleScore = totalQuestions;
      const currentScore = maxPossibleScore - this.wrongAnswers;
      // Example scaling: 5 stars = 90%+, 4.5 = 80%+, 4 = 70%+, etc. Adjust thresholds as needed.
      let scaledRating = 0;
      const percentage =
        maxPossibleScore > 0 ? (currentScore / maxPossibleScore) * 100 : 0;

      if (percentage >= 95) scaledRating = 5;
      else if (percentage >= 85) scaledRating = 4.5;
      else if (percentage >= 75) scaledRating = 4;
      else if (percentage >= 65) scaledRating = 3.5;
      else if (percentage >= 55) scaledRating = 3;
      else if (percentage >= 45) scaledRating = 2.5;
      else if (percentage >= 35) scaledRating = 2;
      else if (percentage >= 25) scaledRating = 1.5;
      else if (percentage >= 15) scaledRating = 1;
      else if (percentage >= 5) scaledRating = 0.5;
      else scaledRating = 0;

      // Round to nearest 0.5 for half-star display
      const roundedRating = Math.round(scaledRating * 2) / 2;

      let starsHtml = "";
      const fullStar = "★";
      const halfStar = "◐";
      const emptyStar = "☆";

      for (let i = 0; i < 5; i++) {
        if (roundedRating >= i + 1) {
          starsHtml += fullStar; // Full star
        } else if (roundedRating >= i + 0.5) {
          starsHtml += halfStar; // Half star
        } else {
          starsHtml += emptyStar; // Empty star
        }
      }
      return starsHtml;
    },

    // --- Methods ---
    // Custom event emitter method
    emitQuizEvent(eventName, data = {}) {
      emitQuizEvent(eventName, data); // Calls the global function
    },

    init() {
      console.log("DEBUG: quizApp component init() started.");

      // ================================== //
      // == TESTING_MODE MOVED TO START === //
      // ================================== //
      window.TESTING_MODE = true; // Set testing mode flag early
      console.log("DEBUG: window.TESTING_MODE set to true at start of init.");
      // ================================== //
      // ===== END OF MOVED LINE ========== //
      // ================================== //

      const dataElement = document.getElementById("quiz-data");
      if (dataElement) {
        try {
          this.questions = JSON.parse(dataElement.textContent || "[]");
          console.log("DEBUG: Quiz data loaded successfully:", this.questions);
          this.userAnswers = Array(this.questions.length).fill(null); // Initialize based on loaded data
        } catch (e) {
          console.error("Failed to parse quiz data from #quiz-data:", e);
          this.questions = [];
          this.userAnswers = [];
        }
      } else {
        console.warn("Quiz data element (#quiz-data) not found in HTML.");
        this.questions = []; // Fallback if element not found
        this.userAnswers = [];
      }

      // Reset other state variables
      this.currentQuestionIndex = 0;
      this.selectedOptionIndex = null;
      this.isAnswered = false;
      this.quizCompleted = false;
      this.score = 0;
      this.wrongAnswers = 0;
      this.startTime = new Date();
      this.endTime = null;
      this.quizTime = 0;

      // Clear any lingering timers from previous runs (e.g., if init is called by restart)
      if (this.feedbackTimer) {
        clearTimeout(this.feedbackTimer);
        this.feedbackTimer = null;
        console.log("DEBUG: Cleared existing feedback timer in init.");
      }

      // Expose the instance globally for testing purposes
      window.quizAppInstance = this;
      console.log("DEBUG: Alpine instance assigned to window.quizAppInstance for testing.");


      if (this.questions.length === 0) {
        console.warn("No questions loaded, quiz cannot start.");
        // Optionally trigger some UI state to show an error message
      } else {
        console.log(
          "Quiz initialized with",
          this.questions.length,
          "questions."
        );
      }

      // Emit quiz initialization event
      this.emitQuizEvent("quiz-initialized", {
        questionsCount: this.questions.length,
      });

      console.log("DEBUG: quizApp component init() finished.");

    },

    selectOption(index) {
      console.log(`DEBUG: selectOption(${index}) called.`);
      if (this.isAnswered || !this.currentQuestion) {
        console.log(
          "DEBUG: Selection ignored - already answered or no current question"
        );
        return;
      }

      this.selectedOptionIndex = index; // Store the user's raw choice index
      this.isAnswered = true; // Set answered flag immediately to trigger feedback styles

      // Store the user's answer index in the array
      if (
        this.userAnswers &&
        this.userAnswers.length > this.currentQuestionIndex
      ) {
        this.userAnswers[this.currentQuestionIndex] = index;
      } else {
        console.error(
          "DEBUG: userAnswers array issue at index:",
          this.currentQuestionIndex
        );
      }

      // Update score/wrong answers based on whether the selected option was correct
      const wasCorrect = this.isCorrect; // Use the getter
      if (wasCorrect) {
        this.score++;
        console.log("DEBUG: Correct Answer! Score:", this.score);
      } else {
        this.wrongAnswers++;
        console.log("DEBUG: Incorrect Answer! Wrong answers:", this.wrongAnswers);
      }

      // Emit answer selected event
      this.emitQuizEvent("answer-selected", {
        questionIndex: this.currentQuestionIndex,
        selectedIndex: index,
        isCorrect: wasCorrect,
      });

      // Clear any existing timer before setting a new one
      if (this.feedbackTimer) {
        clearTimeout(this.feedbackTimer);
         console.log("DEBUG: Cleared existing feedback timer before setting new one.");
      }

      // Determine feedback duration based on correctness
      const feedbackDuration = wasCorrect
        ? this.correctFeedbackDuration
        : this.incorrectFeedbackDuration;

      console.log(
        `DEBUG: Using feedback duration: ${feedbackDuration}ms (${
          wasCorrect ? "correct" : "incorrect"
        } answer)`
      )

      console.log(`DEBUG: Next question will appear in ${feedbackDuration / 1000} seconds.`);

      // Set timer to move to the next question after the feedback duration
      console.log("DEBUG: Setting timer for nextQuestion...");
      this.feedbackTimer = setTimeout(() => {
        console.log("DEBUG: setTimeout callback executing, calling nextQuestion...");
        this.nextQuestion();
      }, feedbackDuration);
    },

    nextQuestion() {
      console.log("DEBUG: nextQuestion entered. Current index:", this.currentQuestionIndex);
      // Clear timer just in case (belt and suspenders)
      if (this.feedbackTimer) {
        clearTimeout(this.feedbackTimer);
        this.feedbackTimer = null;
        console.log("DEBUG: Cleared feedback timer at start of nextQuestion.");
      }

      if (this.currentQuestionIndex < this.questions.length - 1) {
        this.currentQuestionIndex++;
        console.log(`DEBUG: Advanced to question ${this.currentQuestionIndex + 1}`);
        this.isAnswered = false; // Reset for the new question
        this.selectedOptionIndex = null; // Reset selection

        // Emit question changed event
        console.log("DEBUG: About to emit quiz:question-changed...");
        this.emitQuizEvent("question-changed", {
          questionIndex: this.currentQuestionIndex,
        });
      } else {
        this.quizCompleted = true;
        this.endTime = new Date();
        this.calculateQuizTime();
        console.log("DEBUG: Quiz completed. Final score:", this.score);

        // Emit quiz completed event
         console.log("DEBUG: About to emit quiz:quiz-completed...");
        this.emitQuizEvent("quiz-completed", {
          score: this.score,
          wrongAnswers: this.wrongAnswers,
          timeSeconds: this.quizTime,
        });
      }
       console.log("DEBUG: nextQuestion finished.");
    },

    restartQuiz() {
      console.log("DEBUG: Restarting quiz...");
      // Re-initialize the component state fully by calling init()
      // init() already handles resetting state and clearing timers
      this.init();

      // Emit quiz restart event
       console.log("DEBUG: About to emit quiz:quiz-restarted...");
      this.emitQuizEvent("quiz-restarted", {});
    },

    // --- Helper Methods for Results ---
    calculatePercentage() {
      if (this.questions.length === 0) return 0;
      return Math.round((this.score / this.questions.length) * 100);
    },

    calculateQuizTime() {
      if (!this.startTime || !this.endTime) return 0;
      this.quizTime = Math.floor((this.endTime - this.startTime) / 1000);
      return this.quizTime;
    },

    formatTime(seconds) {
      if (!seconds && seconds !== 0) return "--:--"; // Handle null/undefined case
      if (seconds === 0) return "00:00";

      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes.toString().padStart(2, "0")}:${remainingSeconds
        .toString()
        .padStart(2, "0")}`;
    },

    // --- Dynamic Class Logic for Tailwind Feedback ---
    getOptionClass(index) {
      // Ensure currentQuestion exists before proceeding
      if (!this.currentQuestion) {
        return "option-button p-4 rounded-xl font-semibold text-lg md:text-lg sm:text-base text-center transition-all duration-200 ease-in-out border-none cursor-pointer relative overflow-hidden shadow-md flex flex-col items-center justify-center bg-slate-700 text-gray-200";
      }

      // Base Tailwind classes for layout, text, base transition etc.
      let baseClasses = [
        "option-button",
        "p-4",
        "rounded-xl",
        "font-semibold",
        "text-base",
        "text-center",
        // Ensure transitions cover opacity, transform, and visibility
        "transition-all",
        "duration-200",
        "ease-in-out",
        "border-none",
        "cursor-pointer",
        "relative",
        "overflow-hidden",
        // "shadow-md",
        "flex",
        "flex-col",
        "items-center",
        "justify-center",
        "disabled:opacity-100",
        "disabled:cursor-not-allowed",
      ];

      // === State 1: Question NOT Answered Yet ===
      if (!this.isAnswered) {
        const colorClasses = [
          "bg-teal-300 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-blue-300 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-yellow-300 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-purple-400 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-pink-400 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
        ];
        baseClasses.push(colorClasses[index % colorClasses.length]);
        // Add 'visible' explicitly to ensure it overrides potential 'invisible' from previous state
        baseClasses.push("visible");
        return baseClasses.join(" ");
      }
      // === State 2: Question HAS Been Answered (Feedback Time!) ===
      else {
        const actualAnswerIndex = this.currentQuestion.answerIndex;
        const userChoiceIndex = this.selectedOptionIndex;
        let feedbackClasses = "";

        // Is this button the CORRECT answer?
        if (index === actualAnswerIndex) {
          // Make sure it's visible
          feedbackClasses = correctFeedbackEffect;
        }
        // Is this button the user's INCORRECT choice?
        else if (index === userChoiceIndex) {
          // Make sure it's visible
          feedbackClasses = "visible !bg-red-500 !text-white shadow-lg";
        }
        // Otherwise, this button should disappear.
        else {
          // Use 'invisible' (visibility: hidden) along with opacity for the transition effect.
          feedbackClasses = "invisible opacity-0 scale-90 pointer-events-none";
        }

        // Combine base classes with feedback classes
        const filteredBase = baseClasses.filter(
          (cls) =>
            !cls.startsWith("hover:") &&
            !cls.startsWith("active:") &&
            cls !== "visible"
        ); // Remove hover/active/visible
        return filteredBase.join(" ") + " " + feedbackClasses;
      }
    },
  };
};

// Ensure the component registration happens after the function definition
if (typeof window.quizApp === "function") {
  console.log("quizApp component function defined. Registering globally.");
  // The component is usually registered automatically by Alpine if defined before Alpine loads,
  // but explicitly attaching to window ensures it's available.
} else {
  console.error("quizApp function definition failed!");
}