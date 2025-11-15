# Navigation Links for New AI Features

Add these links to your sidebar/navigation component:

## Main Navigation Items

```tsx
// In your Sidebar component or Navigation component

import { DollarSign, Calendar, Sparkles, MessageSquare, BarChart3 } from 'lucide-react';

const aiFeatures = [
  {
    name: 'AI Messages',
    icon: MessageSquare,
    href: '/messages',
    badge: 'AI',
    description: 'GPT-4 powered auto-replies'
  },
  {
    name: 'Price Optimizer',
    icon: DollarSign,
    href: '/price-optimizer',
    badge: 'NEW',
    description: 'AI-powered dynamic pricing'
  },
  {
    name: 'Scheduling',
    icon: Calendar,
    href: '/scheduling',
    badge: 'ML',
    description: 'ML-optimized publication times'
  },
  {
    name: 'Analytics ML',
    icon: BarChart3,
    href: '/analytics',
    badge: 'AI',
    description: 'Revenue predictions & insights'
  },
  {
    name: 'Image Editor',
    icon: Sparkles,
    href: '/image-editor',
    badge: 'AI',
    description: 'AI image enhancement'
  }
];

// Render as navigation group
<div className="px-3 py-2">
  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
    AI Features
  </h3>
  {aiFeatures.map(feature => (
    <NavLink key={feature.href} to={feature.href}>
      <feature.icon className="w-5 h-5" />
      <span>{feature.name}</span>
      {feature.badge && <Badge>{feature.badge}</Badge>}
    </NavLink>
  ))}
</div>
```

## Dashboard Quick Links

```tsx
// Add to Dashboard.tsx in quick actions section

const aiQuickActions = [
  {
    to: '/messages',
    title: '🤖 AI Messages',
    subtitle: 'GPT-4 Auto-Replies',
    gradient: 'from-violet-500 to-purple-600',
    badge: 'AI'
  },
  {
    to: '/price-optimizer',
    title: '💰 Price Optimizer',
    subtitle: 'Smart Pricing',
    gradient: 'from-green-500 to-emerald-600',
    badge: 'NEW'
  },
  {
    to: '/scheduling',
    title: '📅 ML Scheduling',
    subtitle: 'Optimal Times',
    gradient: 'from-blue-500 to-cyan-600',
    badge: 'ML'
  }
];
```
