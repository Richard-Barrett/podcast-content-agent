# Extended production architecture notes

These notes preserve implementation detail beyond the take-home's official
500-word deployment response. The submission answer is
[`deployment_strategy.md`](deployment_strategy.md).

## Goals

The production design should preserve one independently retryable job per episode,
stable input/output contracts, provider-independent inference, retrieval-backed
verification, auditable processing, and no permanently running compute while the
queue is empty.

## Proposed architecture

```text
Transcript producer
      |
      v
S3 input bucket -- event --> EventBridge --> SQS input queue
                                            |
                                            v
                                    ECS Fargate worker
                                      |   |       |
                                      |   |       +--> Bedrock / approved LLM
                                      |   +----------> curated retrieval service
                                      +--------------> DynamoDB job state
                                            |
                       +--------------------+--------------------+
                       v                    v                    v
                 S3 output bucket      CloudWatch          SQS DLQ
```

Package the application as a versioned Docker image in Amazon ECR. An S3
object-created event routes through EventBridge to SQS. Workers can run as an
auto-scaled ECS service or as one Fargate task per job. Queue depth controls
concurrency and absorbs ingestion spikes without overloading model providers.

## Processing lifecycle

1. A producer writes a transcript to a versioned, encrypted S3 input bucket.
2. EventBridge normalizes the event and sends a compact job envelope to SQS.
3. A worker checks an idempotency record in DynamoDB using the transcript hash and
   pipeline version.
4. The worker downloads the transcript and selected prompt/knowledge-base version.
5. Editorial analysis runs through Bedrock or another approved provider adapter.
6. Extracted claims are checked against curated evidence.
7. JSON, Markdown, and a manifest are written atomically to the output bucket.
8. Metrics and structured events go to CloudWatch before the message is deleted.

The manifest should record the input hash, container version, prompt version, model
ID, knowledge-base snapshot, output-schema version, timestamps, and cost metadata.

## Service choices

| Concern | AWS service | Rationale |
|---|---|---|
| Input and output objects | S3 | Durable, inexpensive, versioned object storage |
| Event routing | EventBridge | Decouples object events from queue and worker details |
| Back-pressure and retry | SQS | Visibility timeouts, redrive policy, queue-depth scaling |
| Compute | ECS Fargate | Runs the existing image without managing hosts |
| Image registry | ECR | Versioned private container distribution |
| Model inference | Amazon Bedrock | Managed scaling and IAM-based access to approved models |
| Job and idempotency state | DynamoDB | Conditional writes and low-maintenance keyed state |
| Logs, metrics, and alarms | CloudWatch | Central operational telemetry and alerting |
| Secrets | Secrets Manager | Rotation and runtime retrieval of provider keys |
| Encryption keys | KMS | Customer-managed encryption policy where required |

For a small local knowledge base, store a versioned snapshot in S3 and load it when
the task starts. At larger scale, move retrieval behind a service backed by
OpenSearch Serverless, Aurora PostgreSQL with an approved vector extension, or a
purpose-built curated search index. Preserve the current `Verification` response
contract so orchestration and rendering remain unchanged.

## Scaling

Scale workers from SQS visible-message count and age of oldest message. Set a hard
maximum task count based on provider quotas and downstream capacity. Apply
token-bucket admission control when model calls have strict rate limits.

Keep workers stateless. If editorial analysis and fact verification develop
different latency or resource profiles, split them into separate queues and worker
services with intermediate results in S3 or DynamoDB. This lets each stage scale
independently without changing the public output contract.

## Reliability and recovery

- Set visibility timeouts above expected processing time and extend them for healthy
  long-running jobs.
- Use bounded exponential backoff with jitter for throttling and transient provider
  failures.
- Route messages to a DLQ after a small, explicit retry count.
- Make writes idempotent and use deterministic object keys.
- Store successful expensive stage results so retries can resume.
- Distinguish retryable transport failures from permanent schema/input failures.
- Alarm on DLQ depth, oldest-message age, error rate, p95 duration, throttling, and
  missing output manifests.
- Provide a reviewed DLQ replay procedure rather than automatically replaying poison
  messages.

The local heuristic fallback can remain available as a degraded editorial mode, but
production policy should decide which failures may use it and which require a retry
or manual review.

## Security and privacy

- Use separate IAM task and execution roles with least-privilege access.
- Encrypt S3, SQS, DynamoDB, logs, and secrets with KMS.
- Block public S3 access and enforce TLS.
- Use private subnets and VPC endpoints where required.
- Retrieve external provider credentials from Secrets Manager at runtime.
- Put object references, not transcript text or secrets, in queue messages.
- Apply retention and deletion policies appropriate to customer requirements.
- Redact or hash sensitive identifiers in logs.
- Scan the image and pin approved base-image and dependency versions.
- Record access with CloudTrail and review infrastructure-as-code changes.

Healthcare or other regulated transcripts require a separate data-classification
review, provider eligibility check, and confirmation of contractual controls before
processing.

## Cost controls

Model inference will usually dominate unit cost. Record input/output tokens, model,
latency, retries, and estimated cost per episode. Use a lower-cost model for routine
summarization and reserve stronger models for ambiguous extraction or review.

Additional controls include deduplicating by transcript and pipeline hash, caching
retrieval and successful stages, enforcing token limits, lifecycle-expiring temporary
objects and verbose logs, scaling Fargate to zero, evaluating Fargate Spot for
retry-safe work, and using provisioned inference only after sustained utilization
justifies it.

## Delivery and environments

Build the image once, scan it, and promote the same digest through development,
staging, and production. Manage queues, buckets, roles, alarms, and task definitions
with Terraform, AWS CDK, or CloudFormation.

A safe release sequence runs static and deterministic end-to-end tests, builds and
scans the image, evaluates a fixed corpus in staging, deploys a limited canary,
promotes gradually under alarms, and rolls back by task-definition revision when
needed.

## Production readiness gaps

Before implementation, add explicit JSON Schema validation; prompt, model, KB, and
schema versioning; durable checkpoints; provider retry and circuit-breaker policies;
quality evaluation datasets; provenance-rich evidence connectors; infrastructure as
code; operational dashboards and runbooks; DLQ replay tooling; and data retention,
deletion, and tenancy controls.
