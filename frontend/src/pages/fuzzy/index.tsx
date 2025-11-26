import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import MainWrapper from "@/layouts/wrappers/main-wrapper";
import { SingleFileFuzzyMatching } from "./single-file";
import { MultiFileFuzzyMatching } from "./multi-file";
import { APIConfigurationPage } from "./api-config";

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
                    <TabsList className="grid w-full max-w-3xl grid-cols-3">
                        <TabsTrigger value="single">Group Similar Names / Text</TabsTrigger>
                        <TabsTrigger value="multi">Fuzzy lookup two File</TabsTrigger>
                        <TabsTrigger value="api">API Configuration</TabsTrigger>
                    </TabsList>

                    <TabsContent value="single" className="mt-6">
                        <SingleFileFuzzyMatching />
                    </TabsContent>

                    <TabsContent value="multi" className="mt-6">
                        <MultiFileFuzzyMatching />
                    </TabsContent>

                    <TabsContent value="api" className="mt-6">
                        <APIConfigurationPage />
                    </TabsContent>
                </Tabs>
            </div>
        </MainWrapper>
    );
}
