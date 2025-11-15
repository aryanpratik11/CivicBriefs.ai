const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema(
  {
    name: { type: String, required: true, trim: true },
    email: { type: String, required: true, unique: true, lowercase: true, trim: true },
    phoneNumber: { type: String, required: true, trim: true },
    password: { type: String, required: true },
    testScores: [
      {
        date: { type: Date, required: true },
        sections: {
          polity: { type: Number, required: true, min: 0 },
          economy: { type: Number, required: true, min: 0 },
          history: { type: Number, required: true, min: 0 },
          geography: { type: Number, required: true, min: 0 },
          environment: { type: Number, required: true, min: 0 },
          scienceTech: { type: Number, required: true, min: 0 },
          currentAffairs: { type: Number, required: true, min: 0 }
        }
      }
    ]
  },
  { timestamps: true }
);

module.exports = mongoose.model('User', UserSchema);
