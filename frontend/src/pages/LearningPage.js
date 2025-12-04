import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { toast } from 'sonner';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import Mermaid from 'react-mermaid2';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LearningPage({ user }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { topic, technique } = location.state || {};

  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!topic || !technique) {
      navigate('/dashboard');
      return;
    }
    generateContent();
  }, [topic, technique]);

  const generateContent = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/learning/generate-content`,
        { topic, technique },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setContent(response.data);
    } catch (error) {
      toast.error('Failed to generate content');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const proceedToQuestions = async () => {
    toast.info('Generating questions...');
    try {
      const token = localStorage.getItem('token');
      const contentStr = technique === 'passage' ? content.content : 
                         technique === 'video' ? JSON.stringify(content.content) :
                         content.content;
      
      const questionsResponse = await axios.post(
        `${API}/learning/generate-questions`,
        { topic, content: contentStr, technique, difficulty: 1 },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const sessionResponse = await axios.post(
        `${API}/learning/create-session`,
        {
          topic,
          technique,
          content: content.content,
          questions: questionsResponse.data.questions
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      navigate('/assess', {
        state: {
          sessionId: sessionResponse.data.session_id,
          questions: questionsResponse.data.questions,
          topic,
          technique
        }
      });
    } catch (error) {
      toast.error('Failed to generate questions');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#020617] flex items-center justify-center">
        <Loader2 className="w-12 h-12 text-[#22d3ee] animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#020617]">
      {/* Header */}
      <div className="border-b border-[#1e293b] bg-[#0f172a]/50 backdrop-blur-xl sticky top-0 z-10">
        <div className="container mx-auto px-6 md:px-12 py-4 flex justify-between items-center">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            className="text-[#f8fafc] hover:text-[#22d3ee]"
            data-testid="back-to-dashboard-btn"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <h1 className="text-xl font-bold text-[#22d3ee]">{topic}</h1>
          <div></div>
        </div>
      </div>

      <div className="container mx-auto px-6 md:px-12 lg:px-16 py-12 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="bg-[#0f172a] border-[#1e293b] rounded-3xl" data-testid="learning-content-card">
            <CardContent className="p-8 md:p-12">
              {technique === 'passage' && (
                <div className="prose prose-invert max-w-none">
                  <div className="text-[#f8fafc] text-base md:text-lg leading-relaxed whitespace-pre-wrap">
                    {content.content}
                  </div>
                </div>
              )}

              {technique === 'video' && content.content && (
                <div className="space-y-6">
                  <div className="aspect-video rounded-2xl overflow-hidden bg-black">
                    <iframe
                      width="100%"
                      height="100%"
                      src={`https://www.youtube.com/embed/${content.content.videoId}`}
                      title={content.content.title}
                      frameBorder="0"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                      data-testid="video-iframe"
                    ></iframe>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-[#f8fafc] mb-2">{content.content.title}</h3>
                    <p className="text-[#94a3b8]">{content.content.description}</p>
                  </div>
                </div>
              )}

              {technique === 'flowchart' && (
                <div className="bg-white p-6 rounded-2xl" data-testid="flowchart-container">
                  <Mermaid chart={content.content} />
                </div>
              )}

              <div className="mt-12 text-center">
                <Button
                  onClick={proceedToQuestions}
                  size="lg"
                  className="px-12 py-6 h-auto rounded-full bg-[#22d3ee] text-[#020617] hover:bg-[#22d3ee]/90 font-bold shadow-[0_0_15px_rgba(34,211,238,0.5)] hover:scale-105 transition-all"
                  data-testid="proceed-to-questions-btn"
                >
                  Continue to Questions
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
