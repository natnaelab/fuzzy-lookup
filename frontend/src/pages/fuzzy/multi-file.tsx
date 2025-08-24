import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/context/AuthContext";
import ApiService from "@/lib/api";

interface FileData {
    file: File | null;
    filename: string;
    columns: Record<string, string>;
    selectedColumn: string;
}

export function MultiFileFuzzyMatching() {
    const { license } = useAuth();

    const [file1, setFile1] = useState<FileData>({
        file: null,
        filename: "",
        columns: {},
        selectedColumn: ""
    });

    const [file2, setFile2] = useState<FileData>({
        file: null,
        filename: "",
        columns: {},
        selectedColumn: ""
    });

    const [threshold, setThreshold] = useState(80);
    const [outputType, setOutputType] = useState("csv");
    const [delimiter, setDelimiter] = useState(",");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [uploadingFile, setUploadingFile] = useState<1 | 2 | null>(null);

    const handleFileUpload = async (uploadedFile: File, fileIndex: 1 | 2) => {
        setUploadingFile(fileIndex);
        setError("");
        setSuccess("");

        try {
            const result = await ApiService.getColumnNames(uploadedFile);

            const fileData: FileData = {
                file: uploadedFile,
                filename: result.filename,
                columns: result.column_names,
                selectedColumn: ""
            };

            if (fileIndex === 1) {
                setFile1(fileData);
            } else {
                setFile2(fileData);
            }

            setSuccess(`File ${fileIndex} loaded: ${uploadedFile.name} - ${Object.keys(result.column_names).length} columns found`);
        } catch (err: any) {
            setError(`Error uploading file ${fileIndex}: ${err.response?.data?.detail || err.message}`);
        } finally {
            setUploadingFile(null);
        }
    };

    const performFuzzyMatching = async () => {
        if (!file1.file || !file2.file || !file1.selectedColumn || !file2.selectedColumn) {
            setError("Please upload both files and select columns for matching");
            return;
        }

        if (!file1.filename || !file2.filename) {
            setError("File upload incomplete. Please try uploading the files again.");
            return;
        }

        setLoading(true);
        setError("");
        setSuccess("");

        try {
            const blob = await ApiService.fuzzyLookupMultiFile({
                file_name_1: file1.filename,
                file_name_2: file2.filename,
                file_1_column: file1.selectedColumn,
                file_2_column: file2.selectedColumn,
                threshold: threshold / 100,
                delimiter: delimiter,
                output_type: outputType
            });

            ApiService.downloadBlob(blob, `fuzzy_match_${Date.now()}.${outputType}`);
            setSuccess("✅ Multi-file fuzzy matching completed! File downloaded.");
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

    const resetForm = () => {
        setFile1({ file: null, filename: "", columns: {}, selectedColumn: "" });
        setFile2({ file: null, filename: "", columns: {}, selectedColumn: "" });
        setError("");
        setSuccess("");
    };

    return (
        <div className="space-y-6">
            {license && (
                <div className="text-right">
                    <Badge variant="secondary" className="text-xs">
                        {license.license_type.toUpperCase()} License
                    </Badge>
                    <p className="text-xs text-muted-foreground">
                        {license.operations_remaining} operations remaining
                    </p>
                </div>
            )}

            {error && (
                <div className="text-sm text-red-600 bg-red-50 p-3 rounded border border-red-200">
                    {error}
                </div>
            )}

            {success && (
                <div className="text-sm text-green-600 bg-green-50 p-3 rounded border border-green-200">
                    {success}
                </div>
            )}

            {/* File Upload Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* File 1 */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <span className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-xs font-bold rounded-full">1</span>
                            First File
                        </CardTitle>
                        <CardDescription>
                            Upload your first CSV or Excel file
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <Label>Choose File</Label>
                            <Input
                                type="file"
                                accept=".csv,.xlsx,.xls"
                                disabled={uploadingFile === 1}
                                onChange={(e) => {
                                    const uploadedFile = e.target.files?.[0];
                                    if (uploadedFile) {
                                        handleFileUpload(uploadedFile, 1);
                                    }
                                }}
                            />
                            {uploadingFile === 1 && (
                                <p className="text-xs text-muted-foreground mt-1">Uploading...</p>
                            )}
                        </div>

                        {Object.keys(file1.columns).length > 0 && (
                            <div>
                                <Label>Select Column for Matching</Label>
                                <Select
                                    value={file1.selectedColumn}
                                    onValueChange={(value) => setFile1({ ...file1, selectedColumn: value })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Choose column to match" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {Object.keys(file1.columns).map((column) => (
                                            <SelectItem key={column} value={column}>
                                                {column}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        )}

                        {file1.file && (
                            <div className="text-xs text-muted-foreground">
                                ✅ {file1.file.name} ({Object.keys(file1.columns).length} columns)
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* File 2 */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <span className="flex items-center justify-center w-6 h-6 bg-green-100 text-green-600 text-xs font-bold rounded-full">2</span>
                            Second File
                        </CardTitle>
                        <CardDescription>
                            Upload your second CSV or Excel file
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <Label>Choose File</Label>
                            <Input
                                type="file"
                                accept=".csv,.xlsx,.xls"
                                disabled={uploadingFile === 2}
                                onChange={(e) => {
                                    const uploadedFile = e.target.files?.[0];
                                    if (uploadedFile) {
                                        handleFileUpload(uploadedFile, 2);
                                    }
                                }}
                            />
                            {uploadingFile === 2 && (
                                <p className="text-xs text-muted-foreground mt-1">Uploading...</p>
                            )}
                        </div>

                        {Object.keys(file2.columns).length > 0 && (
                            <div>
                                <Label>Select Column for Matching</Label>
                                <Select
                                    value={file2.selectedColumn}
                                    onValueChange={(value) => setFile2({ ...file2, selectedColumn: value })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Choose column to match" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {Object.keys(file2.columns).map((column) => (
                                            <SelectItem key={column} value={column}>
                                                {column}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        )}

                        {file2.file && (
                            <div className="text-xs text-muted-foreground">
                                ✅ {file2.file.name} ({Object.keys(file2.columns).length} columns)
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Matching Options */}
            <Card>
                <CardHeader>
                    <CardTitle>Matching Options</CardTitle>
                    <CardDescription>
                        Configure how the fuzzy matching should work
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <Label>Similarity Threshold (%)</Label>
                            <Input
                                type="number"
                                min="0"
                                max="100"
                                value={threshold}
                                onChange={(e) => setThreshold(Number(e.target.value))}
                            />
                            <p className="text-xs text-muted-foreground mt-1">
                                Higher = more strict matching
                            </p>
                        </div>

                        <div>
                            <Label>Output Format</Label>
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

                        <div>
                            <Label>CSV Delimiter</Label>
                            <Select value={delimiter} onValueChange={setDelimiter}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value=",">,  (Comma)</SelectItem>
                                    <SelectItem value=";">;  (Semicolon)</SelectItem>
                                    <SelectItem value="\t">Tab</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="flex gap-4 pt-4">
                        <Button
                            onClick={performFuzzyMatching}
                            disabled={loading || !file1.file || !file2.file || !file1.selectedColumn || !file2.selectedColumn}
                            className="flex-1"
                        >
                            {loading ? "Processing..." : "Find Matches"}
                        </Button>

                        <Button
                            variant="outline"
                            onClick={resetForm}
                            disabled={loading}
                        >
                            Reset
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
