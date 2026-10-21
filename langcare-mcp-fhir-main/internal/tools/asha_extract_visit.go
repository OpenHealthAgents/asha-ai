package tools

import (
	"context"
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/langcare/langcare-mcp-fhir/internal/audit"
	"github.com/langcare/langcare-mcp-fhir/internal/fhir"
)

// AshaExtractVisitTool implements extract_structured_visit_from_transcript
type AshaExtractVisitTool struct {
	client      fhir.Client
	auditLogger *audit.AuditLogger
}

func NewAshaExtractVisitTool(client fhir.Client, auditLogger *audit.AuditLogger) *AshaExtractVisitTool {
	return &AshaExtractVisitTool{
		client:      client,
		auditLogger: auditLogger,
	}
}

func (t *AshaExtractVisitTool) Name() string {
	return "extract_structured_visit_from_transcript"
}

func (t *AshaExtractVisitTool) Description() string {
	return "Accepts regional language ASR transcript (via Sarvam API) and maps symptoms, vitals, and household observations into valid FHIR Encounter, Observation[], and QuestionnaireResponse."
}

func (t *AshaExtractVisitTool) InputSchema() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"transcript": map[string]interface{}{
				"type":        "string",
				"description": "ASR text transcript in Hindi, Odia, Telugu, Tamil, Marathi, Bengali, or Indian English",
			},
			"patient_id": map[string]interface{}{
				"type":        "string",
				"description": "Patient identifier (ABHA or local EMR ID)",
			},
			"worker_id": map[string]interface{}{
				"type":        "string",
				"description": "ASHA or ANM worker ID (HPR ID)",
			},
			"village_lgd_code": map[string]interface{}{
				"type":        "string",
				"description": "Local Government Directory (LGD) village code",
			},
			"language_code": map[string]interface{}{
				"type":        "string",
				"description": "Language code (e.g., hi-IN, or-IN, te-IN)",
			},
			"is_maternal": map[string]interface{}{
				"type":        "boolean",
				"description": "Whether visit is for an Antenatal/Postnatal Care mother",
			},
			"is_pediatric": map[string]interface{}{
				"type":        "boolean",
				"description": "Whether visit is for an infant or young child",
			},
		},
		"required": []string{"transcript", "patient_id", "worker_id", "village_lgd_code"},
	}
}

func (t *AshaExtractVisitTool) Execute(ctx context.Context, args map[string]interface{}) (interface{}, error) {
	transcript, _ := args["transcript"].(string)
	patientID, _ := args["patient_id"].(string)
	workerID, _ := args["worker_id"].(string)
	villageLGD, _ := args["village_lgd_code"].(string)
	languageCode, _ := args["language_code"].(string)
	if languageCode == "" {
		languageCode = "hi-IN"
	}
	isMaternal, _ := args["is_maternal"].(bool)
	isPediatric, _ := args["is_pediatric"].(bool)

	nowISO := time.Now().UTC().Format(time.RFC3339)
	encounterID := fmt.Sprintf("enc-asha-%d", time.Now().UnixNano()%1000000)

	// Simple regex parser for vitals
	vitals := make(map[string]float64)
	bpRe := regexp.MustCompile(`(?i)(?:bp|raktachaap|pressure)?\s*(\d{2,3})\s*(?:/|by|-)\s*(\d{2,3})`)
	if match := bpRe.FindStringSubmatch(transcript); len(match) == 3 {
		s, _ := strconv.ParseFloat(match[1], 64)
		d, _ := strconv.ParseFloat(match[2], 64)
		if s >= 70 && s <= 250 && d >= 40 && d <= 150 {
			vitals["systolic_bp"] = s
			vitals["diastolic_bp"] = d
		}
	}

	hbRe := regexp.MustCompile(`(?i)(?:hemoglobin|hb|khoon)\s*(?:is|tha|hai|:)?\s*(\d{1,2}(?:\.\d)?)`)
	if match := hbRe.FindStringSubmatch(transcript); len(match) == 2 {
		hb, _ := strconv.ParseFloat(match[1], 64)
		if hb >= 2.0 && hb <= 20.0 {
			vitals["hemoglobin"] = hb
		}
	}

	// 1. FHIR Encounter
	encounter := map[string]interface{}{
		"resourceType": "Encounter",
		"id":           encounterID,
		"status":       "finished",
		"class": map[string]interface{}{
			"system":  "http://terminology.hl7.org/CodeSystem/v3-ActCode",
			"code":    "HH",
			"display": "Home Health Visit",
		},
		"subject": map[string]interface{}{
			"reference": fmt.Sprintf("Patient/%s", patientID),
		},
		"participant": []map[string]interface{}{
			{
				"individual": map[string]interface{}{
					"reference": fmt.Sprintf("Practitioner/%s", workerID),
				},
			},
		},
		"period": map[string]interface{}{
			"start": nowISO,
			"end":   nowISO,
		},
		"location": []map[string]interface{}{
			{
				"location": map[string]interface{}{
					"display": fmt.Sprintf("Village LGD %s", villageLGD),
				},
			},
		},
	}

	// 2. FHIR Observations
	var observations []map[string]interface{}
	if s, ok := vitals["systolic_bp"]; ok {
		d := vitals["diastolic_bp"]
		obsBP := map[string]interface{}{
			"resourceType": "Observation",
			"id":           fmt.Sprintf("obs-bp-%d", time.Now().UnixNano()%100000),
			"status":       "final",
			"code": map[string]interface{}{
				"coding": []map[string]interface{}{
					{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"},
				},
			},
			"subject": map[string]interface{}{"reference": fmt.Sprintf("Patient/%s", patientID)},
			"encounter": map[string]interface{}{"reference": fmt.Sprintf("Encounter/%s", encounterID)},
			"effectiveDateTime": nowISO,
			"component": []map[string]interface{}{
				{
					"code": map[string]interface{}{"coding": []map[string]interface{}{{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic BP"}}},
					"valueQuantity": map[string]interface{}{"value": s, "unit": "mmHg"},
				},
				{
					"code": map[string]interface{}{"coding": []map[string]interface{}{{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic BP"}}},
					"valueQuantity": map[string]interface{}{"value": d, "unit": "mmHg"},
				},
			},
		}
		observations = append(observations, obsBP)
	}

	if hb, ok := vitals["hemoglobin"]; ok {
		obsHb := map[string]interface{}{
			"resourceType": "Observation",
			"id":           fmt.Sprintf("obs-hb-%d", time.Now().UnixNano()%100000),
			"status":       "final",
			"code": map[string]interface{}{
				"coding": []map[string]interface{}{
					{"system": "http://loinc.org", "code": "718-7", "display": "Hemoglobin"},
				},
			},
			"subject": map[string]interface{}{"reference": fmt.Sprintf("Patient/%s", patientID)},
			"encounter": map[string]interface{}{"reference": fmt.Sprintf("Encounter/%s", encounterID)},
			"effectiveDateTime": nowISO,
			"valueQuantity": map[string]interface{}{"value": hb, "unit": "g/dL"},
		}
		observations = append(observations, obsHb)
	}

	// 3. FHIR QuestionnaireResponse
	qID := "cbac-ncd-v1"
	if isMaternal {
		qID = "anc-highrisk-v1"
	} else if isPediatric {
		qID = "imnci-pediatric-triage-v1"
	}

	lowerTrans := strings.ToLower(transcript)
	questionnaireResponse := map[string]interface{}{
		"resourceType":  "QuestionnaireResponse",
		"id":            fmt.Sprintf("qr-%d", time.Now().UnixNano()%100000),
		"questionnaire": fmt.Sprintf("Questionnaire/%s", qID),
		"status":        "completed",
		"subject":       map[string]interface{}{"reference": fmt.Sprintf("Patient/%s", patientID)},
		"encounter":     map[string]interface{}{"reference": fmt.Sprintf("Encounter/%s", encounterID)},
		"authored":      nowISO,
		"item": []map[string]interface{}{
			{
				"linkId": "symptoms_recorded",
				"text":   "Transcript symptoms captured",
				"answer": []map[string]interface{}{
					{"valueString": lowerTrans},
				},
			},
		},
	}

	return map[string]interface{}{
		"status":           "SUCCESS",
		"patient_id":       patientID,
		"worker_id":        workerID,
		"village_lgd_code": villageLGD,
		"language_code":    languageCode,
		"extracted_vitals": vitals,
		"fhir_resources": map[string]interface{}{
			"encounter":              encounter,
			"observations":           observations,
			"questionnaire_response": questionnaireResponse,
		},
	}, nil
}
