import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, Clock, Target, Zap } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function PerformancePage() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [analyticsRes, progressRes] = await Promise.all([
        axios.get(`${API}/analytics/dashboard`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/progress`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setAnalytics(analyticsRes.data);
      setProgress(progressRes.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#020617] flex items-center justify-center">
        <div className="text-[#22d3ee]">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#020617]" data-testid="performance-dashboard">
      {/* Header */}
      <div className="border-b border-[#1e293b] bg-[#0f172a]/50 backdrop-blur-xl">
        <div className="container mx-auto px-6 md:px-12 py-4 flex justify-between items-center">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            className="text-[#f8fafc] hover:text-[#22d3ee]"
            data-testid="back-to-dashboard-btn"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          <h1 className="text-xl font-bold text-[#22d3ee]">Performance Analytics</h1>
          <div></div>
        </div>
      </div>

      <div className="container mx-auto px-6 md:px-12 lg:px-16 py-12">
        {/* Overall Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl neon-glow" data-testid="accuracy-card">
              <CardContent className="p-6 text-center">
                <Target className="w-12 h-12 text-[#22d3ee] mx-auto mb-4" />
                <div className="text-4xl font-bold text-[#22d3ee] mb-2">
                  {progress?.accuracy || 0}%
                </div>
                <div className="text-sm text-[#94a3b8]">Overall Accuracy</div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl neon-glow">
              <CardContent className="p-6 text-center">
                <TrendingUp className="w-12 h-12 text-[#a3e635] mx-auto mb-4" />
                <div className="text-4xl font-bold text-[#a3e635] mb-2">
                  {progress?.completed_sessions || 0}
                </div>
                <div className="text-sm text-[#94a3b8]">Completed Sessions</div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl neon-glow">
              <CardContent className="p-6 text-center">
                <Clock className="w-12 h-12 text-[#f472b6] mx-auto mb-4" />
                <div className="text-4xl font-bold text-[#f472b6] mb-2">
                  {analytics?.avg_time_per_question ? Math.round(analytics.avg_time_per_question) : 0}s
                </div>
                <div className="text-sm text-[#94a3b8]">Avg Time/Question</div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl neon-glow">
              <CardContent className="p-6 text-center">
                <Zap className="w-12 h-12 text-[#facc15] mx-auto mb-4" />
                <div className="text-4xl font-bold text-[#facc15] mb-2">
                  {progress?.total_questions || 0}
                </div>
                <div className="text-sm text-[#94a3b8]">Total Questions</div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Technique Performance */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mb-12"
        >
          <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl neon-glow">
            <CardHeader>
              <CardTitle className="text-2xl text-[#f8fafc]">Learning Technique Performance</CardTitle>
            </CardHeader>
            <CardContent>
              {analytics?.technique_performance && Object.keys(analytics.technique_performance).length > 0 ? (
                <div className="space-y-6">
                  {Object.entries(analytics.technique_performance).map(([technique, data]) => (
                    <div key={technique} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-[#f8fafc] capitalize font-semibold">{technique}</span>
                        <span className="text-[#22d3ee] font-bold">{data.accuracy}%</span>
                      </div>
                      <Progress value={data.accuracy} className="h-3" />
                      <div className="text-sm text-[#94a3b8]">
                        {data.correct} correct out of {data.total} questions
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-[#94a3b8] py-8">
                  <p>No technique data available yet. Start learning to see your performance!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Strengths & Weaknesses */}
        <div className="grid md:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl neon-glow" data-testid="strengths-card">
              <CardHeader>
                <CardTitle className="text-xl text-[#f8fafc] flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-[#a3e635]" />
                  Strengths
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analytics?.strengths && analytics.strengths.length > 0 ? (
                  <div className="space-y-2">
                    {analytics.strengths.map((strength, idx) => (
                      <div key={idx} className="p-3 bg-[#1e293b] rounded-xl text-[#a3e635] capitalize">
                        {strength}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[#94a3b8]">Complete more sessions to identify strengths</p>
                )}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
          >
            <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl neon-glow" data-testid="weaknesses-card">
              <CardHeader>
                <CardTitle className="text-xl text-[#f8fafc] flex items-center gap-2">
                  <Target className="w-5 h-5 text-[#facc15]" />
                  Areas for Improvement
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analytics?.weaknesses && analytics.weaknesses.length > 0 ? (
                  <div className="space-y-2">
                    {analytics.weaknesses.map((weakness, idx) => (
                      <div key={idx} className="p-3 bg-[#1e293b] rounded-xl text-[#facc15] capitalize">
                        {weakness}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[#94a3b8]">Great! No weak areas identified yet</p>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
