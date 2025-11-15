const mongoose = require('mongoose');

const QuestionSchema = new mongoose.Schema(
  {
    question_id: { type: String, required: true, unique: true },
    stage: { type: String, required: true },
    subject: { type: String, required: true },
    topic: { type: String, required: true },
    difficulty: { type: String, enum: ['Easy', 'Medium', 'Hard'], required: true },
    question: { type: String, required: true },
    options: {
      A: { type: String, required: true },
      B: { type: String, required: true },
      C: { type: String, required: true },
      D: { type: String, required: true }
    },
    correct_answer: { type: String, enum: ['A', 'B', 'C', 'D'], required: true }
  },
  { timestamps: true }
);

module.exports = mongoose.model('Question', QuestionSchema);
