import { useState, useEffect } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Input } from '../components/common/Input';
import { Textarea } from '../components/common/Textarea';
import {
  Plus, Trash2, Power, PlayCircle, CheckCircle, XCircle,
  ExternalLink, Zap, TrendingUp, Globe
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';

interface Webhook {
  id: number;
  url: string;
  events: string[];
  description: string;
  secret: string;
  is_active: boolean;
  created_at: string;
  last_triggered_at: string | null;
  delivery_count: number;
  failure_count: number;
}

interface WebhookEvent {
  name: string;
  description: string;
}

export default function Webhooks() {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [events, setEvents] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const { toast } = useToast();

  // Form state
  const [formData, setFormData] = useState({
    url: '',
    events: [] as string[],
    description: ''
  });

  useEffect(() => {
    fetchWebhooks();
    fetchEvents();
  }, []);

  const fetchWebhooks = async () => {
    try {
      const token = localStorage.getItem('token');
      const API_URL = import.meta.env.VITE_API_URL || '';

      const response = await fetch(`${API_URL}/api/v1/webhooks/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch webhooks');

      const data = await response.json();
      setWebhooks(data);
    } catch (error) {
      console.error('Error fetching webhooks:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load webhooks'
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchEvents = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${API_URL}/api/v1/webhooks/events`);

      if (!response.ok) throw new Error('Failed to fetch events');

      const data = await response.json();
      setEvents(data.description || {});
    } catch (error) {
      console.error('Error fetching events:', error);
    }
  };

  const createWebhook = async () => {
    try {
      const token = localStorage.getItem('token');
      const API_URL = import.meta.env.VITE_API_URL || '';

      const response = await fetch(`${API_URL}/api/v1/webhooks/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create webhook');
      }

      await fetchWebhooks();
      setShowCreateForm(false);
      setFormData({ url: '', events: [], description: '' });

      toast({
        title: 'Success',
        description: 'Webhook created successfully'
      });
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message
      });
    }
  };

  const deleteWebhook = async (id: number) => {
    if (!confirm('Are you sure you want to delete this webhook?')) return;

    try {
      const token = localStorage.getItem('token');
      const API_URL = import.meta.env.VITE_API_URL || '';

      const response = await fetch(`${API_URL}/api/v1/webhooks/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to delete webhook');

      await fetchWebhooks();

      toast({
        title: 'Success',
        description: 'Webhook deleted'
      });
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message
      });
    }
  };

  const toggleWebhook = async (id: number) => {
    try {
      const token = localStorage.getItem('token');
      const API_URL = import.meta.env.VITE_API_URL || '';

      const response = await fetch(`${API_URL}/api/v1/webhooks/${id}/toggle`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to toggle webhook');

      await fetchWebhooks();

      toast({
        title: 'Success',
        description: 'Webhook status updated'
      });
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message
      });
    }
  };

  const testWebhook = async (url: string) => {
    try {
      const token = localStorage.getItem('token');
      const API_URL = import.meta.env.VITE_API_URL || '';

      const response = await fetch(`${API_URL}/api/v1/webhooks/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ url })
      });

      if (!response.ok) throw new Error('Test failed');

      const data = await response.json();

      toast({
        title: data.success ? 'Success' : 'Failed',
        description: data.success
          ? `Webhook responded in ${data.response_time_seconds.toFixed(2)}s`
          : 'Webhook test failed',
        variant: data.success ? 'default' : 'destructive'
      });
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message
      });
    }
  };

  const getSuccessRate = (webhook: Webhook) => {
    const total = webhook.delivery_count + webhook.failure_count;
    if (total === 0) return 100;
    return (webhook.delivery_count / total) * 100;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Webhooks</h1>
          <p className="text-muted-foreground">
            Connect VintedBot with Zapier, Make, and 1000+ apps
          </p>
        </div>

        <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Create Webhook
        </Button>
      </div>

      {/* Popular Integrations */}
      <Card className="p-6 mb-6 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-purple-600" />
          <h2 className="font-semibold">Popular Integrations</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4" />
            <span className="text-sm">Zapier</span>
          </div>
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4" />
            <span className="text-sm">Make</span>
          </div>
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4" />
            <span className="text-sm">n8n</span>
          </div>
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4" />
            <span className="text-sm">Custom</span>
          </div>
        </div>
      </Card>

      {/* Create Form */}
      {showCreateForm && (
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Create New Webhook</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Webhook URL</label>
              <Input
                type="url"
                placeholder="https://your-app.com/webhook"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Must be HTTPS. Private IPs and localhost are blocked for security.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Events</label>
              <div className="space-y-2">
                {Object.entries(events).map(([event, description]) => (
                  <label key={event} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.events.includes(event)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData({ ...formData, events: [...formData.events, event] });
                        } else {
                          setFormData({ ...formData, events: formData.events.filter(e => e !== event) });
                        }
                      }}
                    />
                    <div>
                      <div className="text-sm font-medium">{event}</div>
                      <div className="text-xs text-muted-foreground">{description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Description (optional)</label>
              <Textarea
                placeholder="E.g., Send notifications to Slack"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div className="flex gap-2">
              <Button onClick={createWebhook} disabled={!formData.url || formData.events.length === 0}>
                Create Webhook
              </Button>
              <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Webhooks List */}
      {webhooks.length === 0 ? (
        <Card className="p-12 text-center">
          <Zap className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">No Webhooks Yet</h3>
          <p className="text-muted-foreground mb-6">
            Create your first webhook to connect VintedBot with external services
          </p>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Your First Webhook
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {webhooks.map((webhook) => (
            <Card key={webhook.id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold">{webhook.url}</h3>
                    <Badge variant={webhook.is_active ? 'default' : 'secondary'}>
                      {webhook.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  {webhook.description && (
                    <p className="text-sm text-muted-foreground mb-2">{webhook.description}</p>
                  )}
                  <div className="flex flex-wrap gap-2">
                    {webhook.events.map((event) => (
                      <Badge key={event} variant="outline">{event}</Badge>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toggleWebhook(webhook.id)}
                  >
                    <Power className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => testWebhook(webhook.url)}
                  >
                    <PlayCircle className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => deleteWebhook(webhook.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                <div>
                  <div className="text-sm text-muted-foreground">Deliveries</div>
                  <div className="text-2xl font-bold flex items-center gap-2">
                    {webhook.delivery_count}
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Failures</div>
                  <div className="text-2xl font-bold flex items-center gap-2">
                    {webhook.failure_count}
                    <XCircle className="w-4 h-4 text-red-500" />
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Success Rate</div>
                  <div className="text-2xl font-bold flex items-center gap-2">
                    {getSuccessRate(webhook).toFixed(0)}%
                    <TrendingUp className={`w-4 h-4 ${getSuccessRate(webhook) > 90 ? 'text-green-500' : 'text-orange-500'}`} />
                  </div>
                </div>
              </div>

              {/* Secret */}
              <div className="mt-4 p-3 bg-muted rounded">
                <div className="text-xs text-muted-foreground mb-1">Webhook Secret (for HMAC verification)</div>
                <code className="text-xs font-mono">{webhook.secret}</code>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Documentation */}
      <Card className="p-6 mt-6">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <ExternalLink className="w-4 h-4" />
          How to Use Webhooks
        </h3>
        <div className="space-y-2 text-sm text-muted-foreground">
          <p>1. Create a webhook with your endpoint URL</p>
          <p>2. Select which events you want to receive</p>
          <p>3. VintedBot will send POST requests to your URL when events occur</p>
          <p>4. Verify webhook signatures using the secret key (HMAC-SHA256)</p>
          <p>5. Return HTTP 200 to acknowledge receipt</p>
        </div>
      </Card>
    </div>
  );
}
