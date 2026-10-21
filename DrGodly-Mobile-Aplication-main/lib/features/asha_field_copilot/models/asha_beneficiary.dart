/// Represents an individual rural Beneficiary (FHIR Patient)
class AshaBeneficiary {
  final String id;
  final String householdId;
  final String name;
  final String gender;
  final int ageYears;
  final int ageMonths;
  final String? abhaId;
  final String? rchId;
  final bool isMaternal;
  final int? gestationalWeeks;
  final bool isChild;
  final List<String> receivedVaccines;
  final int completedAncVisits;
  final String? lastNcdScreeningDate;

  const AshaBeneficiary({
    required this.id,
    required this.householdId,
    required this.name,
    required this.gender,
    required this.ageYears,
    this.ageMonths = 0,
    this.abhaId,
    this.rchId,
    this.isMaternal = false,
    this.gestationalWeeks,
    this.isChild = false,
    this.receivedVaccines = const [],
    this.completedAncVisits = 0,
    this.lastNcdScreeningDate,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'household_id': householdId,
      'name': name,
      'gender': gender,
      'age_years': ageYears,
      'age_months': ageMonths,
      'abha_id': abhaId,
      'rch_id': rchId,
      'is_maternal': isMaternal ? 1 : 0,
      'gestational_weeks': gestationalWeeks,
      'is_child': isChild ? 1 : 0,
      'received_vaccines': receivedVaccines.join(','),
      'completed_anc_visits': completedAncVisits,
      'last_ncd_screening_date': lastNcdScreeningDate,
    };
  }

  factory AshaBeneficiary.fromMap(Map<String, dynamic> map) {
    List<String> vaccines = [];
    if (map['received_vaccines'] != null && (map['received_vaccines'] as String).isNotEmpty) {
      vaccines = (map['received_vaccines'] as String).split(',');
    }

    return AshaBeneficiary(
      id: map['id'] as String,
      householdId: map['household_id'] as String? ?? '',
      name: map['name'] as String? ?? 'Beneficiary',
      gender: map['gender'] as String? ?? 'female',
      ageYears: map['age_years'] as int? ?? 0,
      ageMonths: map['age_months'] as int? ?? 0,
      abhaId: map['abha_id'] as String?,
      rchId: map['rch_id'] as String?,
      isMaternal: (map['is_maternal'] == 1 || map['is_maternal'] == true),
      gestationalWeeks: map['gestational_weeks'] as int?,
      isChild: (map['is_child'] == 1 || map['is_child'] == true),
      receivedVaccines: vaccines,
      completedAncVisits: map['completed_anc_visits'] as int? ?? 0,
      lastNcdScreeningDate: map['last_ncd_screening_date'] as String?,
    );
  }
}
