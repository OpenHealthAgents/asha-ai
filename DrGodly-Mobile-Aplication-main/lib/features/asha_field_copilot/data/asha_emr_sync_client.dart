import 'dart:convert';
import 'package:dio/dio.dart';
import '../models/asha_care_gap.dart';

/// GraphQL Client communicating with bezs-emr-gql for offline-to-online sync
class AshaEmrSyncClient {
  final Dio _dio;
  final String emrGqlUrl;

  AshaEmrSyncClient({
    Dio? dio,
    this.emrGqlUrl = 'http://10.0.2.2:8000/graphql', // 10.0.2.2 for Android emulator -> localhost
  }) : _dio = dio ??
            Dio(BaseOptions(
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 10),
              headers: {'Content-Type': 'application/json'},
            ));

  /// Executes batch sync mutation syncOfflineFieldVisits
  Future<Map<String, dynamic>> syncOfflineFieldVisits({
    required List<Map<String, dynamic>> visits,
    String? token,
  }) async {
    const mutation = r'''
      mutation SyncOfflineVisits($visits: [OfflineVisitInput!]!) {
        syncOfflineFieldVisits(visits: $visits) {
          batchId
          totalReceived
          totalProcessed
          totalConflictsResolved
          success
          results {
            visitUuid
            status
            conflictResolved
            message
          }
        }
      }
    ''';

    final options = Options(
      headers: token != null ? {'Authorization': 'Bearer $token'} : null,
    );

    final response = await _dio.post(
      emrGqlUrl,
      data: {
        'query': mutation,
        'variables': {'visits': visits},
      },
      options: options,
    );

    if (response.statusCode == 200 && response.data != null) {
      final data = response.data['data']?['syncOfflineFieldVisits'];
      if (data != null) {
        return Map<String, dynamic>.from(data as Map);
      }
    }
    throw Exception('Failed to sync offline visits: ${response.data}');
  }

  /// Fetches village care gaps for all households in a village LGD code
  Future<List<AshaCareGap>> fetchVillageCareGaps({
    required String villageLgdCode,
    String? token,
  }) async {
    const query = r'''
      query GetVillageCareGaps($villageLgdCode: String!) {
        getVillageCareGaps(villageLgdCode: $villageLgdCode) {
          villageLgdCode
          totalOverdueCount
          overdueImmunizations {
            patientId
            patientName
            vaccineCode
            vaccineName
            dueDate
            daysOverdue
            contactPhone
            householdAddress
          }
          missedAncVisits {
            patientId
            patientName
            ancVisitNumber
            expectedGestationalWeek
            weeksOverdue
            contactPhone
            householdAddress
          }
          pendingNcdScreenings {
            patientId
            patientName
            ageYears
            screeningType
            contactPhone
            householdAddress
          }
        }
      }
    ''';

    final options = Options(
      headers: token != null ? {'Authorization': 'Bearer $token'} : null,
    );

    try {
      final response = await _dio.post(
        emrGqlUrl,
        data: {
          'query': query,
          'variables': {'villageLgdCode': villageLgdCode},
        },
        options: options,
      );

      final summary = response.data?['data']?['getVillageCareGaps'];
      if (summary == null) return [];

      List<AshaCareGap> gaps = [];

      // Immunizations
      for (final item in summary['overdueImmunizations'] ?? []) {
        gaps.add(AshaCareGap(
          id: 'gap-imm-${item['patientId']}-${item['vaccineCode']}',
          householdId: item['householdAddress'] ?? 'group-hh-default',
          patientId: item['patientId'] ?? '',
          patientName: item['patientName'] ?? 'Child',
          gapType: 'IMMUNIZATION',
          title: '${item['vaccineCode']} Overdue',
          description: item['vaccineName'] ?? '',
          dueDate: item['dueDate'] ?? '',
          daysOverdue: item['daysOverdue'] ?? 0,
          urgency: 'HIGH',
          action: 'Administer vaccine at upcoming VHSND.',
        ));
      }

      // ANC
      for (final item in summary['missedAncVisits'] ?? []) {
        gaps.add(AshaCareGap(
          id: 'gap-anc-${item['patientId']}-${item['ancVisitNumber']}',
          householdId: item['householdAddress'] ?? 'group-hh-default',
          patientId: item['patientId'] ?? '',
          patientName: item['patientName'] ?? 'Mother',
          gapType: 'ANC_VISIT',
          title: 'Missed ANC #${item['ancVisitNumber']}',
          description: 'Expected gestational week ${item['expectedGestationalWeek']}.',
          dueDate: '',
          daysOverdue: (item['weeksOverdue'] ?? 1) * 7,
          urgency: 'HIGH',
          action: 'Conduct home visit, assess vitals & schedule Sub-Centre check.',
        ));
      }

      return gaps;
    } catch (_) {
      // Fallback offline empty
      return [];
    }
  }
}
