import { useCallback, useEffect, useMemo, useState } from "react";
import MainWrapper from "@/layouts/wrappers/main-wrapper";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import ApiService, { AdminSubscriptionPlan, SubscriptionPlanPayload } from "@/lib/api";

type PlanFormState = {
    plan_id: string;
    display_name: string;
    product_name: string;
    description: string;
    price_usd: string;
    max_conversions: string;
    max_file_size_mb: string;
    default_duration_days: string;
    paypal_link: string;
    doc_id: string;
    is_active: boolean;
};

const emptyFormState: PlanFormState = {
    plan_id: "",
    display_name: "",
    product_name: "",
    description: "",
    price_usd: "0",
    max_conversions: "",
    max_file_size_mb: "10",
    default_duration_days: "30",
    paypal_link: "",
    doc_id: "Fuzzycloud",
    is_active: true,
};

const normalizeNumber = (value: string): number => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
};

const normalizeOptionalInt = (value: string): number | null => {
    if (value === "" || value === null) return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
};

const mapPlanToForm = (plan: AdminSubscriptionPlan): PlanFormState => ({
    plan_id: plan.plan_id,
    display_name: plan.display_name,
    product_name: plan.product_name,
    description: plan.description || "",
    price_usd: String(plan.price_usd ?? 0),
    max_conversions: plan.max_conversions === null ? "" : String(plan.max_conversions),
    max_file_size_mb: String(plan.max_file_size_mb),
    default_duration_days: String(plan.default_duration_days),
    paypal_link: plan.paypal_link || "",
    doc_id: plan.doc_id,
    is_active: plan.is_active,
});

export const AdminSubscriptionPlansPage = () => {
    const [plans, setPlans] = useState<AdminSubscriptionPlan[]>([]);
    const [loading, setLoading] = useState(true);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [formState, setFormState] = useState<PlanFormState>(emptyFormState);
    const [editingPlan, setEditingPlan] = useState<AdminSubscriptionPlan | null>(null);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchPlans = useCallback(async () => {
        setLoading(true);
        try {
            const data = await ApiService.getAdminPlans(true);
            setPlans(data);
        } catch (err) {
            console.error("Failed to fetch plans", err);
            setError("Unable to load plans.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchPlans();
    }, [fetchPlans]);

    const openCreateDialog = () => {
        setEditingPlan(null);
        setFormState(emptyFormState);
        setDialogOpen(true);
        setError(null);
    };

    const openEditDialog = (plan: AdminSubscriptionPlan) => {
        setEditingPlan(plan);
        setFormState(mapPlanToForm(plan));
        setDialogOpen(true);
        setError(null);
    };

    const closeDialog = () => {
        setDialogOpen(false);
        setEditingPlan(null);
        setFormState(emptyFormState);
        setSaving(false);
        setError(null);
    };

    const handleDialogChange = (open: boolean) => {
        if (!open) {
            closeDialog();
        } else {
            setDialogOpen(true);
        }
    };

    const handleChange = (field: keyof PlanFormState, value: string | boolean) => {
        setFormState((prev) => ({
            ...prev,
            [field]: value,
        }));
    };

    const buildPayload = (): SubscriptionPlanPayload | Omit<SubscriptionPlanPayload, "plan_id"> => {
        const base = {
            display_name: formState.display_name,
            product_name: formState.product_name,
            description: formState.description || null,
            price_usd: normalizeNumber(formState.price_usd),
            max_conversions: normalizeOptionalInt(formState.max_conversions),
            max_file_size_mb: normalizeNumber(formState.max_file_size_mb),
            default_duration_days: normalizeNumber(formState.default_duration_days),
            paypal_link: formState.paypal_link || null,
            doc_id: formState.doc_id || "Fuzzycloud",
            is_active: formState.is_active,
        };

        if (editingPlan) {
            return base;
        }
        return {
            plan_id: formState.plan_id,
            ...base,
        };
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setSaving(true);
        setError(null);
        try {
            if (editingPlan) {
                await ApiService.updateAdminPlan(editingPlan.plan_id, buildPayload());
            } else {
                const payload = buildPayload() as SubscriptionPlanPayload;
                if (!payload.plan_id) {
                    setError("Plan ID is required.");
                    setSaving(false);
                    return;
                }
                await ApiService.createAdminPlan(payload);
            }
            await fetchPlans();
            closeDialog();
        } catch (err: any) {
            console.error("Failed to save plan", err);
            setError(err?.response?.data?.detail || "Failed to save plan.");
        } finally {
            setSaving(false);
        }
    };

    const activePlans = useMemo(() => plans.filter((plan) => plan.is_active), [plans]);

    return (
        <MainWrapper>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Manage Subscription Plans</h1>
                        <p className="text-muted-foreground">
                            Edit limits, pricing, and purchase links without redeploying.
                        </p>
                    </div>
                    <Dialog open={dialogOpen} onOpenChange={handleDialogChange}>
                        <DialogTrigger asChild>
                            <Button onClick={openCreateDialog}>New Plan</Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl">
                            <DialogHeader>
                                <DialogTitle>{editingPlan ? `Edit ${editingPlan.display_name}` : "Create Plan"}</DialogTitle>
                            </DialogHeader>
                            <form onSubmit={handleSubmit} className="space-y-4">
                                {!editingPlan && (
                                    <div>
                                        <Label htmlFor="plan_id">Plan ID</Label>
                                        <Input
                                            id="plan_id"
                                            value={formState.plan_id}
                                            onChange={(e) => handleChange("plan_id", e.target.value)}
                                            placeholder="basic"
                                            required
                                        />
                                    </div>
                                )}
                                <div className="grid gap-4 md:grid-cols-2">
                                    <div>
                                        <Label htmlFor="display_name">Display Name</Label>
                                        <Input
                                            id="display_name"
                                            value={formState.display_name}
                                            onChange={(e) => handleChange("display_name", e.target.value)}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="product_name">Product Name</Label>
                                        <Input
                                            id="product_name"
                                            value={formState.product_name}
                                            onChange={(e) => handleChange("product_name", e.target.value)}
                                            required
                                            disabled={!!editingPlan}
                                        />
                                    </div>
                                </div>
                                <div>
                                    <Label htmlFor="description">Description</Label>
                                    <Textarea
                                        id="description"
                                        value={formState.description}
                                        onChange={(e) => handleChange("description", e.target.value)}
                                        placeholder="Optional short description"
                                    />
                                </div>
                                <div className="grid gap-4 md:grid-cols-2">
                                    <div>
                                        <Label htmlFor="price_usd">Price (USD)</Label>
                                        <Input
                                            type="number"
                                            step="0.01"
                                            id="price_usd"
                                            value={formState.price_usd}
                                            onChange={(e) => handleChange("price_usd", e.target.value)}
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="max_conversions">Monthly Conversions (leave blank for unlimited)</Label>
                                        <Input
                                            type="number"
                                            id="max_conversions"
                                            value={formState.max_conversions}
                                            onChange={(e) => handleChange("max_conversions", e.target.value)}
                                        />
                                    </div>
                                </div>
                                <div className="grid gap-4 md:grid-cols-2">
                                    <div>
                                        <Label htmlFor="max_file_size_mb">File Size Limit (MB)</Label>
                                        <Input
                                            type="number"
                                            id="max_file_size_mb"
                                            value={formState.max_file_size_mb}
                                            onChange={(e) => handleChange("max_file_size_mb", e.target.value)}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="default_duration_days">Default Duration (days)</Label>
                                        <Input
                                            type="number"
                                            id="default_duration_days"
                                            value={formState.default_duration_days}
                                            onChange={(e) => handleChange("default_duration_days", e.target.value)}
                                            required
                                        />
                                    </div>
                                </div>
                                <div className="grid gap-4 md:grid-cols-2">
                                    <div>
                                        <Label htmlFor="paypal_link">PayPal Link</Label>
                                        <Input
                                            id="paypal_link"
                                            value={formState.paypal_link}
                                            onChange={(e) => handleChange("paypal_link", e.target.value)}
                                            placeholder="https://..."
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="doc_id">Firestore Doc ID</Label>
                                        <Input
                                            id="doc_id"
                                            value={formState.doc_id}
                                            onChange={(e) => handleChange("doc_id", e.target.value)}
                                            required
                                        />
                                    </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <Checkbox
                                        id="is_active"
                                        checked={formState.is_active}
                                        onCheckedChange={(checked) => handleChange("is_active", Boolean(checked))}
                                    />
                                    <Label htmlFor="is_active">Plan is active</Label>
                                </div>
                                {error && <p className="text-sm text-destructive">{error}</p>}
                                <DialogFooter>
                                    <Button type="button" variant="outline" onClick={closeDialog}>
                                        Cancel
                                    </Button>
                                    <Button type="submit" disabled={saving}>
                                        {saving ? "Saving..." : "Save"}
                                    </Button>
                                </DialogFooter>
                            </form>
                        </DialogContent>
                    </Dialog>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Active Plans</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <p>Loading plans...</p>
                        ) : activePlans.length === 0 ? (
                            <p className="text-muted-foreground">No plans configured.</p>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="text-left">
                                            <th className="p-2">Plan</th>
                                            <th className="p-2">Price</th>
                                            <th className="p-2">Conversions</th>
                                            <th className="p-2">File Size</th>
                                            <th className="p-2">Duration</th>
                                            <th className="p-2">PayPal</th>
                                            <th className="p-2 text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {activePlans.map((plan) => (
                                            <tr key={plan.plan_id} className="border-t">
                                                <td className="p-2">
                                                    <div className="font-medium">{plan.display_name}</div>
                                                    <p className="text-xs text-muted-foreground">{plan.plan_id}</p>
                                                </td>
                                                <td className="p-2">${plan.price_usd?.toFixed(2)}</td>
                                                <td className="p-2">
                                                    {plan.max_conversions === null ? "Unlimited" : plan.max_conversions}
                                                </td>
                                                <td className="p-2">{plan.max_file_size_mb} MB</td>
                                                <td className="p-2">{plan.default_duration_days} days</td>
                                                <td className="p-2">
                                                    {plan.paypal_link ? (
                                                        <a
                                                            href={plan.paypal_link}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                            className="text-primary underline"
                                                        >
                                                            Link
                                                        </a>
                                                    ) : (
                                                        "-"
                                                    )}
                                                </td>
                                                <td className="p-2 text-right">
                                                    <Button variant="outline" size="sm" onClick={() => openEditDialog(plan)}>
                                                        Edit
                                                    </Button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </MainWrapper>
    );
};

export default AdminSubscriptionPlansPage;
