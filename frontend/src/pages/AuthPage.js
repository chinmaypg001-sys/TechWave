import { useState } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AuthPage({ onLogin }) {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [educationLevel, setEducationLevel] = useState('');
  const [subLevel, setSubLevel] = useState('');
  const [board, setBoard] = useState('');
  
  const [showSubLevel, setShowSubLevel] = useState(false);

  const handleEducationChange = (value) => {
    setEducationLevel(value);
    setShowSubLevel(value === 'school');
    if (value !== 'school') {
      setSubLevel('');
      setBoard('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        const response = await axios.post(`${API}/auth/login`, { email, password });
        toast.success('Login successful!');
        onLogin(response.data.token, response.data.user);
        navigate('/dashboard');
      } else {
        if (!educationLevel) {
          toast.error('Please select your education level');
          setLoading(false);
          return;
        }
        if (educationLevel === 'school' && (!subLevel || !board)) {
          toast.error('Please complete school details');
          setLoading(false);
          return;
        }
        
        const response = await axios.post(`${API}/auth/signup`, {
          email,
          password,
          education_level: educationLevel,
          sub_level: subLevel || null,
          board: board || null
        });
        toast.success('Account created successfully!');
        onLogin(response.data.token, response.data.user);
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] flex">
      {/* Left Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12">
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="w-full max-w-md"
        >
          <Card className="bg-[#0f172a]/80 backdrop-blur-xl border-[#1e293b] rounded-3xl neon-glow" data-testid="auth-form-card">
            <CardContent className="p-8">
              <h2 className="text-4xl font-bold text-[#22d3ee] mb-2">
                {isLogin ? 'Welcome Back' : 'Join BrainPath'}
              </h2>
              <p className="text-[#94a3b8] mb-8">
                {isLogin ? 'Sign in to continue learning' : 'Create your personalized learning journey'}
              </p>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <Label htmlFor="email" className="text-[#f8fafc]">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="your@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="bg-[#1e293b] border-transparent focus:border-[#22d3ee] text-[#f8fafc] rounded-2xl"
                    data-testid="auth-email-input"
                  />
                </div>

                <div>
                  <Label htmlFor="password" className="text-[#f8fafc]">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="bg-[#1e293b] border-transparent focus:border-[#22d3ee] text-[#f8fafc] rounded-2xl"
                    data-testid="auth-password-input"
                  />
                </div>

                {!isLogin && (
                  <>
                    <div>
                      <Label htmlFor="education" className="text-[#f8fafc]">Education Level</Label>
                      <Select value={educationLevel} onValueChange={handleEducationChange}>
                        <SelectTrigger className="bg-[#1e293b] border-transparent text-[#f8fafc] rounded-2xl" data-testid="education-level-select">
                          <SelectValue placeholder="Select level" />
                        </SelectTrigger>
                        <SelectContent className="bg-[#0f172a] border-[#1e293b] text-[#f8fafc]">
                          <SelectItem value="school">School</SelectItem>
                          <SelectItem value="college">College</SelectItem>
                          <SelectItem value="undergraduate">Undergraduate</SelectItem>
                          <SelectItem value="postgraduate">Postgraduate</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {showSubLevel && (
                      <>
                        <div>
                          <Label htmlFor="sublevel" className="text-[#f8fafc]">School Level</Label>
                          <Select value={subLevel} onValueChange={setSubLevel}>
                            <SelectTrigger className="bg-[#1e293b] border-transparent text-[#f8fafc] rounded-2xl" data-testid="school-sublevel-select">
                              <SelectValue placeholder="Select class" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#0f172a] border-[#1e293b] text-[#f8fafc]">
                              <SelectItem value="primary">Class 1-5 (Primary)</SelectItem>
                              <SelectItem value="middle">Class 6-8 (Middle School)</SelectItem>
                              <SelectItem value="high_school">Class 9-10 (High School)</SelectItem>
                              <SelectItem value="senior_secondary">Class 11-12 (Senior Secondary)</SelectItem>
                              <SelectItem value="competitive">JEE/NEET (Competitive)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div>
                          <Label htmlFor="board" className="text-[#f8fafc]">Board/Curriculum</Label>
                          <Select value={board} onValueChange={setBoard}>
                            <SelectTrigger className="bg-[#1e293b] border-transparent text-[#f8fafc] rounded-2xl" data-testid="board-select">
                              <SelectValue placeholder="Select board" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#0f172a] border-[#1e293b] text-[#f8fafc]">
                              <SelectItem value="cbse">CBSE (Central Board)</SelectItem>
                              <SelectItem value="icse">ICSE (Indian Certificate)</SelectItem>
                              <SelectItem value="state">State Board</SelectItem>
                              <SelectItem value="ncert">NCERT (General)</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </>
                    )}
                  </>
                )}

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-full bg-[#22d3ee] text-[#020617] hover:bg-[#22d3ee]/90 font-bold py-6 shadow-[0_0_15px_rgba(34,211,238,0.5)] hover:scale-105 transition-all"
                  data-testid="auth-submit-btn"
                >
                  {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
                </Button>
              </form>

              <div className="mt-6 text-center">
                <button
                  onClick={() => setIsLogin(!isLogin)}
                  className="text-[#22d3ee] hover:text-[#f472b6] transition-colors"
                  data-testid="auth-toggle-btn"
                >
                  {isLogin ? "Don't have an account? Sign Up" : 'Already have an account? Sign In'}
                </button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Right Side - Image */}
      <div className="hidden lg:block lg:w-1/2 relative">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: 'url(https://images.unsplash.com/photo-1629135310765-dcf5781f0ca3?crop=entropy&cs=srgb&fm=jpg&q=85)',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        >
          <div className="absolute inset-0 bg-[#22d3ee]/10"></div>
        </div>
      </div>
    </div>
  );
}
