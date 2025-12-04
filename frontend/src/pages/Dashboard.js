import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Video, GitBranch, LogOut, TrendingUp, Clock, Target } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchProgress();
  }, []);

  const fetchProgress = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/progress`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProgress(response.data);
    } catch (error) {
      console.error('Failed to fetch progress:', error);
    }
  };

  const startLearning = (technique) => {
    if (!topic.trim()) {
      toast.error('Please enter a topic to learn');
      return;
    }
    navigate('/learn', { state: { topic, technique } });
  };

  return (
    <div className="min-h-screen bg-[#020617]" data-testid="dashboard">
      {/* Header */}
      <div className="border-b border-[#1e293b] bg-[#0f172a]/50 backdrop-blur-xl">
        <div className="container mx-auto px-6 md:px-12 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-[#22d3ee]">BrainPath</h1>
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/performance')}
              className="text-[#f8fafc] hover:text-[#22d3ee]"
              data-testid="view-analytics-btn"
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              Analytics
            </Button>
            <Button
              variant="ghost"
              onClick={onLogout}
              className="text-[#f8fafc] hover:text-[#f87171]"
              data-testid="logout-btn"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 md:px-12 lg:px-16 py-12">
        {/* Bento Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Welcome Section - Span 2 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-2"
          >
            <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl h-full neon-glow" data-testid="welcome-card">
              <CardHeader>
                <CardTitle className="text-3xl text-[#f8fafc]">
                  Welcome back! 👋
                </CardTitle>
                <p className="text-[#94a3b8] mt-2">
                  {user?.email} • {user?.education_level}
                  {user?.sub_level && ` • ${user.sub_level}`}
                </p>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <Label htmlFor="topic" className="text-[#f8fafc] text-lg">What do you want to learn today?</Label>
                    <Input
                      id="topic"
                      placeholder="Enter any topic (e.g., Photosynthesis, Python Programming, Ancient History)"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      className="mt-2 bg-[#1e293b] border-transparent focus:border-[#22d3ee] text-[#f8fafc] rounded-2xl text-lg py-6"
                      data-testid="topic-input"
                    />
                  </div>

                  <div>
                    <p className="text-[#94a3b8] mb-4">Choose your learning technique:</p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Button
                        onClick={() => startLearning('passage')}
                        disabled={loading}
                        className="h-auto py-6 rounded-2xl bg-[#0f172a] border border-[#22d3ee] text-[#f8fafc] hover:bg-[#1e293b] hover:scale-105 transition-all"
                        data-testid="technique-passage-btn"
                      >
                        <div className="flex flex-col items-center gap-2">
                          <BookOpen className="w-8 h-8 text-[#22d3ee]" />
                          <span className="font-bold">Passage</span>
                          <span className="text-xs text-[#94a3b8]">Read & Learn</span>
                        </div>
                      </Button>

                      <Button
                        onClick={() => startLearning('video')}
                        disabled={loading}
                        className="h-auto py-6 rounded-2xl bg-[#0f172a] border border-[#f472b6] text-[#f8fafc] hover:bg-[#1e293b] hover:scale-105 transition-all"
                        data-testid="technique-video-btn"
                      >
                        <div className="flex flex-col items-center gap-2">
                          <Video className="w-8 h-8 text-[#f472b6]" />
                          <span className="font-bold">Video</span>
                          <span className="text-xs text-[#94a3b8]">Watch & Learn</span>
                        </div>
                      </Button>

                      <Button
                        onClick={() => startLearning('flowchart')}
                        disabled={loading}
                        className="h-auto py-6 rounded-2xl bg-[#0f172a] border border-[#a3e635] text-[#f8fafc] hover:bg-[#1e293b] hover:scale-105 transition-all"
                        data-testid="technique-flowchart-btn"
                      >
                        <div className="flex flex-col items-center gap-2">
                          <GitBranch className="w-8 h-8 text-[#a3e635]" />
                          <span className="font-bold">Flowchart</span>
                          <span className="text-xs text-[#94a3b8]">Visualize & Learn</span>
                        </div>
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Stats Section - Span 1 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="lg:col-span-1"
          >
            <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl h-full neon-glow" data-testid="stats-card">
              <CardHeader>
                <CardTitle className="text-xl text-[#f8fafc] flex items-center gap-2">
                  <Target className="w-5 h-5 text-[#22d3ee]" />
                  Your Progress
                </CardTitle>
              </CardHeader>
              <CardContent>
                {progress ? (
                  <div className="space-y-6">
                    <div className="text-center p-4 bg-[#1e293b] rounded-2xl">
                      <div className="text-4xl font-bold text-[#22d3ee]">{progress.accuracy}%</div>
                      <div className="text-sm text-[#94a3b8] mt-1">Accuracy</div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-[#1e293b] rounded-xl">
                        <span className="text-[#94a3b8]">Sessions</span>
                        <span className="text-[#f8fafc] font-bold">{progress.completed_sessions}/{progress.total_sessions}</span>
                      </div>

                      <div className="flex justify-between items-center p-3 bg-[#1e293b] rounded-xl">
                        <span className="text-[#94a3b8]">Questions</span>
                        <span className="text-[#f8fafc] font-bold">{progress.correct_answers}/{progress.total_questions}</span>
                      </div>

                      <div className="flex justify-between items-center p-3 bg-[#1e293b] rounded-xl">
                        <span className="text-[#94a3b8] flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          Fast
                        </span>
                        <span className="text-[#a3e635] font-bold">{progress.speed_analysis.fast}</span>
                      </div>

                      <div className="flex justify-between items-center p-3 bg-[#1e293b] rounded-xl">
                        <span className="text-[#94a3b8] flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          Optimal
                        </span>
                        <span className="text-[#22d3ee] font-bold">{progress.speed_analysis.optimal}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-[#94a3b8] py-8">
                    <p>Start learning to see your progress!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
