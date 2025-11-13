
import { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Send } from 'lucide-react';

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
            // Assuming the backend is running on the same host
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
        <div className="container mx-auto p-4 sm:p-6 lg:p-8">
            <div className="max-w-2xl mx-auto">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">Submit Feedback</h1>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                    Have a suggestion, a bug report, or some feedback on the bot? We'd love to hear it! Your input is valuable in helping us improve.
                </p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="feedback-text" className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">
                            Your Feedback
                        </label>
                        <textarea
                            id="feedback-text"
                            rows={8}
                            className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                            value={feedback}
                            onChange={(e) => setFeedback(e.target.value)}
                            placeholder="I think it would be great if..."
                            disabled={isLoading}
                        />
                    </div>

                    <div className="text-right">
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400 disabled:cursor-not-allowed"
                        >
                            <Send className="-ml-1 mr-2 h-5 w-5" />
                            {isLoading ? 'Submitting...' : 'Submit Feedback'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default FeedbackPage;
