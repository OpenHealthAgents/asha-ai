package tools

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/langcare/langcare-mcp-fhir/internal/audit"
	"github.com/langcare/langcare-mcp-fhir/internal/fhir"
)

// AshaEvaluateRedFlagsTool implements evaluate_maternal_pediatric_red_flags
type AshaEvaluateRedFlagsTool struct {
	client      fhir.Client
	auditLogger *audit.AuditLogger
}

func NewAshaEvaluateRedFlagsTool(client fhir.Client, auditLogger *audit.AuditLogger) *AshaEvaluateRedFlagsTool {
	return &AshaEvaluateRedFlagsTool{
		client:      client,
		auditLogger: auditLogger,
	}
}

func (t *AshaEvaluateRedFlagsTool) Name() string {
	return "evaluate_maternal_pediatric_red_flags"
}

func (t *AshaEvaluateRedFlagsTool) Description() string {
	return "Deterministic + LLM hybrid clinical rule engine based on NHM/IMNCI guidelines evaluating maternal high-risk flags and pediatric danger signs. Outputs FHIR RiskAssessment (HIGH, MODERATE, LOW)."
}

func (t *AshaEvaluateRedFlagsTool) InputSchema() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"patient_id": map[string]interface{}{
				"type":        "string",
				"description": "Patient identifier",
			},
			"is_maternal": map[string]interface{}{
				"type":        "boolean",
				"description": "True if evaluating pregnant/postpartum mother",
			},
			"gestational_age_weeks": map[string]interface{}{
				"type":        "number",
				"description": "Gestational age in weeks",
			},
			"is_pediatric": map[string]interface{}{
				"type":        "boolean",
				"description": "True if evaluating infant or young child",
			},
			"age_months": map[string]interface{}{
				"type":        "number",
				"description": "Age in months",
			},
			"systolic_bp": map[string]interface{}{
				"type":        "number",
				"description": "Systolic blood pressure (mmHg)",
			},
			"diastolic_bp": map[string]interface{}{
				"type":        "number",
				"description": "Diastolic blood pressure (mmHg)",
			},
			"hemoglobin": map[string]interface{}{
				"type":        "number",
				"description": "Hemoglobin level (g/dL)",
			},
			"spo2": map[string]interface{}{
				"type":        "number",
				"description": "Oxygen saturation (%)",
			},
			"temperature_c": map[string]interface{}{
				"type":        "number",
				"description": "Body temperature in Celsius",
			},
			"respiratory_rate": map[string]interface{}{
				"type":        "number",
				"description": "Breaths per minute",
			},
			"symptoms": map[string]interface{}{
				"type": "array",
				"items": map[string]interface{}{
					"type": "string",
				},
				"description": "List of reported or observed symptoms",
			},
		},
		"required": []string{"patient_id"},
	}
}

func (t *AshaEvaluateRedFlagsTool) Execute(ctx context.Context, args map[string]interface{}) (interface{}, error) {
	patientID, _ := args["patient_id"].(string)
	isMaternal, _ := args["is_maternal"].(bool)
	isPediatric, _ := args["is_pediatric"].(bool)

	var systolic, diastolic, hb, spo2, temp, rr float64
	if v, ok := args["systolic_bp"].(float64); ok {
		systolic = v
	}
	if v, ok := args["diastolic_bp"].(float64); ok {
		diastolic = v
	}
	if v, ok := args["hemoglobin"].(float64); ok {
		hb = v
	}
	if v, ok := args["spo2"].(float64); ok {
		spo2 = v
	}
	if v, ok := args["temperature_c"].(float64); ok {
		temp = v
	}
	if v, ok := args["respiratory_rate"].(float64); ok {
		rr = v
	}

	var symptoms []string
	if syms, ok := args["symptoms"].([]interface{}); ok {
		for _, s := range syms {
			if str, ok := s.(string); ok {
				symptoms = append(symptoms, strings.ToLower(str))
			}
		}
	}

	var triggeredFlags []map[string]interface{}
	riskLevel := "LOW"
	referralFacility := "Village Health Nutrition Day (VHND) / Sub-Centre"
	transportMode := "Routine"

	// 1. Maternal Rules
	if isMaternal {
		if systolic >= 140 || diastolic >= 90 {
			riskLevel = "HIGH"
			triggeredFlags = append(triggeredFlags, map[string]interface{}{
				"code":        "MAT_PREECLAMPSIA_BP",
				"category":    "MATERNAL",
				"severity":    "HIGH",
				"description": fmt.Sprintf("High BP (%0.0f/%0.0f mmHg >= 140/90). Pre-eclampsia danger sign.", systolic, diastolic),
				"action":      "Immediate referral to PHC/FRU. Left lateral positioning.",
			})
		}
		if hb > 0 && hb < 7.0 {
			riskLevel = "HIGH"
			triggeredFlags = append(triggeredFlags, map[string]interface{}{
				"code":        "MAT_SEVERE_ANEMIA",
				"category":    "MATERNAL",
				"severity":    "HIGH",
				"description": fmt.Sprintf("Severe Maternal Anemia (Hb %0.1f g/dL < 7.0 g/dL).", hb),
				"action":      "Immediate referral to FRU/District Hospital with blood bank for IV Iron Sucrose or transfusion.",
			})
		}
		for _, sym := range symptoms {
			if strings.Contains(sym, "bleeding") || strings.Contains(sym, "khoon") {
				riskLevel = "HIGH"
				triggeredFlags = append(triggeredFlags, map[string]interface{}{
					"code":        "MAT_BLEEDING",
					"category":    "MATERNAL",
					"severity":    "HIGH",
					"description": "Vaginal bleeding reported during pregnancy.",
					"action":      "EMERGENCY 108 REFERRAL. Keep mother warm, elevate legs.",
				})
			}
			if strings.Contains(sym, "edema") || strings.Contains(sym, "sujan") {
				if riskLevel != "HIGH" {
					riskLevel = "MODERATE"
				}
				triggeredFlags = append(triggeredFlags, map[string]interface{}{
					"code":        "MAT_EDEMA",
					"category":    "MATERNAL",
					"severity":    "MODERATE",
					"description": "Pedal edema detected. Screen urine albumin.",
					"action":      "Same-day Sub-Centre referral for albumin dipstick check.",
				})
			}
		}
	}

	// 2. Pediatric Rules
	if isPediatric {
		for _, sym := range symptoms {
			if strings.Contains(sym, "breastfeed") || strings.Contains(sym, "doodh") {
				riskLevel = "HIGH"
				triggeredFlags = append(triggeredFlags, map[string]interface{}{
					"code":        "PED_INABILITY_FEED",
					"category":    "PEDIATRIC",
					"severity":    "HIGH",
					"description": "Inability to drink or breastfeed. Key IMNCI General Danger Sign.",
					"action":      "Immediate emergency transport to PHC.",
				})
			}
			if strings.Contains(sym, "convulsion") || strings.Contains(sym, "fits") || strings.Contains(sym, "daura") {
				riskLevel = "HIGH"
				triggeredFlags = append(triggeredFlags, map[string]interface{}{
					"code":        "PED_CONVULSIONS",
					"category":    "PEDIATRIC",
					"severity":    "HIGH",
					"description": "Convulsions / fits during illness.",
					"action":      "Clear airway, position on side, emergency transport to PHC.",
				})
			}
			if strings.Contains(sym, "chest indrawing") || strings.Contains(sym, "pasli") {
				riskLevel = "HIGH"
				triggeredFlags = append(triggeredFlags, map[string]interface{}{
					"code":        "PED_CHEST_INDRAWING",
					"category":    "PEDIATRIC",
					"severity":    "HIGH",
					"description": "Severe Pneumonia / Very Severe Disease (Chest indrawing).",
					"action":      "Urgent PHC referral. Give 1st dose oral amoxicillin if transfer > 2 hours.",
				})
			}
		}

		if (rr >= 50 && spo2 < 92) || (temp >= 38.5 && spo2 > 0 && spo2 < 90) {
			riskLevel = "HIGH"
			triggeredFlags = append(triggeredFlags, map[string]interface{}{
				"code":        "PED_RESPIRATORY_FAILURE",
				"category":    "PEDIATRIC",
				"severity":    "HIGH",
				"description": fmt.Sprintf("Severe hypoxemia (SpO2 %0.0f%%) with respiratory distress.", spo2),
				"action":      "Emergency oxygen and immediate 108 referral.",
			})
		}
	}

	if riskLevel == "HIGH" {
		referralFacility = "First Referral Unit (FRU) / District Hospital"
		transportMode = "108 Emergency Ambulance"
	} else if riskLevel == "MODERATE" {
		referralFacility = "Primary Health Centre (PHC) / Sub-Centre"
		transportMode = "ASHA-accompanied or local transit"
	}

	nowISO := time.Now().UTC().Format(time.RFC3339)
	riskAssessment := map[string]interface{}{
		"resourceType":       "RiskAssessment",
		"id":                 fmt.Sprintf("risk-asha-%d", time.Now().UnixNano()%100000),
		"status":             "final",
		"subject":            map[string]interface{}{"reference": fmt.Sprintf("Patient/%s", patientID)},
		"occurrenceDateTime": nowISO,
		"prediction": []map[string]interface{}{
			{
				"outcome": map[string]interface{}{
					"text": fmt.Sprintf("Triage Risk Level: %s", riskLevel),
				},
				"qualitativeRisk": map[string]interface{}{
					"coding": []map[string]interface{}{
						{"system": "http://terminology.hl7.org/CodeSystem/risk-probability", "code": strings.ToLower(riskLevel)},
					},
				},
			},
		},
		"mitigation": fmt.Sprintf("Referral Facility: %s. Transport: %s.", referralFacility, transportMode),
	}

	return map[string]interface{}{
		"status":                "EVALUATED",
		"risk_level":            riskLevel,
		"referral_facility":     referralFacility,
		"transport_mode":        transportMode,
		"triggered_flags":       triggeredFlags,
		"fhir_risk_assessment": fhirRiskAssessmentOrWrap(riskAssessment),
	}, nil
}

func fhirRiskAssessmentOrWrap(m map[string]interface{}) map[string]interface{} {
	return m
}
