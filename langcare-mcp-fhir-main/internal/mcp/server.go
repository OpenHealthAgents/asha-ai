package mcp

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/langcare/langcare-mcp-fhir/internal/apps"
	"github.com/langcare/langcare-mcp-fhir/internal/config"
	"github.com/langcare/langcare-mcp-fhir/internal/fhir"
	"github.com/langcare/langcare-mcp-fhir/internal/tools"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Server represents the MCP server
type Server struct {
	mcpServer    *mcp.Server
	toolRegistry *tools.Registry
	fhirClient   fhir.Client
	config       *config.Config
}

// NewServer creates a new MCP server with the official SDK
func NewServer(fhirClient fhir.Client, toolRegistry *tools.Registry, cfg *config.Config) (*Server, error) {
	// Create MCP server with implementation info
	impl := &mcp.Implementation{
		Name:    cfg.MCP.Name,
		Version: cfg.MCP.Version,
	}
	mcpServer := mcp.NewServer(impl, nil)

	server := &Server{
		mcpServer:    mcpServer,
		toolRegistry: toolRegistry,
		fhirClient:   fhirClient,
		config:       cfg,
	}

	// Register all tools from registry
	if err := server.registerTools(); err != nil {
		return nil, fmt.Errorf("failed to register tools: %w", err)
	}

	// Register MCP App tools and resources
	server.registerApps()

	// Register NHM ASHA Clinical Handbook Resources
	server.registerNhmResources()

	return server, nil
}

// GetMCPServer returns the underlying MCP server
func (s *Server) GetMCPServer() *mcp.Server {
	return s.mcpServer
}

// registerTools registers all tools from the registry with the MCP server
func (s *Server) registerTools() error {
	toolInfos := s.toolRegistry.List()

	for _, toolInfo := range toolInfos {
		// Create MCP tool definition
		mcpTool := mcp.Tool{
			Name:        toolInfo.Name,
			Description: toolInfo.Description,
			InputSchema: convertToJSONSchema(toolInfo.InputSchema),
		}

		// Capture tool name for closure
		toolName := toolInfo.Name

		// Add tool using the generic AddTool function
		mcp.AddTool(s.mcpServer, &mcpTool, func(ctx context.Context, req *mcp.CallToolRequest, args map[string]interface{}) (*mcp.CallToolResult, any, error) {
			// Get tool from registry
			tool, ok := s.toolRegistry.Get(toolName)
			if !ok {
				return nil, nil, fmt.Errorf("tool not found: %s", toolName)
			}

			// Execute tool
			result, err := tool.Execute(ctx, args)
			if err != nil {
				return &mcp.CallToolResult{
					Content: []mcp.Content{
						&mcp.TextContent{
							Text: fmt.Sprintf("Error: %v", err),
						},
					},
					IsError: true,
				}, nil, nil
			}

			// Format result as JSON
			resultJSON, err := json.MarshalIndent(result, "", "  ")
			if err != nil {
				return nil, nil, fmt.Errorf("failed to marshal result: %w", err)
			}

			return &mcp.CallToolResult{
				Content: []mcp.Content{
					&mcp.TextContent{
						Text: string(resultJSON),
					},
				},
			}, nil, nil
		})
	}

	return nil
}

// registerApps registers MCP App resources and their dedicated tools.
// Each app gets a UI resource and a wrapper tool linked via _meta.ui.resourceUri.
// The View calls generic FHIR tools (fhir_search, fhir_read, etc.) via app.callServerTool().
func (s *Server) registerApps() {
	for _, appConfig := range apps.DefaultApps {
		appConfig := appConfig // capture loop variable

		html, err := apps.LoadAppHTML(appConfig.Name)
		if err != nil {
			log.Printf("Warning: could not load app %s: %v", appConfig.Name, err)
			continue
		}

		// Register the UI resource
		s.mcpServer.AddResource(
			&mcp.Resource{
				URI:         appConfig.ResourceURI,
				Name:        appConfig.Name,
				Description: appConfig.Description,
				MIMEType:    "text/html;profile=mcp-app",
			},
			func(ctx context.Context, req *mcp.ReadResourceRequest) (*mcp.ReadResourceResult, error) {
				return &mcp.ReadResourceResult{
					Contents: []*mcp.ResourceContents{
						{
							URI:      appConfig.ResourceURI,
							MIMEType: "text/html;profile=mcp-app",
							Text:     html,
						},
					},
				}, nil
			},
		)

		// Register the dedicated app tool with _meta.ui linking to the resource
		s.mcpServer.AddTool(
			&mcp.Tool{
				Name:        appConfig.ToolName,
				Description: appConfig.ToolDesc,
				InputSchema: json.RawMessage(`{"type": "object"}`),
				Meta: mcp.Meta{
					"ui": map[string]interface{}{
						"resourceUri": appConfig.ResourceURI,
					},
				},
			},
			func(ctx context.Context, req *mcp.CallToolRequest) (*mcp.CallToolResult, error) {
				return &mcp.CallToolResult{
					Content: []mcp.Content{
						&mcp.TextContent{
							Text: fmt.Sprintf("%s — open in an MCP Apps-capable host to see the interactive UI.", appConfig.Description),
						},
					},
				}, nil
			},
		)

		log.Printf("Registered MCP App: %s (tool: %s)", appConfig.Name, appConfig.ToolName)
	}
}

// registerNhmResources registers Government of India NHM clinical guidelines as MCP resources
func (s *Server) registerNhmResources() {
	nhmGuidelines := []struct {
		URI         string
		Name        string
		Description string
		Content     string
	}{
		{
			URI:         "resource://nhm/handbooks/asha-maternal-child-v1",
			Name:        "NHM ASHA Maternal and Child Health Handbook",
			Description: "National Health Mission ASHA Clinical Guidelines (Module 6 & 7): ANC checkups, IFA prophylaxis, and danger signs.",
			Content:     "# NHM ASHA Module 6 & 7: Maternal and Newborn Care\n4 ANC checkups required. Severe anemia Hb < 7 g/dL and BP >= 140/90 mmHg require immediate 108 referral.",
		},
		{
			URI:         "resource://nhm/workflows/imnci-triage-v1",
			Name:        "IMNCI Pediatric Triage Protocol",
			Description: "Integrated Management of Neonatal and Childhood Illnesses (IMNCI) algorithms (General danger signs, chest indrawing, stridor).",
			Content:     "# IMNCI Protocol\nInability to drink, vomiting everything, convulsions, or chest indrawing indicates Severe Disease requiring urgent referral.",
		},
		{
			URI:         "resource://nhm/workflows/anc-highrisk-protocol-v1",
			Name:        "RMNCH+A High-Risk Pregnancy Guidelines",
			Description: "Protocol for identifying high-risk maternal conditions: Pre-eclampsia, Severe Anemia, Obstetric hemorrhage, and Fetal distress.",
			Content:     "# High-Risk Pregnancy Guidelines\nImmediate referral to FRU with blood bank for severe anemia or hypertensive crisis.",
		},
		{
			URI:         "resource://nhm/guidelines/cbac-ncd-screening-v1",
			Name:        "Ayushman Bharat CBAC NCD Screening",
			Description: "Community Based Assessment Checklist (CBAC) for 30+ population screening for Hypertension, Diabetes, and Cancer.",
			Content:     "# CBAC NCD Screening\nAge 30+ screening: Score > 4 indicates high risk requiring Health and Wellness Centre confirmation.",
		},
	}

	for _, g := range nhmGuidelines {
		guide := g
		s.mcpServer.AddResource(
			&mcp.Resource{
				URI:         guide.URI,
				Name:        guide.Name,
				Description: guide.Description,
				MIMEType:    "text/markdown",
			},
			func(ctx context.Context, req *mcp.ReadResourceRequest) (*mcp.ReadResourceResult, error) {
				return &mcp.ReadResourceResult{
					Contents: []*mcp.ResourceContents{
						{
							URI:      guide.URI,
							MIMEType: "text/markdown",
							Text:     guide.Content,
						},
					},
				}, nil
			},
		)
		log.Printf("Registered NHM Resource: %s (%s)", guide.Name, guide.URI)
	}
}

// convertToJSONSchema converts a map to JSON schema format
func convertToJSONSchema(schema map[string]interface{}) json.RawMessage {
	data, err := json.Marshal(schema)
	if err != nil {
		// Return empty schema on error
		return json.RawMessage(`{"type": "object"}`)
	}
	return json.RawMessage(data)
}
