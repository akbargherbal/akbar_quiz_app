// src/multi_choice_quiz/static/multi_choice_quiz/app.js (MODIFIED for Step 6.1 & 6.2)

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
    userAnswers: [], // Tracks basic correct/incorrect - may be less relevant now
    selectedOptionIndex: null,
    isAnswered: false,
    quizCompleted: false,
    score: 0,
    wrongAnswers: 0, // Tracks count of wrong answers
    feedbackTimer: null,
    correctFeedbackDuration: 4000,
    incorrectFeedbackDuration: 6000,
    startTime: null,
    endTime: null,
    quizTime: 0,
    detailedAnswers: {}, // <<< STEP 6.1: Object to store {questionId: selectedOptionIndex}
    quizId: null,

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
      // ... (no change)
      const totalQuestions = this.questions.length;
      if (totalQuestions === 0) return "☆☆☆☆☆";

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
      const event = new CustomEvent(`quiz:${eventName}`, {
        detail: { ...data, timestamp: Date.now() },
      });
      document.dispatchEvent(event);
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

      this.detailedAnswers = {}; // <<< STEP 6.1: Reset on init

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

      const container = document.getElementById("quiz-app-container");
      this.quizId = container ? container.dataset.quizId : null;
      if (!this.quizId) {
        console.warn(
          "Could not find quiz ID (data-quiz-id attribute on container). Results submission might fail."
        );
      } else {
        console.log("DEBUG: Quiz ID loaded:", this.quizId);
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

      window.quizAppInstance = this; // For testing/debugging
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
        quizId: this.quizId,
      });

      console.log("DEBUG: quizApp component init() finished.");
    },

    selectOption(index) {
      if (this.isAnswered || !this.currentQuestion) {
        console.log(
          "DEBUG: Selection ignored - already answered or no current question"
        );
        return;
      }

      this.selectedOptionIndex = index;
      this.isAnswered = true;

      // --- START STEP 6.1 LOGIC ---
      if (this.currentQuestion && this.currentQuestion.id) {
          const questionId = this.currentQuestion.id;
          // Store user's selected index (0-based) against the question ID
          this.detailedAnswers[questionId] = index;
          console.log(`DEBUG: Recorded answer for QID ${questionId}: Selected Index ${index}`);
      } else {
           console.error("DEBUG: Could not record detailed answer - currentQuestion or ID missing.");
      }
      // --- END STEP 6.1 LOGIC ---

      // Update basic answer tracking array (less important now?)
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

      // Update score/wrong answer count
      const wasCorrect = this.isCorrect;
      if (wasCorrect) {
        this.score++;
      } else {
        this.wrongAnswers++;
      }

      this.emitQuizEvent("answer-selected", {
        questionIndex: this.currentQuestionIndex,
        selectedIndex: index,
        isCorrect: wasCorrect,
      });

      // Handle feedback timer
      if (this.feedbackTimer) {
        clearTimeout(this.feedbackTimer);
      }
      const feedbackDuration = wasCorrect
        ? this.correctFeedbackDuration
        : this.incorrectFeedbackDuration;
      this.feedbackTimer = setTimeout(() => {
        this.nextQuestion();
      }, feedbackDuration);
    },

    nextQuestion() {
      if (this.feedbackTimer) {
        clearTimeout(this.feedbackTimer);
        this.feedbackTimer = null;
      }

      if (this.currentQuestionIndex < this.questions.length - 1) {
        this.currentQuestionIndex++;
        this.isAnswered = false;
        this.selectedOptionIndex = null;
        this.emitQuizEvent("question-changed", {
          questionIndex: this.currentQuestionIndex,
        });
      } else {
        this.quizCompleted = true;
        this.endTime = new Date();
        this.calculateQuizTime();
        console.log("DEBUG: Quiz completed. Final score:", this.score);
        this.emitQuizEvent("quiz-completed", {
          score: this.score,
          wrongAnswers: this.wrongAnswers,
          timeSeconds: this.quizTime,
          quizId: this.quizId,
        });
        this.submitResults(); // Submit results automatically
      }
    },

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
        quiz_id: parseInt(this.quizId, 10),
        score: this.score,
        total_questions: this.questions.length,
        percentage: this.calculatePercentage(),
        end_time: this.endTime
          ? this.endTime.toISOString()
          : new Date().toISOString(),
        // --- START STEP 6.2 CHANGE ---
        attempt_details: this.detailedAnswers // Add the collected detailed answers
        // --- END STEP 6.2 CHANGE ---
      };

      console.log("DEBUG: Submitting quiz results (with details):", payload); // Updated log message

      fetch("/quiz/submit_attempt/", { // Use the correct URL defined in urls.py
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // 'X-CSRFToken': getCookie('csrftoken') // Add later if required
        },
        body: JSON.stringify(payload),
      })
        .then((response) => {
          if (!response.ok) {
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

    restartQuiz() {
      console.log("DEBUG: Restarting quiz...");
      this.detailedAnswers = {}; // <<< STEP 6.1: Reset on restart
      initialized = false; // Reset initialization flag
      this.init(); // Re-initialize the component
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
      if (!seconds && seconds !== 0) return "--:--";
      if (seconds === 0) return "00:00";
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes.toString().padStart(2, "0")}:${remainingSeconds
        .toString()
        .padStart(2, "0")}`;
    },

    // --- Dynamic Class Logic (Unchanged) ---
    getOptionClass(index) {
      // ... (Keep the existing complex logic for feedback styles) ...
      if (!this.currentQuestion) {
        return "option-button p-4 rounded-xl font-semibold text-lg md:text-lg sm:text-base text-center transition-all duration-200 ease-in-out border-none cursor-pointer relative overflow-hidden shadow-md flex flex-col items-center justify-center bg-slate-700 text-gray-200";
      }

      let baseClasses = [
        "option-button", "p-4", "rounded-xl", "font-semibold", "text-base",
        "text-center", "transition-all", "duration-200", "ease-in-out",
        "border-none", "cursor-pointer", "relative", "overflow-hidden",
        "flex", "flex-col", "items-center", "justify-center",
        "disabled:opacity-100", "disabled:cursor-not-allowed",
      ];

      if (!this.isAnswered) {
        const colorClasses = [
          "bg-teal-300 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-blue-300 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-yellow-300 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-purple-400 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
          "bg-pink-400 text-slate-800 hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0 active:shadow-md",
        ];
        baseClasses.push(colorClasses[index % colorClasses.length]);
        baseClasses.push("visible");
        return baseClasses.join(" ");
      } else {
        const actualAnswerIndex = this.currentQuestion.answerIndex;
        const userChoiceIndex = this.selectedOptionIndex;
        let feedbackClasses = "";

        if (index === actualAnswerIndex) {
          feedbackClasses = correctFeedbackEffect;
          const filteredBase = baseClasses.filter(cls => !cls.startsWith("hover:") && !cls.startsWith("active:") && cls !== "visible");
          return filteredBase.join(" ") + " " + feedbackClasses;
        } else if (index === userChoiceIndex) {
          feedbackClasses = "visible !bg-red-500 !text-white shadow-lg";
          const filteredBase = baseClasses.filter(cls => !cls.startsWith("hover:") && !cls.startsWith("active:") && cls !== "visible");
          return filteredBase.join(" ") + " " + feedbackClasses;
        } else {
          return "option-hidden-immediately";
        }
      }
    }, // End of getOptionClass
  }; // End of returned object
}; // End of quizApp function

// --- CSRF Helper (Keep commented) ---
/*
function getCookie(name) { ... }
*/

console.log(
  "quizApp component function defined. Registered globally via window.quizApp."
);

// --- Define global correctFeedbackEffect ---
const glowSize = 2;
const glowBlur = glowSize * 4;
const glowOpacity = 0.8;
const scaleFactor = 105;
const pulseDuration = 1.5;

const correctFeedbackEffect = `
    visible !bg-green-500 !text-black scale-[${scaleFactor}%]
    shadow-[0_0_${glowBlur}px_${glowSize}px_rgba(255,255,255,${glowOpacity})]
    animate-[pulse-glow-scale_${pulseDuration}s_ease-in-out_infinite]
  `.trim().replace(/\s+/g, " ");