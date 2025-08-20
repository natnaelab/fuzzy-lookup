import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import MainWrapper from "@/layouts/wrappers/main-wrapper";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PanelsTopLeft, Settings } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";

export default function ManageVendor() {
  return (
    <MainWrapper>
      <div className="flex flex-col items-start">
        <h1 className="text-base font-semibold md:text-2xl">Vendor 1</h1>
        <p className="text-sm text-slate-500">Manage Vendor</p>
      </div>
      <div className="flex flex-col gap-12">
        <Tabs defaultValue="tab1">
          <TabsList variant="line">
            <TabsTrigger value="tab1" className="inline-flex gap-2">
              <PanelsTopLeft className="-ml-1 size-4" aria-hidden="true" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="tab2" className="inline-flex gap-2">
              <Settings className="-ml-1 size-4" aria-hidden="true" />
              Settings
            </TabsTrigger>
          </TabsList>
          <div className="mt-4">
            <TabsContent value="tab1">
              <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed shadow-sm min-h-[50vh]">
                <div className="flex flex-row flex-wrap items-center gap-1 text-center">
                  Tab 1 content
                </div>
              </div>
            </TabsContent>
            <TabsContent value="tab2">
              <div className="flex flex-col flex-1 items-center justify-start py-2 px-0">
                <div className="flex flex-col items-start gap-1 text-center space-y-4 w-full">
                  <Card className="w-full">
                    <CardHeader className="flex items-start">
                      <CardTitle className="text-lg">Vendor Details</CardTitle>
                      <CardDescription>
                        Used to identify the vendor in the platform.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <form className="flex flex-col space-y-6">
                        <div className="flex flex-col items-start space-y-2">
                          <Label htmlFor="vendor-name" className="text-base">
                            Name
                          </Label>
                          <Input placeholder="Vendor Name" />
                        </div>
                        <div className="flex flex-col items-start space-y-2">
                          <Label htmlFor="vendor-name" className="text-base">
                            Description
                          </Label>
                          <Textarea
                            id="description"
                            className="min-h-24"
                            placeholder="Description of the Vendor"
                          />
                        </div>
                      </form>
                    </CardContent>
                    <CardFooter className="border-t px-6 py-4">
                      <Button>Save</Button>
                    </CardFooter>
                  </Card>
                  <Card className="w-full border border-red-500">
                    <CardHeader className="flex items-start">
                      <CardTitle className="text-red-500">
                        Deactivate Vendor
                      </CardTitle>
                      {/* <CardDescription>
                        Deactivate the vendor from the platform.
                      </CardDescription> */}
                    </CardHeader>
                    <CardContent>
                      <form className="flex flex-col gap-4">
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            id="include"
                            defaultChecked={false}
                            color="red"
                          />
                          <label
                            htmlFor="include"
                            className="text-sm font-medium leading-none text-red-500 peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                          >
                            Are you sure you want to deactivate this vendor?
                          </label>
                        </div>
                      </form>
                    </CardContent>
                    <CardFooter className="border-t px-6 py-4">
                      <Button variant="destructive">Deactivate</Button>
                    </CardFooter>
                  </Card>
                </div>
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </MainWrapper>
  );
}
