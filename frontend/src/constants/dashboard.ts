import { Props } from "@/components/icons/types";
import { Home, GitMerge, CreditCard } from "lucide-react";

export const SIDEBAR_MENU_ITEMS: {
  key: string;
  label: string;
  href: string;
  Icon: React.FC<Props>;
}[] = [
    {
      key: "dashboard",
      label: "Dashboard",
      href: "/dashboard",
      Icon: Home,
    },
    {
      key: "fuzzy",
      label: "Fuzzy Matching",
      href: "/fuzzy",
      Icon: GitMerge,
    },
    {
      key: "subscription",
      label: "Subscription",
      href: "/subscription",
      Icon: CreditCard,
    },
  ];
