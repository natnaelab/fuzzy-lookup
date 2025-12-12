import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useAuth } from "@/context/AuthContext";
import ApiService, { type APIConfiguration, type UserFile } from "@/lib/api";
import { Trash2, Code } from "lucide-react";

export function APIConfigurationPage() {
    const { license } = useAuth();
    const [configurations, setConfigurations] = useState<APIConfiguration[]>([]);
    const [userFiles, setUserFiles] = useState<UserFile[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    // Form state
    const [selectedFile, setSelectedFile] = useState<number | null>(null);
    const [selectedColumn, setSelectedColumn] = useState("");
    const [configName, setConfigName] = useState("");
    const [configDescription, setConfigDescription] = useState("");
    const [threshold, setThreshold] = useState(80);
    const [availableColumns, setAvailableColumns] = useState<Record<string, string>>({});

    // API docs modal state
    const [selectedConfigForDocs, setSelectedConfigForDocs] = useState<number | null>(null);
    const [apiDocs, setApiDocs] = useState<any>(null);

    // Load configurations and files on mount
    useEffect(() => {
        loadConfigurations();
        loadUserFiles();
    }, []);

    const loadConfigurations = async () => {
        try {
            const configs = await ApiService.getAPIConfigs();
            setConfigurations(configs);
        } catch (err: any) {
            console.error("Failed to load configurations:", err);
        }
    };

    const loadUserFiles = async () => {
        try {
            const response = await ApiService.getUserFiles(100);
            setUserFiles(response.files);
        } catch (err: any) {
            console.error("Failed to load files:", err);
        }
    };

    const handleFileSelect = async (fileId: number) => {
        setSelectedFile(fileId);
        setSelectedColumn("");
        setAvailableColumns({});

        try {
            const response = await ApiService.getFileColumns(fileId);
            setAvailableColumns(response.column_names);
        } catch (err: any) {
            setError(`Failed to load file columns: ${err.message}`);
        }
    };

    const handleCreateConfiguration = async () => {
        if (!selectedFile || !selectedColumn || !configName) {
            setError("Please fill in all required fields");
            return;
        }

        setLoading(true);
        setError("");
        setSuccess("");

        try {
            await ApiService.createAPIConfig({
                name: configName,
                description: configDescription || undefined,
                file_id: selectedFile,
                column_name: selectedColumn,
                threshold: threshold / 100,
            });

            setSuccess("✅ API configuration created successfully!");

            // Reset form
            setSelectedFile(null);
            setSelectedColumn("");
            setConfigName("");
            setConfigDescription("");
            setThreshold(80);
            setAvailableColumns({});

            // Reload configurations
            loadConfigurations();
        } catch (err: any) {
            setError(`❌ ${err.response?.data?.detail || err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteConfiguration = async (configId: number) => {
        if (!confirm("Are you sure you want to delete this configuration?")) {
            return;
        }

        try {
            await ApiService.deleteAPIConfig(configId);
            setSuccess("Configuration deleted successfully");
            loadConfigurations();
        } catch (err: any) {
            setError(`Failed to delete: ${err.message}`);
        }
    };

    const handleViewDocs = async (configId: number) => {
        try {
            const docs = await ApiService.getAPIConfigDocs(configId);
            setApiDocs(docs);
            setSelectedConfigForDocs(configId);
        } catch (err: any) {
            setError(`Failed to load documentation: ${err.message}`);
        }
    };

    return (
        <div className="space-y-6">
            {license && (
                <div className="text-right">
                    <Badge variant="secondary" className="text-xs">
                        {license.display_name}
                    </Badge>
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

            {/* Create New Configuration */}
            <Card>
                <CardHeader>
                    <CardTitle>Create API Configuration</CardTitle>
                    <CardDescription>
                        Upload a dataset and configure it for API access. External applications can query this dataset using your credentials.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <Label htmlFor="config-name">Configuration Name *</Label>
                            <Input
                                id="config-name"
                                placeholder="e.g., Company Names Lookup"
                                value={configName}
                                onChange={(e) => setConfigName(e.target.value)}
                            />
                        </div>

                        <div>
                            <Label htmlFor="config-desc">Description (optional)</Label>
                            <Input
                                id="config-desc"
                                placeholder="Brief description of this dataset"
                                value={configDescription}
                                onChange={(e) => setConfigDescription(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <Label>Select Reference Dataset *</Label>
                        <Select
                            value={selectedFile?.toString() || ""}
                            onValueChange={(value) => handleFileSelect(parseInt(value))}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Choose a file from your uploads" />
                            </SelectTrigger>
                            <SelectContent>
                                {userFiles.map((file) => (
                                    <SelectItem key={file.id} value={file.id.toString()}>
                                        {file.original_filename} ({file.file_size_mb} MB)
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        {userFiles.length === 0 && (
                            <p className="text-xs text-muted-foreground mt-1">
                                No files uploaded yet. Upload files in the other tabs first.
                            </p>
                        )}
                    </div>

                    {Object.keys(availableColumns).length > 0 && (
                        <div>
                            <Label>Column to Match On *</Label>
                            <Select
                                value={selectedColumn}
                                onValueChange={setSelectedColumn}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Choose column for fuzzy matching" />
                                </SelectTrigger>
                                <SelectContent>
                                    {Object.keys(availableColumns).map((column) => (
                                        <SelectItem key={column} value={column}>
                                            {column}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>Default Threshold (%)</Label>
                            <Input
                                type="number"
                                min="0"
                                max="100"
                                value={threshold}
                                onChange={(e) => setThreshold(Number(e.target.value))}
                            />
                            <p className="text-xs text-muted-foreground mt-1">
                                Can be overridden in API requests
                            </p>
                        </div>
                    </div>

                    <Button
                        onClick={handleCreateConfiguration}
                        disabled={loading || !selectedFile || !selectedColumn || !configName}
                        className="w-full"
                    >
                        {loading ? "Creating..." : "Create Configuration"}
                    </Button>
                </CardContent>
            </Card>

            {/* List of Configurations */}
            <Card>
                <CardHeader>
                    <CardTitle>Your API Configurations</CardTitle>
                    <CardDescription>
                        Manage your saved API configurations and view usage documentation
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {configurations.length === 0 ? (
                        <div className="text-center text-muted-foreground py-8">
                            No configurations created yet. Create one above to get started.
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {configurations.map((config) => (
                                <div
                                    key={config.id}
                                    className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <h3 className="font-semibold">{config.name}</h3>
                                                {!config.is_active && (
                                                    <Badge variant="secondary">Inactive</Badge>
                                                )}
                                            </div>
                                            {config.description && (
                                                <p className="text-sm text-muted-foreground mt-1">
                                                    {config.description}
                                                </p>
                                            )}
                                            <div className="flex flex-wrap gap-4 mt-2 text-xs text-muted-foreground">
                                                <span>File: {config.filename}</span>
                                                <span>Column: {config.column_name}</span>
                                                <span>Threshold: {(config.threshold * 100).toFixed(0)}%</span>
                                                <span>ID: {config.id}</span>
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            <Dialog>
                                                <DialogTrigger asChild>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handleViewDocs(config.id)}
                                                    >
                                                        <Code className="w-4 h-4 mr-1" />
                                                        API Docs
                                                    </Button>
                                                </DialogTrigger>
                                                <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                                                    <DialogHeader>
                                                        <DialogTitle>API Documentation - {config.name}</DialogTitle>
                                                        <DialogDescription>
                                                            Use these endpoints to query your dataset programmatically
                                                        </DialogDescription>
                                                    </DialogHeader>
                                                    {apiDocs && selectedConfigForDocs === config.id && (
                                                        <div className="space-y-6 text-sm">
                                                            <section className="space-y-2">
                                                                <h4 className="font-semibold">Step 1: Authenticate</h4>
                                                                <p>
                                                                    Use your account email and password to request a{" "}
                                                                    {apiDocs.authentication?.type || "JWT"} token. Keep the
                                                                    returned <code>access_token</code> handy for every API call.
                                                                </p>
                                                                <div className="bg-muted p-3 rounded text-xs space-y-2">
                                                                    <div className="font-semibold">
                                                                        {apiDocs.authentication?.example?.request?.method || "POST"}{" "}
                                                                        {apiDocs.authentication?.login_endpoint}
                                                                    </div>
                                                                    {apiDocs.authentication?.example?.request?.body && (
                                                                        <div>
                                                                            <div className="uppercase tracking-wide text-[10px] text-muted-foreground">
                                                                                Request body
                                                                            </div>
                                                                            <pre className="mt-1 bg-background p-2 rounded border text-[11px] overflow-x-auto">
                                                                                {JSON.stringify(apiDocs.authentication.example.request.body, null, 2)}
                                                                            </pre>
                                                                        </div>
                                                                    )}
                                                                    {apiDocs.authentication?.example?.response && (
                                                                        <div>
                                                                            <div className="uppercase tracking-wide text-[10px] text-muted-foreground">
                                                                                Sample response
                                                                            </div>
                                                                            <pre className="mt-1 bg-background p-2 rounded border text-[11px] overflow-x-auto">
                                                                                {JSON.stringify(apiDocs.authentication.example.response, null, 2)}
                                                                            </pre>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </section>

                                                            <section className="space-y-2">
                                                                <h4 className="font-semibold">Step 2: Query your dataset</h4>
                                                                <p>
                                                                    Call your configuration endpoint with the search term. Add the token from Step 1 as a
                                                                    <code>Bearer</code> header.
                                                                </p>
                                                                <div className="bg-muted p-3 rounded text-xs space-y-2">
                                                                    <div className="font-semibold">
                                                                        {apiDocs.query_endpoint?.method || "POST"}{" "}
                                                                        {apiDocs.query_endpoint?.url}
                                                                    </div>
                                                                    {apiDocs.query_endpoint?.headers && (
                                                                        <div>
                                                                            <div className="uppercase tracking-wide text-[10px] text-muted-foreground">
                                                                                Headers
                                                                            </div>
                                                                            <pre className="mt-1 bg-background p-2 rounded border text-[11px] overflow-x-auto">
                                                                                {JSON.stringify(apiDocs.query_endpoint.headers, null, 2)}
                                                                            </pre>
                                                                        </div>
                                                                    )}
                                                                    {apiDocs.query_endpoint?.body && (
                                                                        <div>
                                                                            <div className="uppercase tracking-wide text-[10px] text-muted-foreground">
                                                                                Request body
                                                                            </div>
                                                                            <pre className="mt-1 bg-background p-2 rounded border text-[11px] overflow-x-auto">
                                                                                {JSON.stringify(apiDocs.query_endpoint.body, null, 2)}
                                                                            </pre>
                                                                        </div>
                                                                    )}
                                                                    {apiDocs.query_endpoint?.example_response && (
                                                                        <div>
                                                                            <div className="uppercase tracking-wide text-[10px] text-muted-foreground">
                                                                                Sample response
                                                                            </div>
                                                                            <pre className="mt-1 bg-background p-2 rounded border text-[11px] overflow-x-auto">
                                                                                {JSON.stringify(apiDocs.query_endpoint.example_response, null, 2)}
                                                                            </pre>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </section>

                                                            <section className="space-y-2">
                                                                <h4 className="font-semibold">cURL example</h4>
                                                                <pre className="bg-muted p-3 rounded text-xs whitespace-pre-wrap">
                                                                    {apiDocs.curl_example}
                                                                </pre>
                                                            </section>
                                                        </div>
                                                    )}
                                                </DialogContent>
                                            </Dialog>
                                            <Button
                                                variant="destructive"
                                                size="sm"
                                                onClick={() => handleDeleteConfiguration(config.id)}
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
