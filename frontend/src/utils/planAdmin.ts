const ADMIN_EMAILS = (import.meta.env.VITE_PLAN_ADMIN_EMAILS || "")
    .split(",")
    .map((email) => email.trim().toLowerCase())
    .filter(Boolean);

const DEFAULT_PLAN_ID = import.meta.env.VITE_DEFAULT_PLAN_ID || "free";

export function isPlanAdmin(email?: string | null): boolean {
    if (!email) {
        return false;
    }
    return ADMIN_EMAILS.includes(email.toLowerCase());
}

export function getDefaultPlanId(): string {
    return DEFAULT_PLAN_ID;
}
