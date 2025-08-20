import MainWrapper from "@/layouts/wrappers/main-wrapper";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ArrowRight, Plus, Search } from "lucide-react";
//  import { Link } from "react-router-dom";
import { PhoneInput } from "@/components/ui/phone-input";

export function Vendors() {
  return (
    <MainWrapper>
      <div className="flex flex-col items-left">
        <h1 className="text-lg font-semibold md:text-2xl">Vendors</h1>
        <p className="text-slate-500">Manage your vendors</p>
      </div>
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed shadow-sm w-full mt-4">
        <div className="flex p-4 flex-row w-full">
          <form className="w-1/2">
            <div className="relative w-full">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search ..."
                className="w-full appearance-none bg-background pl-8 shadow-none"
              />
            </div>
          </form>
          <Dialog>
            <DialogTrigger asChild>
              <Button size="icon" className="rounded-sm w-auto px-2 ml-4">
                <Plus size={18} className="mr-2" /> Create a Vendor
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Create a Vendor</DialogTitle>
                <DialogDescription>
                  Fill in the form below to create a new vendor.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-6">
                <div className="grid gap-3">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    type="text"
                    className="w-full"
                    placeholder="Name of the vendor"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="phone">Phone</Label>
                  <PhoneInput id="phone" placeholder="phone" required />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="m@example.com"
                    required
                  />
                </div>
                <div className="grid gap-3">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    className="min-h-24"
                    placeholder="Description of the vendor"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">Save</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
        <div className="grid grid-cols-2 flex-wrap items-start p-4 gap-2 w-full">
          <Card className="col-span-1">
            <CardHeader className="flex items-start">
              <CardTitle>Vendor 3</CardTitle>
              <CardDescription>
                Deploy your new project in one-click.
              </CardDescription>
            </CardHeader>
            <CardFooter className="flex justify-end">
              <Button className="flex items-center justify-center">
                Manage <ArrowRight size={15} className="ml-2" />
              </Button>
            </CardFooter>
          </Card>
          <Card className="col-span-1">
            <CardHeader className="flex items-start">
              <CardTitle>Vendor 3</CardTitle>
              <CardDescription>
                Deploy your new project in one-click.
              </CardDescription>
            </CardHeader>
            <CardFooter className="flex justify-end">
              <Button className="flex items-center justify-center">
                Manage <ArrowRight size={15} className="ml-2" />
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </MainWrapper>
  );
}
