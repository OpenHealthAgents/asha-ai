/// Offline Mutation Outbox entry for resilient offline-to-online sync
class AshaSyncMutation {
  final String mutationId;
  final String visitUuid;
  final String mutationType; // "VISIT_SYNC" | "VOICE_CHUNK" | "REGISTER_OCR" | "POC_VITALS"
  final String payloadJson;
  final String? localAudioFilePath;
  final String status; // "PENDING" | "SYNCING" | "SYNCED" | "FAILED"
  final int retryCount;
  final String createdAt;
  final String? lastAttemptedAt;
  final String? errorMessage;

  const AshaSyncMutation({
    required this.mutationId,
    required this.visitUuid,
    required this.mutationType,
    required this.payloadJson,
    this.localAudioFilePath,
    this.status = 'PENDING',
    this.retryCount = 0,
    required this.createdAt,
    this.lastAttemptedAt,
    this.errorMessage,
  });

  Map<String, dynamic> toMap() {
    return {
      'mutation_id': mutationId,
      'visit_uuid': visitUuid,
      'mutation_type': mutationType,
      'payload_json': payloadJson,
      'local_audio_file_path': localAudioFilePath,
      'status': status,
      'retry_count': retryCount,
      'created_at': createdAt,
      'last_attempted_at': lastAttemptedAt,
      'error_message': errorMessage,
    };
  }

  factory AshaSyncMutation.fromMap(Map<String, dynamic> map) {
    return AshaSyncMutation(
      mutationId: map['mutation_id'] as String,
      visitUuid: map['visit_uuid'] as String,
      mutationType: map['mutation_type'] as String,
      payloadJson: map['payload_json'] as String,
      localAudioFilePath: map['local_audio_file_path'] as String?,
      status: map['status'] as String? ?? 'PENDING',
      retryCount: map['retry_count'] as int? ?? 0,
      createdAt: map['created_at'] as String,
      lastAttemptedAt: map['last_attempted_at'] as String?,
      errorMessage: map['error_message'] as String?,
    );
  }

  AshaSyncMutation copyWith({
    String? status,
    int? retryCount,
    String? lastAttemptedAt,
    String? errorMessage,
  }) {
    return AshaSyncMutation(
      mutationId: mutationId,
      visitUuid: visitUuid,
      mutationType: mutationType,
      payloadJson: payloadJson,
      localAudioFilePath: localAudioFilePath,
      status: status ?? this.status,
      retryCount: retryCount ?? this.retryCount,
      createdAt: createdAt,
      lastAttemptedAt: lastAttemptedAt ?? this.lastAttemptedAt,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}
