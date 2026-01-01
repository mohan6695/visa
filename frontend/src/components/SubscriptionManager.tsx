'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@/hooks/useUser';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, CheckCircle, XCircle, CreditCard, Calendar, AlertTriangle } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import apiClient from '@/lib/api';

interface Plan {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  interval: string;
  tier: string;
}

interface SubscriptionStatus {
  is_premium: boolean;
  tier: string;
  status: string;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end?: boolean;
}

export const SubscriptionManager: React.FC = () => {
  const { user } = useUser();
  const router = useRouter();
  
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscriptionStatus, setSubscriptionStatus] = useState<SubscriptionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedCurrency, setSelectedCurrency] = useState<string>('usd');
  
  // Load subscription plans and status
  useEffect(() => {
    if (user) {
      loadSubscriptionData();
    }
  }, [user, selectedCurrency]);
  
  const loadSubscriptionData = async () => {
    try {
      setIsLoading(true);
      
      // Load subscription plans
      const plansResponse = await apiClient.getSubscriptionPlans(selectedCurrency);
      if (plansResponse.success) {
        setPlans(plansResponse.plans);
      }
      
      // Load subscription status
      const statusResponse = await apiClient.getSubscriptionStatus();
      if (statusResponse.success) {
        setSubscriptionStatus(statusResponse);
      }
      
    } catch (error) {
      console.error('Failed to load subscription data:', error);
      toast({
        title: "Error",
        description: "Failed to load subscription information.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSubscribe = async (priceId: string) => {
    if (!user) {
      toast({
        title: "Please sign in",
        description: "You need to be signed in to subscribe.",
      });
      router.push('/login');
      return;
    }
    
    try {
      setIsProcessing(true);
      
      const response = await apiClient.createCheckoutSession({
        price_id: priceId,
        success_url: `${window.location.origin}/account?subscription=success`,
        cancel_url: `${window.location.origin}/account?subscription=canceled`,
        currency: selectedCurrency
      });
      
      if (response.success && response.url) {
        // Redirect to Stripe checkout
        window.location.href = response.url;
      } else {
        throw new Error(response.error || 'Failed to create checkout session');
      }
      
    } catch (error) {
      console.error('Failed to create checkout session:', error);
      toast({
        title: "Error",
        description: "Failed to start subscription process. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const handleCancelSubscription = async () => {
    if (!user) return;
    
    if (!confirm('Are you sure you want to cancel your subscription? You will lose premium benefits at the end of your current billing period.')) {
      return;
    }
    
    try {
      setIsProcessing(true);
      
      const response = await apiClient.cancelSubscription();
      
      if (response.success) {
        toast({
          title: "Subscription cancelled",
          description: "Your subscription has been cancelled. You will have access until the end of your current billing period.",
        });
        
        // Reload subscription status
        loadSubscriptionData();
      } else {
        throw new Error(response.error || 'Failed to cancel subscription');
      }
      
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      toast({
        title: "Error",
        description: "Failed to cancel subscription. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString();
  };
  
  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2">Loading subscription information...</span>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Current Subscription Status */}
      {subscriptionStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CreditCard className="mr-2 h-5 w-5" />
              Subscription Status
              {subscriptionStatus.is_premium && (
                <Badge className="ml-2" variant="default">
                  {subscriptionStatus.tier === 'group_leader' ? 'Group Leader' : 'Premium'}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {subscriptionStatus.is_premium ? (
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                  <span>Active subscription</span>
                </div>
                {subscriptionStatus.current_period_end && (
                  <div className="flex items-center text-sm">
                    <Calendar className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>Current period ends: {formatDate(subscriptionStatus.current_period_end)}</span>
                  </div>
                )}
                {subscriptionStatus.cancel_at_period_end && (
                  <div className="flex items-center text-sm">
                    <AlertTriangle className="mr-2 h-4 w-4 text-yellow-500" />
                    <span>Your subscription will end on {formatDate(subscriptionStatus.current_period_end)}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center text-sm">
                <XCircle className="mr-2 h-4 w-4 text-destructive" />
                <span>No active subscription</span>
              </div>
            )}
          </CardContent>
          {subscriptionStatus.is_premium && !subscriptionStatus.cancel_at_period_end && (
            <CardFooter>
              <Button 
                variant="outline" 
                onClick={handleCancelSubscription}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Cancel Subscription'
                )}
              </Button>
            </CardFooter>
          )}
        </Card>
      )}
      
      {/* Subscription Plans */}
      <Card>
        <CardHeader>
          <CardTitle>Subscription Plans</CardTitle>
          <CardDescription>Choose a plan that works for you</CardDescription>
          <div className="flex items-center space-x-2 mt-2">
            <span className="text-sm">Currency:</span>
            <select
              value={selectedCurrency}
              onChange={(e) => setSelectedCurrency(e.target.value)}
              className="text-sm border rounded px-2 py-1"
            >
              <option value="usd">USD</option>
              <option value="inr">INR</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="monthly">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="monthly">Monthly</TabsTrigger>
              <TabsTrigger value="yearly">Yearly (Save 16%)</TabsTrigger>
            </TabsList>
            
            {/* Monthly Plans */}
            <TabsContent value="monthly" className="space-y-4 mt-4">
              {plans
                .filter(plan => plan.interval === 'month')
                .map(plan => (
                  <Card key={plan.id}>
                    <CardHeader>
                      <CardTitle>{plan.name}</CardTitle>
                      <div className="flex items-center justify-between">
                        <span className="text-2xl font-bold">
                          {formatCurrency(plan.price, plan.currency)}
                          <span className="text-sm font-normal text-muted-foreground">/month</span>
                        </span>
                        <Badge variant={plan.tier === 'group_leader' ? 'default' : 'outline'}>
                          {plan.tier === 'group_leader' ? 'Group Leader' : 'Premium'}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-4">{plan.description}</p>
                      <ul className="space-y-2 text-sm">
                        <li className="flex items-center">
                          <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                          Unlimited posts
                        </li>
                        <li className="flex items-center">
                          <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                          Cross-group search
                        </li>
                        <li className="flex items-center">
                          <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                          Ad-free experience
                        </li>
                        {plan.tier === 'group_leader' && (
                          <>
                            <li className="flex items-center">
                              <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                              Advanced analytics
                            </li>
                            <li className="flex items-center">
                              <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                              Featured placement
                            </li>
                          </>
                        )}
                      </ul>
                    </CardContent>
                    <CardFooter>
                      <Button 
                        className="w-full" 
                        onClick={() => handleSubscribe(plan.id)}
                        disabled={isProcessing || (subscriptionStatus?.tier === plan.tier && subscriptionStatus?.is_premium)}
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Processing...
                          </>
                        ) : subscriptionStatus?.tier === plan.tier && subscriptionStatus?.is_premium ? (
                          'Current Plan'
                        ) : (
                          'Subscribe'
                        )}
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
            </TabsContent>
            
            {/* Yearly Plans */}
            <TabsContent value="yearly" className="space-y-4 mt-4">
              {plans
                .filter(plan => plan.interval === 'year')
                .map(plan => (
                  <Card key={plan.id}>
                    <CardHeader>
                      <CardTitle>{plan.name}</CardTitle>
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-2xl font-bold">
                            {formatCurrency(plan.price, plan.currency)}
                            <span className="text-sm font-normal text-muted-foreground">/year</span>
                          </span>
                          <div className="text-sm text-muted-foreground">
                            {formatCurrency(plan.price / 12, plan.currency)}/month
                          </div>
                        </div>
                        <Badge variant={plan.tier === 'group_leader' ? 'default' : 'outline'}>
                          {plan.tier === 'group_leader' ? 'Group Leader' : 'Premium'}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-4">{plan.description}</p>
                      <ul className="space-y-2 text-sm">
                        <li className="flex items-center">
                          <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                          Unlimited posts
                        </li>
                        <li className="flex items-center">
                          <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                          Cross-group search
                        </li>
                        <li className="flex items-center">
                          <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                          Ad-free experience
                        </li>
                        {plan.tier === 'group_leader' && (
                          <>
                            <li className="flex items-center">
                              <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                              Advanced analytics
                            </li>
                            <li className="flex items-center">
                              <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                              Featured placement
                            </li>
                          </>
                        )}
                      </ul>
                    </CardContent>
                    <CardFooter>
                      <Button 
                        className="w-full" 
                        onClick={() => handleSubscribe(plan.id)}
                        disabled={isProcessing || (subscriptionStatus?.tier === plan.tier && subscriptionStatus?.is_premium)}
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Processing...
                          </>
                        ) : subscriptionStatus?.tier === plan.tier && subscriptionStatus?.is_premium ? (
                          'Current Plan'
                        ) : (
                          'Subscribe'
                        )}
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      
      {/* Free vs Premium Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Free vs Premium</CardTitle>
          <CardDescription>Compare features between free and premium plans</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-4">Feature</th>
                  <th className="text-center py-2 px-4">Free</th>
                  <th className="text-center py-2 px-4">Premium</th>
                  <th className="text-center py-2 px-4">Group Leader</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-2 px-4">Daily Posts</td>
                  <td className="text-center py-2 px-4">10</td>
                  <td className="text-center py-2 px-4">Unlimited</td>
                  <td className="text-center py-2 px-4">Unlimited</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-4">Search Scope</td>
                  <td className="text-center py-2 px-4">Own Group</td>
                  <td className="text-center py-2 px-4">All Groups</td>
                  <td className="text-center py-2 px-4">All Groups</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-4">Ads</td>
                  <td className="text-center py-2 px-4">Yes</td>
                  <td className="text-center py-2 px-4">No</td>
                  <td className="text-center py-2 px-4">No</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-4">Advanced Analytics</td>
                  <td className="text-center py-2 px-4">No</td>
                  <td className="text-center py-2 px-4">No</td>
                  <td className="text-center py-2 px-4">Yes</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-4">Featured Placement</td>
                  <td className="text-center py-2 px-4">No</td>
                  <td className="text-center py-2 px-4">No</td>
                  <td className="text-center py-2 px-4">Yes</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};