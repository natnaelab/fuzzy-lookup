import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import MainWrapper from "@/layouts/wrappers/main-wrapper";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ApiService from "@/lib/api";
import { CheckCircle2, XCircle } from "lucide-react";

interface Plan {
    plan_id: string;
    product_name: string;
    display_name: string;
    max_conversions: number | null;
    max_file_size_mb: number;
    default_duration_days: number;
    paypal_link: string | null;
}

export function SubscriptionPage() {
    const { license } = useAuth();
    const [plans, setPlans] = useState<Plan[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPlans = async () => {
            try {
                const response = await ApiService.getLicenseTypes();
                setPlans(response.plans || []);
            } catch (error) {
                console.error("Failed to fetch plans:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchPlans();
    }, []);

    const getPlanFeatures = (plan: Plan) => {
        return [
            {
                feature: "Conversions",
                value: plan.max_conversions === null ? "Unlimited" : `${plan.max_conversions} per month`,
                included: true
            },
            {
                feature: "File Size Limit",
                value: `${plan.max_file_size_mb} MB`,
                included: true
            },
            {
                feature: "API Access",
                value: "Full API access",
                included: true
            },
            {
                feature: "Duration",
                value: `${plan.default_duration_days} days`,
                included: true
            }
        ];
    };

    const isCurrentPlan = (planId: string) => {
        return license?.plan_id === planId;
    };

    const getPlanPrice = (planId: string) => {
        if (planId === "free") return "Free";
        if (planId === "basic") return "$9.99/month";
        if (planId === "standard") return "$29.99/month";
        return "Contact us";
    };

    if (loading) {
        return (
            <MainWrapper>
                <div className="flex items-center justify-center min-h-[400px]">
                    <p>Loading plans...</p>
                </div>
            </MainWrapper>
        );
    }

    return (
        <MainWrapper>
            <div className="space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold">Subscription Plans</h1>
                    <p className="text-muted-foreground mt-2">
                        Choose the plan that best fits your needs
                    </p>
                </div>

                {/* Current Plan */}
                {license && (
                    <Card className="border-primary">
                        <CardHeader>
                            <CardTitle className="flex items-center justify-between">
                                <span>Current Plan</span>
                                <Badge variant="default">{license.display_name}</Badge>
                            </CardTitle>
                            <CardDescription>
                                Your active subscription details
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            <div className="flex justify-between">
                                <span className="text-sm font-medium">Conversions Remaining:</span>
                                <span className="text-sm">
                                    {license.conversions_remaining === null 
                                        ? "Unlimited" 
                                        : license.conversions_remaining}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-sm font-medium">File Size Limit:</span>
                                <span className="text-sm">{license.max_file_size_mb} MB</span>
                            </div>
                            {license.expiry && (
                                <div className="flex justify-between">
                                    <span className="text-sm font-medium">Expires:</span>
                                    <span className="text-sm">
                                        {new Date(license.expiry).toLocaleDateString()}
                                    </span>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Available Plans */}
                <div>
                    <h2 className="text-2xl font-semibold mb-4">Available Plans</h2>
                    <div className="grid gap-6 md:grid-cols-3">
                        {plans.map((plan) => (
                            <Card 
                                key={plan.plan_id} 
                                className={isCurrentPlan(plan.plan_id) ? "border-primary" : ""}
                            >
                                <CardHeader>
                                    <div className="flex items-center justify-between">
                                        <CardTitle>{plan.display_name}</CardTitle>
                                        {isCurrentPlan(plan.plan_id) && (
                                            <Badge variant="outline">Current</Badge>
                                        )}
                                    </div>
                                    <CardDescription className="text-2xl font-bold">
                                        {getPlanPrice(plan.plan_id)}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="space-y-2">
                                        {getPlanFeatures(plan).map((item, idx) => (
                                            <div key={idx} className="flex items-start gap-2">
                                                {item.included ? (
                                                    <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                                                ) : (
                                                    <XCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                                                )}
                                                <div className="flex-1">
                                                    <p className="text-sm font-medium">{item.feature}</p>
                                                    <p className="text-xs text-muted-foreground">{item.value}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    {plan.paypal_link && !isCurrentPlan(plan.plan_id) && (
                                        <Button 
                                            asChild 
                                            className="w-full"
                                            variant={plan.plan_id === "standard" ? "default" : "outline"}
                                        >
                                            <a 
                                                href={plan.paypal_link} 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                            >
                                                Upgrade to {plan.display_name}
                                            </a>
                                        </Button>
                                    )}

                                    {isCurrentPlan(plan.plan_id) && (
                                        <Button className="w-full" disabled>
                                            Current Plan
                                        </Button>
                                    )}

                                    {!plan.paypal_link && plan.plan_id === "free" && !isCurrentPlan(plan.plan_id) && (
                                        <Button className="w-full" variant="outline" disabled>
                                            Default Plan
                                        </Button>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            </div>
        </MainWrapper>
    );
}
