import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import MainWrapper from "@/layouts/wrappers/main-wrapper";
import { SingleFileFuzzyMatching } from "./single-file";
import { MultiFileFuzzyMatching } from "./multi-file";

export function FuzzyMatching() {
    const [activeTab, setActiveTab] = useState("single");

    return (
        <MainWrapper>
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Fuzzy Matching</h1>
                    <p className="text-muted-foreground">
                        Find duplicates in a single file or match records between two files
                    </p>
                </div>

                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsList className="grid w-full max-w-md grid-cols-2">
                        <TabsTrigger value="single">Single File</TabsTrigger>
                        <TabsTrigger value="multi">Multi File</TabsTrigger>
                    </TabsList>

                    <TabsContent value="single" className="mt-6">
                        <SingleFileFuzzyMatching />
                    </TabsContent>

                    <TabsContent value="multi" className="mt-6">
                        <MultiFileFuzzyMatching />
                    </TabsContent>
                </Tabs>
            </div>
        </MainWrapper>
    );
}
