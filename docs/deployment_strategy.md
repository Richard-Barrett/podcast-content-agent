# AWS deployment strategy

This is the submission deployment strategy and intentionally stays below the
assignment's 500-word maximum. Extended design notes are available in
[`production_architecture_notes.md`](production_architecture_notes.md).

## Architecture

Package the existing application as a versioned container in Amazon ECR. Podcast
transcripts arrive in an encrypted, versioned S3 input bucket. S3 events route
through EventBridge to an SQS queue, which decouples uploads from processing and
provides back-pressure. An ECS Fargate worker consumes one episode per job, invokes
Amazon Bedrock or another approved model through the existing provider interface,
checks extracted claims against a curated retrieval service, and writes JSON and
Markdown results to an S3 output bucket.

DynamoDB stores the transcript hash, pipeline version, status, and output location
for idempotency. CloudWatch receives structured logs, metrics, dashboards, and
alarms. Secrets Manager stores external-provider credentials; task roles grant only
the S3, SQS, DynamoDB, model, and logging permissions each worker requires.

## Cost

Fargate avoids idle server cost and scales to zero when the queue is empty. S3, SQS,
and DynamoDB remain inexpensive at assignment-scale volume. Model inference will be
the largest variable cost, so record tokens and estimated cost per episode, enforce
prompt and response limits, deduplicate jobs by transcript hash, and cache successful
retrieval and inference stages. Use a lower-cost model for routine summarization and
reserve stronger models for ambiguous claim extraction. At sustained high volume,
compare Fargate with ECS on EC2 and on-demand inference with provisioned throughput
using measured utilization.

## Scalability

Scale stateless Fargate workers from SQS queue depth and oldest-message age. Set a
maximum task count based on model-provider quotas and downstream capacity. SQS
absorbs traffic spikes, while per-episode jobs allow horizontal scaling without
cross-episode state. If summarization and verification develop different latency or
resource profiles, separate them into independently scaled queues and workers while
storing intermediate results in S3 or DynamoDB.

## Fault tolerance

Set the SQS visibility timeout above normal processing time and extend it for healthy
long-running jobs. Use bounded exponential backoff with jitter for throttling and
transient provider errors. After a small retry limit, send failed jobs to a dead-letter
queue for reviewed replay.

Make output keys deterministic and use DynamoDB conditional writes so retries cannot
publish duplicate results. Checkpoint successful expensive stages so a retry does not
repeat completed inference. Distinguish retryable transport failures from permanent
input/schema failures. Alarm on dead-letter depth, oldest-message age, error rate,
latency, provider throttling, and missing outputs. Encrypt data with KMS, avoid putting
transcript text in queue messages, redact sensitive log fields, and apply explicit S3
and CloudWatch retention policies.
