import { useEffect, useMemo, useState } from "react";
import MainWrapper from "@/layouts/wrappers/main-wrapper";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import ApiService, { AdminPlan, AdminPlanCreate, AdminPlanUpdate } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { getDefaultPlanId, isPlanAdmin } from "@/utils/planAdmin";
import { Loader2, Trash2 } from "lucide-react";

const NEW_PLAN_TEMPLATE: AdminPlanCreate = {
    plan_id: "",
    product_name: "",
    display_name: "",
    max_conversions: null,
    max_file_size_mb: 5,
    default_duration_days: 30,
    paypal_link: "",
    doc_id: "Fuzzycloud",
};

export function PlanSettingsPage() {
    const { user } = useAuth();
    const isAuthorized = useMemo(() => isPlanAdmin(user?.email), [user]);
    const defaultPlanId = useMemo(() => getDefaultPlanId(), []);

    const [plans, setPlans] = useState<AdminPlan[]>([]);
    const [newPlan, setNewPlan] = useState<AdminPlanCreate>(NEW_PLAN_TEMPLATE);
    const [loading, setLoading] = useState(true);
    const [savingPlanId, setSavingPlanId] = useState<string | null>(null);
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    useEffect(() => {
        if (!isAuthorized) {
            setLoading(false);
            return;
        }
        const fetchPlans = async () => {
            setLoading(true);
            try {
                const response = await ApiService.getAdminPlans();
                setPlans(response);
            } catch (err: any) {
                setError(err.response?.data?.detail || err.message || "Failed to load plans");
            } finally {
                setLoading(false);
            }
        };
        fetchPlans();
    }, [isAuthorized]);

    const resetNewPlan = () => setNewPlan(NEW_PLAN_TEMPLATE);

    const handlePlanFieldChange = (planId: string, field: keyof AdminPlan, value: string | number | null) => {
        setPlans((prev) =>
            prev.map((plan) =>
                plan.plan_id === planId
                    ? {
                        ...plan,
                        [field]: value,
                    }
                    : plan
            )
        );
    };

    const handlePlanSave = async (plan: AdminPlan) => {
        setSavingPlanId(plan.plan_id);
        setError("");
        setSuccess("");
        const payload: AdminPlanUpdate = {
            product_name: plan.product_name,
            display_name: plan.display_name,
            max_conversions: plan.max_conversions,
            max_file_size_mb: plan.max_file_size_mb,
            default_duration_days: plan.default_duration_days,
            paypal_link: plan.paypal_link || null,
            doc_id: plan.doc_id || null,
        };

        try {
            const updated = await ApiService.updateAdminPlan(plan.plan_id, payload);
            setPlans((prev) => prev.map((item) => (item.plan_id === plan.plan_id ? updated : item)));
            setSuccess(`✅ Plan "${updated.display_name}" updated`);
        } catch (err: any) {
            setError(`Failed to update plan: ${err.response?.data?.detail || err.message}`);
        } finally {
            setSavingPlanId(null);
        }
    };

    const handlePlanDelete = async (planId: string) => {
        if (!confirm("Are you sure you want to delete this plan?")) {
            return;
        }
        setSavingPlanId(planId);
        setError("");
        setSuccess("");
        try {
            await ApiService.deleteAdminPlan(planId);
            setPlans((prev) => prev.filter((plan) => plan.plan_id !== planId));
            setSuccess("✅ Plan removed");
        } catch (err: any) {
            setError(`Failed to delete plan: ${err.response?.data?.detail || err.message}`);
        } finally {
            setSavingPlanId(null);
        }
    };

    const handleCreatePlan = async () => {
        if (!newPlan.plan_id || !newPlan.product_name || !newPlan.display_name) {
            setError("Please fill in plan ID, product name, and display name");
            return;
        }
        setCreating(true);
        setError("");
        setSuccess("");
        try {
            const payload: AdminPlanCreate = {
                ...newPlan,
                max_file_size_mb: Number(newPlan.max_file_size_mb),
                default_duration_days: Number(newPlan.default_duration_days),
                max_conversions:
                    newPlan.max_conversions === null || newPlan.max_conversions === undefined
                        ? null
                        : Number(newPlan.max_conversions),
                paypal_link: newPlan.paypal_link ? newPlan.paypal_link : null,
            };
            const created = await ApiService.createAdminPlan(payload);
            setPlans((prev) => [...prev, created]);
            resetNewPlan();
            setSuccess(`✅ Plan "${created.display_name}" created`);
        } catch (err: any) {
            setError(`Failed to create plan: ${err.response?.data?.detail || err.message}`);
        } finally {
            setCreating(false);
        }
    };

    if (!isAuthorized) {
        return (
            <MainWrapper>
                <Card>
                    <CardHeader>
                        <CardTitle>Plan Settings</CardTitle>
                        <CardDescription>
                            Only authorized administrators can modify subscription plans.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm text-muted-foreground">
                            Please contact support if you believe you should have access to this section.
                        </p>
                    </CardContent>
                </Card>
            </MainWrapper>
        );
    }

    return (
        <MainWrapper>
            <div className="space-y-6">
                <div>
                    <h1 className="text-2xl font-semibold">Plan Settings</h1>
                    <p className="text-muted-foreground">
                        Update subscription plans without redeploying the application.
                    </p>
                </div>

                {(error || success) && (
                    <div className={`rounded border px-3 py-2 text-sm ${error ? "border-red-200 bg-red-50 text-red-700" : "border-green-200 bg-green-50 text-green-700"}`}>
                        {error || success}
                    </div>
                )}

                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                    <div className="space-y-6">
                        {plans.map((plan) => (
                            <Card key={plan.plan_id}>
                                <CardHeader>
                                    <CardTitle>{plan.display_name}</CardTitle>
                                    <CardDescription>
                                        Plan ID: {plan.plan_id}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid gap-4 md:grid-cols-2">
                                        <div>
                                            <Label>Product Name</Label>
                                            <Input
                                                value={plan.product_name}
                                                onChange={(e) =>
                                                    handlePlanFieldChange(plan.plan_id, "product_name", e.target.value)
                                                }
                                            />
                                        </div>
                                        <div>
                                            <Label>Display Name</Label>
                                            <Input
                                                value={plan.display_name}
                                                onChange={(e) =>
                                                    handlePlanFieldChange(plan.plan_id, "display_name", e.target.value)
                                                }
                                            />
                                        </div>
                                    </div>
                                    <div className="grid gap-4 md:grid-cols-3">
                                        <div>
                                            <Label>Max Conversions (leave blank for unlimited)</Label>
                                            <Input
                                                type="number"
                                                value={plan.max_conversions ?? ""}
                                                onChange={(e) =>
                                                    handlePlanFieldChange(
                                                        plan.plan_id,
                                                        "max_conversions",
                                                        e.target.value === "" ? null : Number(e.target.value)
                                                    )
                                                }
                                            />
                                        </div>
                                        <div>
                                            <Label>File Size Limit (MB)</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={plan.max_file_size_mb}
                                                onChange={(e) =>
                                                    handlePlanFieldChange(
                                                        plan.plan_id,
                                                        "max_file_size_mb",
                                                        Number(e.target.value)
                                                    )
                                                }
                                            />
                                        </div>
                                        <div>
                                            <Label>Default Duration (days)</Label>
                                            <Input
                                                type="number"
                                                min={1}
                                                value={plan.default_duration_days}
                                                onChange={(e) =>
                                                    handlePlanFieldChange(
                                                        plan.plan_id,
                                                        "default_duration_days",
                                                        Number(e.target.value)
                                                    )
                                                }
                                            />
                                        </div>
                                    </div>
                                    <div className="grid gap-4 md:grid-cols-2">
                                        <div>
                                            <Label>PayPal Link</Label>
                                            <Textarea
                                                value={plan.paypal_link ?? ""}
                                                onChange={(e) =>
                                                    handlePlanFieldChange(
                                                        plan.plan_id,
                                                        "paypal_link",
                                                        e.target.value || null
                                                    )
                                                }
                                            />
                                        </div>
                                        <div>
                                            <Label>Firestore Doc ID</Label>
                                            <Input
                                                value={plan.doc_id ?? ""}
                                                onChange={(e) =>
                                                    handlePlanFieldChange(plan.plan_id, "doc_id", e.target.value)
                                                }
                                            />
                                        </div>
                                    </div>
                                    <div className="flex flex-wrap gap-3">
                                        <Button
                                            onClick={() => handlePlanSave(plan)}
                                            disabled={savingPlanId === plan.plan_id}
                                        >
                                            {savingPlanId === plan.plan_id ? "Saving..." : "Save Changes"}
                                        </Button>
                                        <Button
                                            variant="destructive"
                                            disabled={plan.plan_id === defaultPlanId || savingPlanId === plan.plan_id}
                                            onClick={() => handlePlanDelete(plan.plan_id)}
                                        >
                                            <Trash2 className="mr-2 h-4 w-4" />
                                            Delete
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                <Card>
                    <CardHeader>
                        <CardTitle>Create New Plan</CardTitle>
                        <CardDescription>
                            Define a new subscription tier.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-4 md:grid-cols-2">
                            <div>
                                <Label>Plan ID</Label>
                                <Input
                                    value={newPlan.plan_id}
                                    onChange={(e) => setNewPlan((prev) => ({ ...prev, plan_id: e.target.value }))}
                                />
                            </div>
                            <div>
                                <Label>Product Name</Label>
                                <Input
                                    value={newPlan.product_name}
                                    onChange={(e) => setNewPlan((prev) => ({ ...prev, product_name: e.target.value }))}
                                />
                            </div>
                        </div>
                        <div>
                            <Label>Display Name</Label>
                            <Input
                                value={newPlan.display_name}
                                onChange={(e) => setNewPlan((prev) => ({ ...prev, display_name: e.target.value }))}
                            />
                        </div>
                        <div className="grid gap-4 md:grid-cols-3">
                            <div>
                                <Label>Max Conversions</Label>
                                <Input
                                    type="number"
                                    value={newPlan.max_conversions ?? ""}
                                    onChange={(e) =>
                                        setNewPlan((prev) => ({
                                            ...prev,
                                            max_conversions: e.target.value === "" ? null : Number(e.target.value),
                                        }))
                                    }
                                />
                                <p className="text-xs text-muted-foreground mt-1">Leave empty for unlimited</p>
                            </div>
                            <div>
                                <Label>File Size Limit (MB)</Label>
                                <Input
                                    type="number"
                                    min={1}
                                    value={newPlan.max_file_size_mb}
                                    onChange={(e) =>
                                        setNewPlan((prev) => ({ ...prev, max_file_size_mb: Number(e.target.value) }))
                                    }
                                />
                            </div>
                            <div>
                                <Label>Default Duration (days)</Label>
                                <Input
                                    type="number"
                                    min={1}
                                    value={newPlan.default_duration_days}
                                    onChange={(e) =>
                                        setNewPlan((prev) => ({
                                            ...prev,
                                            default_duration_days: Number(e.target.value),
                                        }))
                                    }
                                />
                            </div>
                        </div>
                        <div className="grid gap-4 md:grid-cols-2">
                            <div>
                                <Label>PayPal Link</Label>
                                <Textarea
                                    value={newPlan.paypal_link ?? ""}
                                    onChange={(e) =>
                                        setNewPlan((prev) => ({ ...prev, paypal_link: e.target.value || null }))
                                    }
                                />
                            </div>
                            <div>
                                <Label>Firestore Doc ID</Label>
                                <Input
                                    value={newPlan.doc_id ?? ""}
                                    onChange={(e) => setNewPlan((prev) => ({ ...prev, doc_id: e.target.value }))}
                                />
                            </div>
                        </div>
                        <div className="flex gap-3">
                            <Button onClick={handleCreatePlan} disabled={creating}>
                                {creating ? "Creating..." : "Create Plan"}
                            </Button>
                            <Button variant="outline" onClick={resetNewPlan} disabled={creating}>
                                Reset
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </MainWrapper>
    );
}
