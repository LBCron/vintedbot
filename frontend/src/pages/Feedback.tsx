import { useState } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Send, MessageSquare, Sparkles, Heart } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';

const FeedbackPage = () => {
  const [feedback, setFeedback] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (feedback.trim().length < 10) {
      toast.error('Please enter at least 10 characters for your feedback.');
      return;
    }

    setIsLoading(true);
    const toastId = toast.loading('Submitting your feedback...');

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
      await axios.post(`${apiUrl}/feedback`, { text: feedback });

      toast.success('Thank you for your feedback!', { id: toastId });
      setFeedback('');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'An error occurred.';
      toast.error(`Submission failed: ${errorMessage}`, { id: toastId });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="max-w-4xl mx-auto p-4 md:p-6 lg:p-8 space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4"
        >
          <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg shadow-violet-500/50">
            <MessageSquare className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent">
              Submit Feedback
            </h1>
            <p className="text-slate-400 mt-1">
              Help us improve VintedBot with your suggestions
            </p>
          </div>
        </motion.div>

        {/* Info Cards */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          <GlassCard hover className="p-6 text-center">
            <div className="p-3 bg-violet-500/20 rounded-xl border border-violet-500/30 w-fit mx-auto mb-3">
              <Sparkles className="w-6 h-6 text-violet-400" />
            </div>
            <h3 className="font-semibold text-white mb-1">Feature Requests</h3>
            <p className="text-sm text-slate-400">
              Got ideas for new features?
            </p>
          </GlassCard>

          <GlassCard hover className="p-6 text-center">
            <div className="p-3 bg-red-500/20 rounded-xl border border-red-500/30 w-fit mx-auto mb-3">
              <MessageSquare className="w-6 h-6 text-red-400" />
            </div>
            <h3 className="font-semibold text-white mb-1">Bug Reports</h3>
            <p className="text-sm text-slate-400">
              Found something broken?
            </p>
          </GlassCard>

          <GlassCard hover className="p-6 text-center">
            <div className="p-3 bg-green-500/20 rounded-xl border border-green-500/30 w-fit mx-auto mb-3">
              <Heart className="w-6 h-6 text-green-400" />
            </div>
            <h3 className="font-semibold text-white mb-1">General Feedback</h3>
            <p className="text-sm text-slate-400">
              Share your experience
            </p>
          </GlassCard>
        </motion.div>

        {/* Feedback Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <GlassCard className="p-8">
            <h2 className="text-2xl font-bold text-white mb-2">
              We'd Love to Hear From You
            </h2>
            <p className="text-slate-400 mb-6">
              Your input is valuable in helping us improve VintedBot. Share suggestions, report bugs, or just let us know how we're doing!
            </p>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="feedback-text" className="block text-sm font-medium text-slate-300 mb-2">
                  Your Feedback <span className="text-red-400">*</span>
                </label>
                <textarea
                  id="feedback-text"
                  rows={8}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 resize-none focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="I think it would be great if..."
                  disabled={isLoading}
                />
                <p className="text-xs text-slate-500 mt-2">
                  Minimum 10 characters. Be as detailed as you'd like!
                </p>
              </div>

              <div className="flex justify-end">
                <Button
                  type="submit"
                  disabled={isLoading || feedback.trim().length < 10}
                  loading={isLoading}
                  icon={Send}
                  size="lg"
                >
                  {isLoading ? 'Submitting...' : 'Submit Feedback'}
                </Button>
              </div>
            </form>
          </GlassCard>
        </motion.div>

        {/* Thank You Message */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <GlassCard className="p-6 bg-gradient-to-br from-violet-500/10 to-purple-500/10 border-violet-500/30">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-violet-500/20 rounded-xl border border-violet-500/30">
                <Heart className="w-6 h-6 text-violet-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-white mb-1">
                  Thank You for Your Support!
                </h3>
                <p className="text-sm text-slate-300">
                  Every piece of feedback helps us make VintedBot better. We read and consider all submissions carefully.
                </p>
              </div>
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
};

export default FeedbackPage;
