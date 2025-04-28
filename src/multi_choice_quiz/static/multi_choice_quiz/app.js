// src/multi_choice_quiz/static/multi_choice_quiz/app.js

// Add a log to confirm this script is running
console.log("app.js executing. Setting up quizApp component...");

// Correct Answer Effects Constants (remain unchanged)
const glowSize = 2;
const glowBlur = glowSize * 4;
const glowOpacity = 0.8;
const scaleFactor = 105;
const pulseDuration = 1.5; // seconds

// Base effect class string (remain unchanged)
// KEEP the scale and shadow here to set the base state
const correctFeedbackEffect = `
  visible
  !bg-green-500  /* This is correct for setting the base color */
  !text-black
  scale-[${scaleFactor}%] /* Sets the base larger size */
  shadow-[0_0_${glowBlur}px_${glowSize}px_rgba(255,255,255,${glowOpacity})] /* Sets the base glow */
  animate-[pulse-glow-scale_${pulseDuration}s_ease-in-out_infinite] /* Use the NEW animation name */
`
  .trim()
  .replace(/\s+/g, " "); // Make sure to replace the animation name

// Register the component globally
window.quizApp = function () {
  let initialized = false;

  // Thresholds for star rating calculation (highest first)
  const starRatingThresholds = [
    { threshold: 95, rating: 5 },
    { threshold: 85, rating: 4.5 },
    { threshold: 75, rating: 4 },
    { threshold: 65, rating: 3.5 },
    { threshold: 55, rating: 3 },
    { threshold: 45, rating: 2.5 },
    { threshold: 35, rating: 2 },
    { threshold: 25, rating: 1.5 },
    { threshold: 15, rating: 1 },
    { threshold: 5, rating: 0.5 },
  ];

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
    // --- Using ORIGINAL feedback durations ---
    correctFeedbackDuration: 4000, // Feedback duration for correct answers (milliseconds)
    incorrectFeedbackDuration: 6000, // Feedback duration for incorrect answers (milliseconds)
    // --- Using ORIGINAL feedback durations ---
    startTime: null, // Time when quiz started
    endTime: null, // Time when quiz ended
    quizTime: 0, // Total time spent on quiz in seconds

    // --- Computed Properties (Getters) ---
    get currentQuestion() {
      return this.questions && this.questions.length > this.currentQuestionIndex
        ? this.questions[this.currentQuestionIndex]
        : null;
    },
    get isCorrect() {
      return this.currentQuestion && this.selectedOptionIndex !== null
        ? this.selectedOptionIndex === this.currentQuestion.answerIndex
        : null;
    },
    get starRatingDisplay() {
      const totalQuestions = this.questions.length;
      if (totalQuestions === 0) return "☆☆☆☆☆"; // Default empty stars if no questions

      const maxPossibleScore = totalQuestions;
      const currentScore = maxPossibleScore - this.wrongAnswers;
      const percentage =
        maxPossibleScore > 0 ? (currentScore / maxPossibleScore) * 100 : 0;

      let scaledRating = 0;
      for (const item of starRatingThresholds) {
        if (percentage >= item.threshold) {
          scaledRating = item.rating;
          break;
        }
      }
      const roundedRating = Math.round(scaledRating * 2) / 2;

      let starsHtml = "";
      const fullStar = "★";
      const halfStar = "◐";
      const emptyStar = "☆";

      for (let i = 0; i < 5; i++) {
        if (roundedRating >= i + 1) {
          starsHtml += fullStar;
        } else if (roundedRating >= i + 0.5) {
          starsHtml += halfStar;
        } else {
          starsHtml += emptyStar;
        }
      }
      return starsHtml;
    },

    // --- Methods ---
    emitQuizEvent(eventName, data = {}) {
      console.log(
        "DEBUG: emitQuizEvent called for:",
        eventName,
        "TESTING_MODE:",
        window.TESTING_MODE
      );
      const event = new CustomEvent(`quiz:${eventName}`, {
        detail: { ...data, timestamp: Date.now() },
      });
      document.dispatchEvent(event);
      console.log(`DEBUG: Emitted event quiz:${eventName}`, data);
    },

    init() {
      console.log("DEBUG: quizApp component init() entered.");
      if (initialized) {
        console.log("DEBUG: init() skipped - already initialized.");
        return;
      }
      initialized = true;
      console.log(
        "DEBUG: quizApp component init() running for the first time."
      );

      window.TESTING_MODE = true;
      console.log("DEBUG: window.TESTING_MODE set to true at start of init.");

      const dataElement = document.getElementById("quiz-data");
      if (dataElement) {
        try {
          this.questions = JSON.parse(dataElement.textContent || "[]");
          console.log("DEBUG: Quiz data loaded successfully:", this.questions);
          this.userAnswers = Array(this.questions.length).fill(null);
        } catch (e) {
          console.error("Failed to parse quiz data from #quiz-data:", e);
          this.questions = [];
          this.userAnswers = [];
        }
      } else {
        console.warn("Quiz data element (#quiz-data) not found in HTML.");
        this.questions = [];
        this.userAnswers = [];
      }

      this.currentQuestionIndex = 0;
      this.selectedOptionIndex = null;
      this.isAnswered = false;
      this.quizCompleted = false;
      this.score = 0;
      this.wrongAnswers = 0;
      this.startTime = new Date();
      this.endTime = null;
      this.quizTime = 0;

      if (this.feedbackTimer) {
        clearTimeout(this.feedbackTimer);
        this.feedbackTimer = null;
        console.log("DEBUG: Cleared existing feedback timer in init.");
      }

      window.quizAppInstance = this;
      console.log(
        "DEBUG: Alpine instance assigned to window.quizAppInstance for testing."
      );

      if (this.questions.length === 0) {
        console.warn("No questions loaded, quiz cannot start.");
      } else {
        console.log(
          "Quiz initialized with",
          this.questions.length,
          "questions."
        );
      }

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

      this.selectedOptionIndex = index;
      this.isAnswered = true;

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

      const wasCorrect = this.isCorrect;
      if (wasCorrect) {
        this.score++;
        console.log("DEBUG: Correct Answer! Score:", this.score);
      } else {
        this.wrongAnswers++;
        console.log(
          "DEBUG: Incorrect Answer! Wrong answers:",
          this.wrongAnswers
        );
      }

      this.emitQuizEvent("answer-selected", {
        questionIndex: this.currentQuestionIndex,
        selectedIndex: index,
        isCorrect: wasCorrect,
      });

      if (this.feedbackTimer) {
        clearTimeout(this.feedbackTimer);
        console.log(
          "DEBUG: Cleared existing feedback timer before setting new one."
        );
      }

      const feedbackDuration = wasCorrect
        ? this.correctFeedbackDuration
        : this.incorrectFeedbackDuration;

      console.log(
        `DEBUG: Using feedback duration: ${feedbackDuration}ms (${
          wasCorrect ? "correct" : "incorrect"
        } answer)`
      );
      console.log(
        `DEBUG: Next question will appear in ${feedbackDuration / 1000} seconds.`
      );

      console.log("DEBUG: Setting timer for nextQuestion...");
      this.feedbackTimer = setTimeout(() => {
        console.log(
          "DEBUG: setTimeout callback executing, calling nextQuestion..."
        );
        this.nextQuestion();
      }, feedbackDuration);
    },

    nextQuestion() {
      console.log(
        "DEBUG: nextQuestion entered. Current index:",
        this.currentQuestionIndex
      );
      if (this.feedbackTimer) {
        clearTimeout(this.feedbackTimer);
        this.feedbackTimer = null;
        console.log("DEBUG: Cleared feedback timer at start of nextQuestion.");
      }

      if (this.currentQuestionIndex < this.questions.length - 1) {
        this.currentQuestionIndex++;
        console.log(
          `DEBUG: Advanced to question ${this.currentQuestionIndex + 1}`
        );
        this.isAnswered = false;
        this.selectedOptionIndex = null;

        console.log("DEBUG: About to emit quiz:question-changed...");
        this.emitQuizEvent("question-changed", {
          questionIndex: this.currentQuestionIndex,
        });
      } else {
        this.quizCompleted = true;
        this.endTime = new Date();
        this.calculateQuizTime();
        console.log("DEBUG: Quiz completed. Final score:", this.score);

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
      initialized = false;
      this.init();
      console.log("DEBUG: About to emit quiz:quiz-restarted...");
      this.emitQuizEvent("quiz-restarted", {});
    },

    // --- Helper Methods for Results (unchanged) ---
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
      if (!seconds && seconds !== 0) return "--:--";
      if (seconds === 0) return "00:00";

      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes.toString().padStart(2, "0")}:${remainingSeconds
        .toString()
        .padStart(2, "0")}`;
    },

    // --- Dynamic Class Logic (MODIFIED FOR INSTANT HIDE) ---
    getOptionClass(index) {
      if (!this.currentQuestion) {
        // Default classes if no question - Use original default return
        return "option-button p-4 rounded-xl font-semibold text-lg md:text-lg sm:text-base text-center transition-all duration-200 ease-in-out border-none cursor-pointer relative overflow-hidden shadow-md flex flex-col items-center justify-center bg-slate-700 text-gray-200";
      }

      // Original base classes including original transition
      let baseClasses = [
        "option-button",
        "p-4",
        "rounded-xl",
        "font-semibold",
        "text-base",
        "text-center",
        "transition-all",
        "duration-200",
        "ease-in-out", // ORIGINAL transition
        "border-none",
        "cursor-pointer",
        "relative",
        "overflow-hidden", //"shadow-md",
        "flex",
        "flex-col",
        "items-center",
        "justify-center",
        "disabled:opacity-100",
        "disabled:cursor-not-allowed",
      ];

      // State 1: Question NOT Answered Yet (Original Logic)
      if (!this.isAnswered) {
        const colorClasses = [
          "bg-teal-300 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-blue-300 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-yellow-300 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-purple-400 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-pink-400 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
        ];
        baseClasses.push(colorClasses[index % colorClasses.length]);
        baseClasses.push("visible"); // Ensure visibility
        return baseClasses.join(" ");
      }
      // State 2: Question HAS Been Answered (Feedback Time!)
      else {
        const actualAnswerIndex = this.currentQuestion.answerIndex;
        const userChoiceIndex = this.selectedOptionIndex;
        let feedbackClasses = ""; // Used for correct/incorrect cases

        if (index === actualAnswerIndex) {
          // Correct answer - Original logic: combine filtered base + effect
          feedbackClasses = correctFeedbackEffect; // Defined globally
          const filteredBase = baseClasses.filter(
            (cls) =>
              !cls.startsWith("hover:") &&
              !cls.startsWith("active:") &&
              cls !== "visible"
          );
          return filteredBase.join(" ") + " " + feedbackClasses; // Apply transition
        } else if (index === userChoiceIndex) {
          // User's incorrect choice - Original logic: combine filtered base + specific red style
          feedbackClasses = "visible !bg-red-500 !text-white shadow-lg"; // Explicitly visible, red background
          const filteredBase = baseClasses.filter(
            (cls) =>
              !cls.startsWith("hover:") &&
              !cls.startsWith("active:") &&
              cls !== "visible"
          );
          return filteredBase.join(" ") + " " + feedbackClasses; // Apply transition

          // --- INSTANT HIDE using CSS class ---
        } else {
          // Other options disappear instantly using CSS class.
          // Return *ONLY* the CSS class name. This replaces all other classes.
          return "option-hidden-immediately"; // NO transition will apply here
          // --- INSTANT HIDE using CSS class ---
        }
      }
    }, // End of getOptionClass
  }; // End of returned object
}; // End of quizApp function

// Original registration logic
console.log(
  "quizApp component function defined. Registered globally via window.quizApp."
);
