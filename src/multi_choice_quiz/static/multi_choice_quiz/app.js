// src/multi_choice_quiz/static/multi_choice_quiz/app.js (MODIFIED)

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
    userAnswers: [],
    selectedOptionIndex: null,
    isAnswered: false,
    quizCompleted: false,
    score: 0,
    wrongAnswers: 0,
    feedbackTimer: null,
    correctFeedbackDuration: 400,
    incorrectFeedbackDuration: 600,
    startTime: null,
    endTime: null,
    quizTime: 0,
    quizId: null, // <<< Add state for quiz ID

    // --- Computed Properties (Getters) ---
    get currentQuestion() {
      // ... (no change)
      return this.questions && this.questions.length > this.currentQuestionIndex
        ? this.questions[this.currentQuestionIndex]
        : null;
    },
    get isCorrect() {
      // ... (no change)
      return this.currentQuestion && this.selectedOptionIndex !== null
        ? this.selectedOptionIndex === this.currentQuestion.answerIndex
        : null;
    },
    get starRatingDisplay() {
      // ... (no change)
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
      // ... (no change)
      // console.log( // Keep this commented unless debugging events specifically
      //   "DEBUG: emitQuizEvent called for:",
      //   eventName,
      //   "TESTING_MODE:",
      //   window.TESTING_MODE
      // );
      const event = new CustomEvent(`quiz:${eventName}`, {
        detail: { ...data, timestamp: Date.now() },
      });
      document.dispatchEvent(event);
      // console.log(`DEBUG: Emitted event quiz:${eventName}`, data); // Keep this commented unless debugging events
    },

    init() {
      // ... (previous init logic)
      console.log("DEBUG: quizApp component init() entered.");
      if (initialized) {
        console.log("DEBUG: init() skipped - already initialized.");
        return;
      }
      initialized = true;
      console.log(
        "DEBUG: quizApp component init() running for the first time."
      );

      // window.TESTING_MODE = true; // Keep for now if tests rely on it
      // console.log("DEBUG: window.TESTING_MODE set to true at start of init.");

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

      // <<< START: Get Quiz ID from data attribute >>>
      const container = document.getElementById("quiz-app-container");
      this.quizId = container ? container.dataset.quizId : null;
      if (!this.quizId) {
        console.warn(
          "Could not find quiz ID (data-quiz-id attribute on container). Results submission might fail."
        );
      } else {
        console.log("DEBUG: Quiz ID loaded:", this.quizId);
      }
      // <<< END: Get Quiz ID >>>

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
        quizId: this.quizId, // Include quizId in event
      });

      console.log("DEBUG: quizApp component init() finished.");
    },

    selectOption(index) {
      // ... (no change)
      // console.log(`DEBUG: selectOption(${index}) called.`);
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
        // console.log("DEBUG: Correct Answer! Score:", this.score);
      } else {
        this.wrongAnswers++;
        // console.log(
        //   "DEBUG: Incorrect Answer! Wrong answers:",
        //   this.wrongAnswers
        // );
      }

      this.emitQuizEvent("answer-selected", {
        questionIndex: this.currentQuestionIndex,
        selectedIndex: index,
        isCorrect: wasCorrect,
      });

      if (this.feedbackTimer) {
        clearTimeout(this.feedbackTimer);
        // console.log( // Keep commented unless debugging timers
        //   "DEBUG: Cleared existing feedback timer before setting new one."
        // );
      }

      const feedbackDuration = wasCorrect
        ? this.correctFeedbackDuration
        : this.incorrectFeedbackDuration;

      // console.log( // Keep commented unless debugging timers
      //   `DEBUG: Using feedback duration: ${feedbackDuration}ms (${
      //     wasCorrect ? "correct" : "incorrect"
      //   } answer)`
      // );
      // console.log( // Keep commented unless debugging timers
      //   `DEBUG: Next question will appear in ${feedbackDuration / 1000} seconds.`
      // );

      // console.log("DEBUG: Setting timer for nextQuestion..."); // Keep commented unless debugging timers
      this.feedbackTimer = setTimeout(() => {
        // console.log( // Keep commented unless debugging timers
        //   "DEBUG: setTimeout callback executing, calling nextQuestion..."
        // );
        this.nextQuestion();
      }, feedbackDuration);
    },

    nextQuestion() {
      // console.log( // Keep commented unless debugging nextQuestion
      //   "DEBUG: nextQuestion entered. Current index:",
      //   this.currentQuestionIndex
      // );
      if (this.feedbackTimer) {
        clearTimeout(this.feedbackTimer);
        this.feedbackTimer = null;
        // console.log("DEBUG: Cleared feedback timer at start of nextQuestion."); // Keep commented unless debugging timers
      }

      if (this.currentQuestionIndex < this.questions.length - 1) {
        this.currentQuestionIndex++;
        // console.log( // Keep commented unless debugging nextQuestion
        //   `DEBUG: Advanced to question ${this.currentQuestionIndex + 1}`
        // );
        this.isAnswered = false;
        this.selectedOptionIndex = null;

        // console.log("DEBUG: About to emit quiz:question-changed..."); // Keep commented unless debugging events
        this.emitQuizEvent("question-changed", {
          questionIndex: this.currentQuestionIndex,
        });
      } else {
        this.quizCompleted = true;
        this.endTime = new Date();
        this.calculateQuizTime();
        console.log("DEBUG: Quiz completed. Final score:", this.score);

        // console.log("DEBUG: About to emit quiz:quiz-completed..."); // Keep commented unless debugging events
        this.emitQuizEvent("quiz-completed", {
          score: this.score,
          wrongAnswers: this.wrongAnswers,
          timeSeconds: this.quizTime,
          quizId: this.quizId,
        });

        // <<< CALL SUBMIT RESULTS HERE >>>
        this.submitResults();
      }
      // console.log("DEBUG: nextQuestion finished."); // Keep commented unless debugging nextQuestion
    },

    // <<< START NEW METHOD >>>
    submitResults() {
      if (!this.quizId) {
        console.error("Cannot submit results: Quiz ID is missing.");
        return;
      }
      if (!this.quizCompleted) {
        console.warn("Attempted to submit results before quiz was completed.");
        return;
      }

      const payload = {
        quiz_id: parseInt(this.quizId, 10), // Ensure quiz_id is an integer
        score: this.score,
        total_questions: this.questions.length,
        percentage: this.calculatePercentage(),
        // Send end time in ISO format (UTC)
        end_time: this.endTime
          ? this.endTime.toISOString()
          : new Date().toISOString(),
        // Add attempt_details later (Phase 6)
        // attempt_details: { /* structure based on Req 6.c */ }
      };

      console.log("DEBUG: Submitting quiz results:", payload);

      fetch("/quiz/submit_attempt/", { // Use the correct URL defined in urls.py
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // IMPORTANT: CSRF token handling needed if not using @csrf_exempt
          // 'X-CSRFToken': getCookie('csrftoken') // Add this later if required
        },
        body: JSON.stringify(payload),
      })
        .then((response) => {
          if (!response.ok) {
            // Attempt to read error details if possible
            return response.text().then((text) => {
              throw new Error(
                `HTTP error ${response.status}: ${text || response.statusText}`
              );
            });
          }
          return response.json();
        })
        .then((result) => {
          console.log("DEBUG: Submission successful:", result);
          this.emitQuizEvent("results-submitted", {
            attemptId: result.attempt_id,
          });
        })
        .catch((error) => {
          console.error("DEBUG: Error submitting quiz results:", error);
          this.emitQuizEvent("results-submission-failed", {
            error: error.message,
          });
          // Optionally show a user-facing error message here
        });
    },
    // <<< END NEW METHOD >>>

    restartQuiz() {
      // ... (no change)
      console.log("DEBUG: Restarting quiz...");
      initialized = false; // Reset initialization flag
      this.init(); // Re-initialize the component
      // console.log("DEBUG: About to emit quiz:quiz-restarted..."); // Keep commented unless debugging events
      this.emitQuizEvent("quiz-restarted", {});
    },

    // --- Helper Methods for Results (unchanged) ---
    calculatePercentage() {
      // ... (no change)
      if (this.questions.length === 0) return 0;
      return Math.round((this.score / this.questions.length) * 100);
    },

    calculateQuizTime() {
      // ... (no change)
      if (!this.startTime || !this.endTime) return 0;
      this.quizTime = Math.floor((this.endTime - this.startTime) / 1000);
      return this.quizTime;
    },

    formatTime(seconds) {
      // ... (no change)
      if (!seconds && seconds !== 0) return "--:--";
      if (seconds === 0) return "00:00";

      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes.toString().padStart(2, "0")}:${remainingSeconds
        .toString()
        .padStart(2, "0")}`;
    },

    // --- Dynamic Class Logic (Unchanged from previous state) ---
    getOptionClass(index) {
      // ... (Keep the existing complex logic for feedback styles) ...
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
        } else {
          // Other options disappear instantly using CSS class.
          return "option-hidden-immediately"; // NO transition will apply here
        }
      }
    }, // End of getOptionClass
  }; // End of returned object
}; // End of quizApp function

// Helper function to get CSRF token (Keep commented for now, uncomment if needed)
/*
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
*/

// Original registration logic
console.log(
  "quizApp component function defined. Registered globally via window.quizApp."
);

// --- Define global correctFeedbackEffect (ensure it's defined before use) ---
const glowSize = 2;
const glowBlur = glowSize * 4;
const glowOpacity = 0.8;
const scaleFactor = 105;
const pulseDuration = 1.5; // seconds

// Base effect class string
const correctFeedbackEffect = `
    visible
    !bg-green-500
    !text-black
    scale-[${scaleFactor}%]
    shadow-[0_0_${glowBlur}px_${glowSize}px_rgba(255,255,255,${glowOpacity})]
    animate-[pulse-glow-scale_${pulseDuration}s_ease-in-out_infinite]
  `
  .trim()
  .replace(/\s+/g, " ");