import 'dart:convert';
import 'asha_beneficiary.dart';

/// Represents a rural Household Group cached from medplum/bezs-emr-gql
class AshaHousehold {
  final String id;
  final String villageLgdCode;
  final String headName;
  final String address;
  final String wardNumber;
  final String contactPhone;
  final int memberCount;
  final List<AshaBeneficiary> members;

  const AshaHousehold({
    required this.id,
    required this.villageLgdCode,
    required this.headName,
    required this.address,
    required this.wardNumber,
    required this.contactPhone,
    required this.memberCount,
    this.members = const [],
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'village_lgd_code': villageLgdCode,
      'head_name': headName,
      'address': address,
      'ward_number': wardNumber,
      'contact_phone': contactPhone,
      'member_count': memberCount,
      'members_json': jsonEncode(members.map((m) => m.toMap()).toList()),
    };
  }

  factory AshaHousehold.fromMap(Map<String, dynamic> map) {
    List<AshaBeneficiary> membersList = [];
    if (map['members_json'] != null) {
      try {
        final decoded = jsonDecode(map['members_json'] as String) as List<dynamic>;
        membersList = decoded.map((item) => AshaBeneficiary.fromMap(item as Map<String, dynamic>)).toList();
      } catch (_) {}
    }

    return AshaHousehold(
      id: map['id'] as String,
      villageLgdCode: map['village_lgd_code'] as String? ?? '',
      headName: map['head_name'] as String? ?? 'Head of Household',
      address: map['address'] as String? ?? '',
      wardNumber: map['ward_number'] as String? ?? '',
      contactPhone: map['contact_phone'] as String? ?? '',
      memberCount: map['member_count'] as int? ?? membersList.length,
      members: membersList,
    );
  }

  AshaHousehold copyWith({
    String? id,
    String? villageLgdCode,
    String? headName,
    String? address,
    String? wardNumber,
    String? contactPhone,
    int? memberCount,
    List<AshaBeneficiary>? members,
  }) {
    return AshaHousehold(
      id: id ?? this.id,
      villageLgdCode: villageLgdCode ?? this.villageLgdCode,
      headName: headName ?? this.headName,
      address: address ?? this.address,
      wardNumber: wardNumber ?? this.wardNumber,
      contactPhone: contactPhone ?? this.contactPhone,
      memberCount: memberCount ?? this.memberCount,
      members: members ?? this.members,
    );
  }
}
