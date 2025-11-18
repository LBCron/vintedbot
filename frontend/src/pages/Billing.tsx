import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { CreditCard, Calendar, TrendingUp, ExternalLink, AlertCircle } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { paymentsAPI } from '../api/client';

interface SubscriptionInfo {
  plan: string;
  status: string;
  has_stripe_account: boolean;
  member_since: string;
}

interface PlanLimits {
  plan: string;
  status: string;
  limit: number;
  current_usage: number;
  can_create: boolean;
  remaining: number;
}

export default function Billing() {
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [limits, setLimits] = useState<PlanLimits | null>(null);
  const [loading, setLoading] = useState(true);
  const [portalLoading, setPortalLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    fetchBillingInfo();
  }, []);

  // SECURITY FIX Bug #1: Use paymentsAPI with HTTP-only cookies instead of localStorage
  const fetchBillingInfo = async () => {
    try {
      // Fetch subscription info using paymentsAPI (uses HTTP-only cookies)
      const subResponse = await paymentsAPI.getSubscription();
      setSubscription(subResponse.data);

      // Fetch plan limits using paymentsAPI (uses HTTP-only cookies)
      const limitsResponse = await paymentsAPI.getLimits();
      setLimits(limitsResponse.data);

    } catch (error) {
      console.error('Error fetching billing info:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load billing information'
      });
    } finally {
      setLoading(false);
    }
  };

  // SECURITY FIX Bug #1: Use paymentsAPI with HTTP-only cookies instead of localStorage
  const openBillingPortal = async () => {
    setPortalLoading(true);

    try {
      // Get billing portal URL using paymentsAPI (uses HTTP-only cookies)
      const response = await paymentsAPI.getBillingPortal();

      // Redirect to Stripe billing portal
      window.location.href = response.data.portal_url;

    } catch (error: any) {
      console.error('Billing portal error:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to open billing portal'
      });
      setPortalLoading(false);
    }
  };

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case 'free':
        return 'bg-gray-100 text-gray-800';
      case 'starter':
        return 'bg-blue-100 text-blue-800';
      case 'pro':
        return 'bg-purple-100 text-purple-800';
      case 'enterprise':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'canceled':
        return 'bg-red-100 text-red-800';
      case 'past_due':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="container mx-auto px-4 py-12">
        <Card className="p-8 text-center">
          <AlertCircle className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">No Subscription Found</h2>
          <p className="text-muted-foreground mb-6">
            We couldn't find any subscription information for your account.
          </p>
          <Button onClick={() => navigate('/pricing')}>
            View Pricing Plans
          </Button>
        </Card>
      </div>
    );
  }

  const usagePercentage = limits ? (limits.current_usage / (limits.limit === -1 ? limits.current_usage : limits.limit)) * 100 : 0;

  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Billing & Subscription</h1>
        <p className="text-muted-foreground">
          Manage your subscription and view your usage
        </p>
      </div>

      {/* Current Plan */}
      <Card className="p-6 mb-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold mb-2">Current Plan</h2>
            <div className="flex items-center gap-3">
              <Badge className={getPlanColor(subscription.plan)}>
                {subscription.plan.toUpperCase()}
              </Badge>
              <Badge className={getStatusColor(subscription.status)}>
                {subscription.status.toUpperCase()}
              </Badge>
            </div>
          </div>

          {subscription.plan !== 'free' && subscription.has_stripe_account && (
            <Button
              onClick={openBillingPortal}
              disabled={portalLoading}
              variant="outline"
            >
              {portalLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
                  Loading...
                </>
              ) : (
                <>
                  <CreditCard className="w-4 h-4 mr-2" />
                  Manage Subscription
                  <ExternalLink className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-primary/10">
              <Calendar className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Member Since</p>
              <p className="font-medium">
                {new Date(subscription.member_since).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-primary/10">
              <TrendingUp className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Status</p>
              <p className="font-medium capitalize">{subscription.status}</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Usage */}
      {limits && (
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Usage This Month</h2>

          <div className="mb-4">
            <div className="flex justify-between mb-2">
              <span className="text-sm text-muted-foreground">Listings Created</span>
              <span className="text-sm font-medium">
                {limits.current_usage} / {limits.limit === -1 ? '∞' : limits.limit}
              </span>
            </div>

            {limits.limit !== -1 && (
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    usagePercentage > 90 ? 'bg-red-500' :
                    usagePercentage > 70 ? 'bg-orange-500' :
                    'bg-primary'
                  }`}
                  style={{ width: `${Math.min(usagePercentage, 100)}%` }}
                ></div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-muted">
            <div>
              <p className="font-medium">
                {limits.remaining === -1 ? 'Unlimited' : limits.remaining} listings remaining
              </p>
              <p className="text-sm text-muted-foreground">
                {limits.can_create ? 'You can create more listings' : 'Upgrade to create more'}
              </p>
            </div>

            {!limits.can_create && (
              <Button onClick={() => navigate('/pricing')}>
                Upgrade Plan
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* Actions */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>

        <div className="space-y-3">
          {subscription.plan === 'free' && (
            <Button
              onClick={() => navigate('/pricing')}
              className="w-full justify-between"
            >
              <span>Upgrade to Premium</span>
              <ExternalLink className="w-4 h-4" />
            </Button>
          )}

          {subscription.plan !== 'free' && subscription.has_stripe_account && (
            <>
              <Button
                onClick={openBillingPortal}
                variant="outline"
                className="w-full justify-between"
                disabled={portalLoading}
              >
                <span>Update Payment Method</span>
                <CreditCard className="w-4 h-4" />
              </Button>

              <Button
                onClick={openBillingPortal}
                variant="outline"
                className="w-full justify-between"
                disabled={portalLoading}
              >
                <span>View Invoices</span>
                <ExternalLink className="w-4 h-4" />
              </Button>

              <Button
                onClick={openBillingPortal}
                variant="destructive"
                className="w-full justify-between"
                disabled={portalLoading}
              >
                <span>Cancel Subscription</span>
                <AlertCircle className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </Card>
    </div>
  );
}
