import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { toast } from 'sonner';
import { useNavigate, useLocation } from 'react-router-dom';
import { Clock, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AssessmentPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { sessionId, questions, topic, technique } = location.state || {};

  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState([]);
  const [timer, setTimer] = useState(0);
  const [startTime, setStartTime] = useState(Date.now());
  const [completed, setCompleted] = useState(false);
  const [score, setScore] = useState(0);

  useEffect(() => {
    if (!sessionId || !questions) {
      navigate('/dashboard');
      return;
    }

    const interval = setInterval(() => {
      setTimer((Date.now() - startTime) / 1000);
    }, 100);

    return () => clearInterval(interval);
  }, [startTime]);

  const currentQuestion = questions?.[currentIndex];
  const expectedTime = currentQuestion?.expected_time || 60;
  const timeRatio = timer / expectedTime;

  const handleAnswerChange = (value) => {
    setAnswers({ ...answers, [currentQuestion.id]: value });
  };

  const submitAnswer = async () => {
    const answer = answers[currentQuestion.id];
    if (!answer || answer.trim() === '') {
      toast.error('Please provide an answer');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/learning/evaluate-answer`,
        {
          session_id: sessionId,
          question_id: currentQuestion.id,
          answer,
          time_taken: timer
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setResults([...results, response.data]);
      if (response.data.is_correct) {
        setScore(score + 1);
      }

      toast.success(response.data.feedback, {
        icon: response.data.is_correct ? '✅' : '❌'
      });

      // Move to next question or finish
      if (currentIndex < questions.length - 1) {
        setCurrentIndex(currentIndex + 1);
        setTimer(0);
        setStartTime(Date.now());
      } else {
        setCompleted(true);
      }
    } catch (error) {
      toast.error('Failed to submit answer');
    }
  };

  const finishAssessment = () => {
    const passed = score >= 4;
    if (passed) {
      toast.success(
        `Great job! You scored ${score}/6. You can skip the remaining techniques!`,
        { duration: 5000 }
      );
    } else {
      toast.info(
        `You scored ${score}/6. Try another learning technique to improve!`,
        { duration: 5000 }
      );
    }
    navigate('/dashboard');
  };

  if (!questions || questions.length === 0) {
    return (
      <div className="min-h-screen bg-[#020617] flex items-center justify-center">
        <p className="text-[#94a3b8]">Loading questions...</p>
      </div>
    );
  }

  if (completed) {
    return (
      <div className="min-h-screen bg-[#020617] flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl max-w-md neon-glow" data-testid="assessment-results-card">
            <CardContent className="p-12 text-center">
              <div className="mb-6">
                {score >= 4 ? (
                  <CheckCircle className="w-24 h-24 text-[#a3e635] mx-auto" />
                ) : (
                  <XCircle className="w-24 h-24 text-[#facc15] mx-auto" />
                )}
              </div>
              <h2 className="text-4xl font-bold text-[#f8fafc] mb-4">Assessment Complete!</h2>
              <div className="text-6xl font-bold text-[#22d3ee] mb-6">{score}/6</div>
              <p className="text-[#94a3b8] mb-8">
                {score >= 4
                  ? 'Excellent work! You can move to the next topic.'
                  : 'Good effort! Try another technique to improve your understanding.'}
              </p>
              <Button
                onClick={finishAssessment}
                size="lg"
                className="w-full rounded-full bg-[#22d3ee] text-[#020617] hover:bg-[#22d3ee]/90 font-bold py-6"
                data-testid="finish-assessment-btn"
              >
                Continue
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#020617]">
      {/* Progress Bar */}
      <div className="w-full h-2 bg-[#1e293b]">
        <div
          className="h-full bg-[#22d3ee] transition-all duration-300"
          style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
        ></div>
      </div>

      <div className="container mx-auto px-6 md:px-12 py-12 max-w-3xl">
        <motion.div
          key={currentIndex}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl neon-glow" data-testid="question-card">
            <CardContent className="p-8 md:p-12">
              {/* Timer and Question Number */}
              <div className="flex justify-between items-center mb-8">
                <span className="text-[#94a3b8]">
                  Question {currentIndex + 1} of {questions.length}
                </span>
                <div
                  className={`flex items-center gap-2 font-mono text-xl ${
                    timeRatio > 1.5 ? 'timer-danger' : timeRatio > 1 ? 'timer-warning' : 'text-[#a3e635]'
                  }`}
                  data-testid="question-timer"
                >
                  <Clock className="w-5 h-5" />
                  {Math.floor(timer)}s
                </div>
              </div>

              {/* Question */}
              <div className="mb-8">
                <div className="text-sm text-[#22d3ee] mb-2 uppercase tracking-wide">
                  {currentQuestion.type === 'mcq' ? 'Multiple Choice' : 'Short Answer'}
                </div>
                <h2 className="text-2xl md:text-3xl font-bold text-[#f8fafc] mb-6">
                  {currentQuestion.question}
                </h2>

                {/* MCQ Options */}
                {currentQuestion.type === 'mcq' && (
                  <RadioGroup
                    value={answers[currentQuestion.id] || ''}
                    onValueChange={handleAnswerChange}
                    className="space-y-4"
                  >
                    {currentQuestion.options.map((option, idx) => (
                      <div
                        key={idx}
                        className="flex items-center space-x-3 p-4 rounded-2xl border border-[#1e293b] hover:border-[#22d3ee] transition-colors cursor-pointer bg-[#1e293b]/50"
                      >
                        <RadioGroupItem value={option} id={`option-${idx}`} data-testid={`mcq-option-${idx}`} />
                        <Label htmlFor={`option-${idx}`} className="text-[#f8fafc] cursor-pointer flex-1">
                          {option}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                )}

                {/* Short Answer */}
                {currentQuestion.type === 'short' && (
                  <Textarea
                    placeholder="Type your answer here..."
                    value={answers[currentQuestion.id] || ''}
                    onChange={(e) => handleAnswerChange(e.target.value)}
                    className="bg-[#1e293b] border-transparent focus:border-[#22d3ee] text-[#f8fafc] rounded-2xl min-h-[150px] text-lg"
                    data-testid="short-answer-input"
                  />
                )}
              </div>

              {/* Submit Button */}
              <Button
                onClick={submitAnswer}
                size="lg"
                className="w-full rounded-full bg-[#22d3ee] text-[#020617] hover:bg-[#22d3ee]/90 font-bold py-6 text-lg"
                data-testid="submit-answer-btn"
              >
                Submit Answer
              </Button>

              {/* Expected Time Hint */}
              <div className="mt-4 text-center text-sm text-[#94a3b8]">
                Expected time: ~{expectedTime}s
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
