import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'asha_local_database.dart';
import 'asha_emr_sync_client.dart';
import 'asha_filenest_client.dart';
import '../models/asha_sync_mutation.dart';

/// Sync Queue Service managing the offline mutation outbox
class AshaSyncQueueService {
  static final AshaSyncQueueService instance = AshaSyncQueueService._init();
  final AshaLocalDatabase _db = AshaLocalDatabase.instance;
  final AshaEmrSyncClient _emrClient = AshaEmrSyncClient();
  final AshaFilenestClient _filenestClient = AshaFilenestClient();

  bool _isSyncing = false;
  bool get isSyncing => _isSyncing;

  final _syncStatusController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get syncStatusStream => _syncStatusController.stream;

  AshaSyncQueueService._init();

  /// Enqueue a visit mutation for offline storage and eventual sync
  Future<void> enqueueVisitSync({
    required String visitUuid,
    required Map<String, dynamic> visitPayload,
    String? localAudioFilePath,
  }) async {
    final mutation = AshaSyncMutation(
      mutationId: 'mut-${DateTime.now().millisecondsSinceEpoch}-${visitUuid.substring(0, 8)}',
      visitUuid: visitUuid,
      mutationType: 'VISIT_SYNC',
      payloadJson: jsonEncode(visitPayload),
      localAudioFilePath: localAudioFilePath,
      createdAt: DateTime.now().toUtc().toIso8601String(),
    );

    await _db.enqueueMutation(mutation);
    _notifySyncState();

    // Trigger sync attempt immediately in background
    triggerSync();
  }

  /// Triggers outbox synchronization when network connectivity is available
  Future<void> triggerSync() async {
    if (_isSyncing) return;
    _isSyncing = true;
    _notifySyncState();

    try {
      final pendingMutations = await _db.getPendingMutations();
      if (pendingMutations.isEmpty) {
        _isSyncing = false;
        _notifySyncState();
        return;
      }

      for (final mutation in pendingMutations) {
        await _processMutation(mutation);
      }
    } catch (e) {
      if (kDebugMode) {
        print('[AshaSyncQueueService] Sync batch error: $e');
      }
    } finally {
      _isSyncing = false;
      _notifySyncState();
    }
  }

  Future<void> _processMutation(AshaSyncMutation mutation) async {
    await _db.updateMutationStatus(mutation.mutationId, 'SYNCING');

    try {
      // 1. If audio file exists, upload to bezs-filenest first
      if (mutation.localAudioFilePath != null && mutation.localAudioFilePath!.isNotEmpty) {
        final file = File(mutation.localAudioFilePath!);
        if (await file.exists()) {
          final payload = jsonDecode(mutation.payloadJson) as Map<String, dynamic>;
          await _filenestClient.uploadAudioFileInChunks(
            audioFile: file,
            visitUuid: mutation.visitUuid,
            workerId: payload['worker_id'] ?? 'usr-asha-sunita',
            patientId: payload['patient_id'] ?? 'patient-default',
            villageLgdCode: payload['village_lgd_code'] ?? '215432',
          );
        }
      }

      // 2. Sync to bezs-emr-gql via GraphQL mutation
      final payload = jsonDecode(mutation.payloadJson) as Map<String, dynamic>;
      final emrVisits = [
        {
          'visitUuid': mutation.visitUuid,
          'patientId': payload['patient_id'] ?? 'patient-default',
          'workerId': payload['worker_id'] ?? 'usr-asha-sunita',
          'villageLgdCode': payload['village_lgd_code'] ?? '215432',
          'clientTimestamp': mutation.createdAt,
          'encounterType': payload['encounter_type'] ?? 'household_visit',
          'observations': payload['observations'] ?? [],
          'questionnaireResponses': payload['questionnaire_responses'] ?? [],
          'audioRecordingRef': mutation.localAudioFilePath != null ? 'filenest://${mutation.visitUuid}.opus' : null,
          'isHighRisk': payload['is_high_risk'] ?? false,
          'triageCategory': payload['triage_category'] ?? 'ROUTINE',
        }
      ];

      final result = await _emrClient.syncOfflineFieldVisits(visits: emrVisits);
      if (result['success'] == true) {
        await _db.markMutationSynced(mutation.mutationId);
      } else {
        await _db.updateMutationStatus(
          mutation.mutationId,
          'FAILED',
          errorMessage: 'EMR sync unconfirmed',
        );
      }
    } catch (e) {
      await _db.updateMutationStatus(
        mutation.mutationId,
        'FAILED',
        errorMessage: e.toString(),
      );
    }
  }

  void _notifySyncState() async {
    final pendingCount = await _db.getPendingOutboxCount();
    _syncStatusController.add({
      'is_syncing': _isSyncing,
      'pending_outbox_count': pendingCount,
    });
  }
}
