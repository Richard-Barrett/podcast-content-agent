# AWS Deployment Strategy

## Architecture

The production version of the podcast agent would run as an asynchronous, containerized workload on AWS. Podcast transcripts would be uploaded to Amazon S3, which would publish an event to Amazon EventBridge or directly to Amazon SQS. SQS would act as the durable work queue between ingestion and processing.

The agent container would run on Amazon ECS using AWS Fargate. Each task would process one podcast episode: parse the transcript, generate the summary and editorial notes, extract factual claims, retrieve supporting evidence, perform verification, and write JSON/Markdown results back to S3.

For model inference, the application would use Amazon Bedrock rather than operating local Ollama infrastructure in production. The existing provider abstraction would allow Bedrock to be added without changing the core orchestration workflow. A production knowledge base could be stored in Amazon OpenSearch, S3, or another retrieval service depending on data volume and search requirements.

Application logs, latency metrics, error counts, and processing metrics would be sent to Amazon CloudWatch.

## Scalability

Podcast episodes are independent processing units, making the workload naturally parallel. ECS services or Fargate tasks could autoscale based on SQS queue depth, message age, and average processing latency.

SQS provides buffering during traffic spikes so ingestion does not depend on immediate worker availability. Scaling limits should also account for Bedrock model quotas and downstream retrieval capacity rather than increasing workers without bound.

For larger transcripts, preprocessing and chunking could reduce prompt size and allow summarization or claim extraction stages to run independently.

## Fault Tolerance

SQS would provide durable message delivery and retry behavior. Failed processing attempts would use exponential backoff and eventually move to a dead-letter queue for inspection.

Each episode would have an idempotency key based on its episode ID or transcript hash so retries do not produce duplicate processing or unnecessary model charges.

Intermediate processing state could be persisted so a failure during fact-checking does not require repeating successful summarization work. External model and retrieval calls would use timeouts, bounded retries, and structured error logging.

S3 versioning and durable output storage would protect generated artifacts from accidental overwrite or loss.

## Cost

The primary variable cost is model inference. Costs would be controlled through model selection, prompt-size limits, transcript chunking, caching, and avoiding duplicate processing.

Fargate is appropriate because workers only consume compute while jobs are running and does not require maintaining EC2 instances. S3 and SQS are relatively inexpensive for this workload and scale with usage.

CloudWatch metrics would track token usage, processing latency, failures, and estimated cost per episode. This allows the agency to evaluate quality-versus-cost tradeoffs and route simpler workloads to cheaper models while reserving more capable models for difficult analysis or verification tasks.
