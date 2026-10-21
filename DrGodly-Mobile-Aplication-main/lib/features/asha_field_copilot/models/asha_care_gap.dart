/// Care gap model representing overdue immunization, missed ANC, or pending NCD
class AshaCareGap {
  final String id;
  final String householdId;
  final String patientId;
  final String patientName;
  final String gapType; // "IMMUNIZATION" | "ANC_VISIT" | "NCD_SCREENING"
  final String title;
  final String description;
  final String dueDate;
  final int daysOverdue;
  final String urgency; // "HIGH" | "MEDIUM" | "ROUTINE"
  final String action;
  final bool isResolved;

  const AshaCareGap({
    required this.id,
    required this.householdId,
    required this.patientId,
    required this.patientName,
    required this.gapType,
    required this.title,
    required this.description,
    required this.dueDate,
    required this.daysOverdue,
    required this.urgency,
    required this.action,
    this.isResolved = false,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'household_id': householdId,
      'patient_id': patientId,
      'patient_name': patientName,
      'gap_type': gapType,
      'title': title,
      'description': description,
      'due_date': dueDate,
      'days_overdue': daysOverdue,
      'urgency': urgency,
      'action': action,
      'is_resolved': isResolved ? 1 : 0,
    };
  }

  factory AshaCareGap.fromMap(Map<String, dynamic> map) {
    return AshaCareGap(
      id: map['id'] as String,
      householdId: map['household_id'] as String? ?? '',
      patientId: map['patient_id'] as String? ?? '',
      patientName: map['patient_name'] as String? ?? 'Beneficiary',
      gapType: map['gap_type'] as String? ?? 'IMMUNIZATION',
      title: map['title'] as String? ?? '',
      description: map['description'] as String? ?? '',
      dueDate: map['due_date'] as String? ?? '',
      daysOverdue: map['days_overdue'] as int? ?? 0,
      urgency: map['urgency'] as String? ?? 'MEDIUM',
      action: map['action'] as String? ?? '',
      isResolved: (map['is_resolved'] == 1 || map['is_resolved'] == true),
    );
  }
}
