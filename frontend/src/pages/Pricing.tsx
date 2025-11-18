import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Check, Zap, Sparkles, Crown } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { logger } from '../utils/logger';

interface PricingPlan {
  id: string;
  name: string;
  price: number;
  currency: string;
  interval: string;
  features: string[];
  listing_limit: number;
  popular?: boolean;
  icon: React.ReactNode;
}

export default function Pricing() {
  const [plans, setPlans] = useState<Record<string, PricingPlan>>({});
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${API_URL}/api/v1/payments/plans`);

      if (!response.ok) throw new Error('Failed to fetch plans');

      const data = await response.json();
      setPlans(data.plans);
    } catch (error) {
      // LOW BUG FIX: Use logger instead of console.error
      logger.error('Error fetching plans:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load pricing plans'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planId: string) => {
    if (planId === 'free') {
      navigate('/register');
      return;
    }

    setCheckoutLoading(planId);

    try {
      const token = localStorage.getItem('token');

      if (!token) {
        navigate('/login?redirect=/pricing');
        return;
      }

      const API_URL = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${API_URL}/api/v1/payments/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          plan: planId,
          success_url: `${window.location.origin}/dashboard?payment=success`,
          cancel_url: `${window.location.origin}/pricing?payment=canceled`
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Checkout failed');
      }

      const data = await response.json();

      // Redirect to Stripe checkout
      window.location.href = data.checkout_url;

    } catch (error: any) {
      // LOW BUG FIX: Use logger instead of console.error
      logger.error('Checkout error:', error);
      toast({
        variant: 'destructive',
        title: 'Checkout Error',
        description: error.message || 'Failed to start checkout'
      });
      setCheckoutLoading(null);
    }
  };

  const getPlanIcon = (planId: string) => {
    switch (planId) {
      case 'free':
        return <Zap className="w-8 h-8" />;
      case 'starter':
        return <Sparkles className="w-8 h-8" />;
      case 'pro':
        return <Crown className="w-8 h-8" />;
      case 'enterprise':
        return <Crown className="w-8 h-8 text-yellow-500" />;
      default:
        return <Zap className="w-8 h-8" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Choose Your Perfect Plan
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Unlock the full power of VintedBot with premium features. Start for free, upgrade anytime.
        </p>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
        {Object.entries(plans).map(([planId, plan]) => (
          <Card
            key={planId}
            className={`relative p-6 flex flex-col ${
              plan.name === 'Pro' ? 'border-2 border-primary shadow-lg scale-105' : ''
            }`}
          >
            {plan.name === 'Pro' && (
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                <span className="bg-primary text-primary-foreground px-4 py-1 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
            )}

            <div className="mb-4">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
                {getPlanIcon(planId)}
              </div>

              <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>

              <div className="mb-4">
                {plan.price === 0 ? (
                  <div className="text-4xl font-bold">Free</div>
                ) : (
                  <div className="flex items-baseline">
                    <span className="text-4xl font-bold">€{(plan.price / 100).toFixed(2)}</span>
                    <span className="text-muted-foreground ml-2">/{plan.interval}</span>
                  </div>
                )}
              </div>

              <div className="mb-2 text-sm text-muted-foreground">
                {plan.listing_limit === -1 ? (
                  <span className="font-medium text-primary">Unlimited listings</span>
                ) : (
                  <span>{plan.listing_limit} listings/month</span>
                )}
              </div>
            </div>

            <ul className="space-y-3 mb-6 flex-grow">
              {plan.features.map((feature, index) => (
                <li key={index} className="flex items-start gap-2">
                  <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{feature}</span>
                </li>
              ))}
            </ul>

            <Button
              onClick={() => handleSubscribe(planId)}
              disabled={checkoutLoading === planId}
              variant={plan.name === 'Pro' ? 'default' : 'outline'}
              className="w-full"
            >
              {checkoutLoading === planId ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Loading...
                </>
              ) : planId === 'free' ? (
                'Get Started Free'
              ) : (
                'Subscribe Now'
              )}
            </Button>
          </Card>
        ))}
      </div>

      {/* FAQ Section */}
      <div className="mt-20 max-w-3xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-8">Frequently Asked Questions</h2>

        <div className="space-y-4">
          <Card className="p-6">
            <h3 className="font-semibold mb-2">Can I change my plan later?</h3>
            <p className="text-muted-foreground">
              Yes! You can upgrade or downgrade your plan at any time from your billing settings.
              Changes take effect immediately.
            </p>
          </Card>

          <Card className="p-6">
            <h3 className="font-semibold mb-2">What happens if I exceed my listing limit?</h3>
            <p className="text-muted-foreground">
              You'll be prompted to upgrade to a higher plan. Your existing listings remain active,
              but you won't be able to create new ones until you upgrade or wait for the next billing cycle.
            </p>
          </Card>

          <Card className="p-6">
            <h3 className="font-semibold mb-2">Is my payment information secure?</h3>
            <p className="text-muted-foreground">
              Absolutely! We use Stripe for payment processing, which is PCI-DSS compliant and trusted
              by millions of businesses worldwide. We never store your credit card information.
            </p>
          </Card>

          <Card className="p-6">
            <h3 className="font-semibold mb-2">Can I cancel anytime?</h3>
            <p className="text-muted-foreground">
              Yes, you can cancel your subscription at any time from the billing portal.
              You'll retain access to premium features until the end of your billing period.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
