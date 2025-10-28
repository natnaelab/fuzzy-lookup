import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/context/AuthContext";
import ApiService from "@/lib/api";

export function SingleFileFuzzyMatching() {
    const { license } = useAuth();
    const [file, setFile] = useState<File | null>(null);
    const [columns, setColumns] = useState<Record<string, string>>({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [threshold, setThreshold] = useState(80);
    const [selectedColumn, setSelectedColumn] = useState("");
    const [outputType, setOutputType] = useState("csv");

    const handleFileUpload = async (uploadedFile: File) => {
        setLoading(true);
        setError("");
        setSuccess("");

        try {
            const result = await ApiService.getColumnNames(uploadedFile);
            setColumns(result.column_names);
            setFile(uploadedFile);
            setSuccess(`File loaded: ${uploadedFile.name} - ${Object.keys(result.column_names).length} columns found`);
        } catch (err: any) {
            setError(`Error: ${err.response?.data?.detail || err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const findDuplicates = async () => {
        if (!file || !selectedColumn) {
            setError("Please upload a file and select a column");
            return;
        }

        setLoading(true);
        setError("");
        setSuccess("");

        try {
            const blob = await ApiService.findDuplicates(
                file,
                selectedColumn,
                threshold / 100,
                outputType
            );

            ApiService.downloadBlob(blob, `duplicates_${Date.now()}.${outputType}`);
            setSuccess("✅ File processed and downloaded!");
        } catch (err: any) {
            let errorMessage = "Something went wrong";

            if (err.response?.data?.detail) {
                errorMessage = err.response.data.detail;
            } else if (err.message) {
                errorMessage = err.message;
            }
            setError(`❌ ${errorMessage}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {license && (
                <div className="text-right">
                    <Badge variant="secondary" className="text-xs">
                        {license.display_name}
                    </Badge>
                    <p className="text-xs text-muted-foreground">
                        {license.conversions_remaining === null
                            ? "Unlimited conversions"
                            : `${license.conversions_remaining} conversions remaining`}
                    </p>
                </div>
            )}

            <Card>
                <CardHeader>
                    <CardTitle>Upload Your File</CardTitle>
                    <CardDescription>
                        Upload a CSV or Excel file to find duplicate entries
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {error && (
                        <div className="text-sm text-red-600 bg-red-50 p-3 rounded">
                            {error}
                        </div>
                    )}

                    {success && (
                        <div className="text-sm text-green-600 bg-green-50 p-3 rounded">
                            {success}
                        </div>
                    )}

                    <div className="space-y-4">
                        <Label>Choose File</Label>
                        <Input
                            type="file"
                            accept=".csv,.xlsx,.xls"
                            onChange={(e) => {
                                const uploadedFile = e.target.files?.[0];
                                if (uploadedFile) {
                                    handleFileUpload(uploadedFile);
                                }
                            }}
                        />
                    </div>

                    {Object.keys(columns).length > 0 && (
                        <div className="space-y-4">
                            <Label>Select Column with Names</Label>
                            <Select value={selectedColumn} onValueChange={setSelectedColumn}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Choose the column to check for duplicates" />
                                </SelectTrigger>
                                <SelectContent>
                                    {Object.keys(columns).map((column) => (
                                        <SelectItem key={column} value={column}>
                                            {column}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <Label>Threshold (%)</Label>
                            <Input
                                type="number"
                                min="0"
                                max="100"
                                value={threshold}
                                onChange={(e) => setThreshold(Number(e.target.value))}
                            />
                        </div>

                        <div>
                            <Label>Download As</Label>
                            <Select value={outputType} onValueChange={setOutputType}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="csv">CSV</SelectItem>
                                    <SelectItem value="xlsx">Excel</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <Button
                        onClick={findDuplicates}
                        disabled={loading || !file || !selectedColumn}
                        className="w-full"
                    >
                        {loading ? "Finding Duplicates..." : "Find Duplicates"}
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}
