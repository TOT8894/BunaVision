# BunaVision

## AI-Powered Coffee Quality Pre-Assessment

**Document version:** 1.0
**Status:** Initial specification — pending technical validation
**Project type:** AI + Cloud Engineering Hackathon
**Application platform:** Web
**Primary deployment target:** AWS
**Team size:** 4 members
**Primary market:** Ethiopian coffee producers, washing stations, cooperatives, and exporters

---

# 1. Executive Summary

BunaVision is a web-based application that uses computer vision to help users identify and count visible defects in green coffee bean samples and generate preliminary quality assessment reports.

Green coffee quality assessment often involves manual inspection and specialized expertise. Producers and washing stations may not always have convenient access to experienced graders, making it difficult to identify potential quality issues early.

BunaVision aims to make preliminary visual assessment more accessible by allowing users to upload a standardized photograph of a green coffee bean sample. A computer-vision model analyzes the image, identifies supported defect categories, and produces a report containing detected defects, counts, confidence scores, and visual annotations where supported.

AWS cloud services provide secure image storage, backend processing, result persistence, and application hosting.

The system is intended to support preliminary screening, not replace official coffee grading, physical examination, laboratory testing, or certified quality assessment.

## 1.1 Core workflow

User captures sample → uploads image → backend validates image → AI analyzes beans → system processes predictions → results are stored → user views the assessment report.

## 1.2 Value proposition

BunaVision helps coffee-sector users identify potential visible defects earlier, review sample images with AI-assisted annotations, and maintain records of preliminary assessments.

## 1.3 Key differentiator

The project combines computer vision with cloud engineering to deliver a practical, end-to-end workflow for an Ethiopian agricultural use case rather than presenting AI as a standalone chatbot.

---

# 2. Problem Definition

## 2.1 Problem statement

Green coffee quality assessment can require manual inspection, time, and access to experienced graders. Some producers, washing stations, and cooperatives may have limited access to these resources, making early identification and consistent recording of visible defects challenging.

When potential defects are not identified early, producers may miss opportunities to investigate processing problems, improve sample preparation, or prepare for formal grading.

An accessible, image-based preliminary screening tool could help users inspect samples more efficiently before seeking official assessment.

## 2.2 Who experiences the problem?

* Smallholder coffee producers and farmer groups.
* Coffee washing stations.
* Coffee cooperatives.
* Coffee exporters.
* Quality-control staff and sample preparation teams.

## 2.3 Current challenges

1. Manual inspection takes time and depends on human expertise.
2. Access to experienced graders may be limited in some locations.
3. Visual defect counts can vary between assessors.
4. Preliminary inspection results may not be recorded consistently.
5. Producers may have difficulty reviewing sample quality before formal grading.

These are the problems the project intends to address. Their prevalence and severity should be validated through conversations with potential users rather than assumed to be uniform across Ethiopia.

## 2.4 Proposed solution

BunaVision provides an AI-assisted preliminary assessment workflow:

1. The user uploads an image of a green coffee bean sample.
2. The system checks whether the image meets basic requirements.
3. A computer-vision model detects beans or visible defects within its supported classes.
4. The backend converts predictions into structured results.
5. The system presents detected defects, counts, confidence information, and an annotated image.
6. The user can review and save the assessment report.

## 2.5 Project hypothesis

If users can obtain an accessible, repeatable preliminary visual assessment of green coffee samples, they may be able to identify potential defects earlier and organize sample quality-control activities more effectively.

The hackathon prototype will demonstrate the technical workflow and evaluate model performance. It will not claim to prove commercial benefits without user testing.

---

# 3. Goals, Objectives, and Success Criteria

## 3.1 Primary objectives

* Build a functional web application for green coffee sample image analysis.
* Integrate an existing computer-vision model or pretrained model suitable for the selected task.
* Identify and count supported visible defect categories.
* Display AI results in an understandable report.
* Use AWS services for cloud processing, storage, and deployment.
* Demonstrate a complete upload-to-report workflow.
* Evaluate model predictions against labeled test images.

## 3.2 Secondary objectives

* Save and retrieve previous assessments.
* Provide visual annotations that help users understand the model's predictions.
* Record assessment timestamps and model versions.
* Prepare an architecture that can support later model improvements.

## 3.3 Hackathon acceptance criteria

The prototype is considered demonstrable when:

* A user can open the deployed web application.
* A user can upload an accepted image format.
* The backend validates the uploaded file.
* The AI pipeline returns results for supported image inputs.
* The frontend displays defect predictions and counts where supported.
* An annotated image is shown if the chosen model supports localization.
* The assessment can be saved and retrieved.
* Invalid files and processing failures produce understandable messages.
* The team can demonstrate at least one known example and explain the model's limitations.
* AWS services are visibly involved in the actual application workflow.

Numerical accuracy targets, processing-time targets, and cost limits remain to be established after selecting the model and testing the deployment environment.

---

# 4. Scope and Boundaries

## 4.1 Minimum viable product (MVP)

The MVP includes:

1. A landing page explaining BunaVision.
2. An image upload interface.
3. Image format, size, and basic quality validation.
4. AI-based analysis of supported defects.
5. A results dashboard.
6. Defect counts and confidence scores.
7. Annotated image display, if supported by the model.
8. A saved assessment record.
9. A simple assessment history page.
10. AWS-hosted application and backend components.
11. Error handling and basic operational logging.

Authentication is a design decision to finalize. If assessment history is private to each user, authentication and ownership checks must be implemented. If the hackathon demo is intentionally public or single-user, private data must not be exposed.

## 4.2 Out of scope for the initial version

* Official Ethiopian coffee grading or certification.
* Automatic determination of a legally or commercially binding coffee grade.
* Guaranteed prediction of cup quality, flavor, aroma, or export price from an image.
* Moisture, density, odor, or laboratory measurements.
* Fully automated grading against all national or international standards.
* Mobile-native applications.
* Marketplace, payment, and logistics management.
* Guaranteed detection of internal or hidden defects.
* A custom foundation model trained from scratch.
* Multi-tenant enterprise administration unless time permits.

## 4.3 Scope-control principle

A reliable, working image-to-report workflow is more valuable for the hackathon than a large collection of unfinished features.

---

# 5. Target Users and User Stories

## 5.1 Primary user: Coffee producer or washing-station operator

**Goal:** Obtain a preliminary indication of visible defects in a sample.

User stories:

* As a user, I want to upload a coffee sample image so that I can request an assessment.
* As a user, I want to see the detected defects so that I can investigate potential quality issues.
* As a user, I want to see counts and confidence information so that I can interpret the predictions.
* As a user, I want to view the original and annotated images so that I can understand where defects were detected.
* As a user, I want to access previous assessments so that I can review my records.

## 5.2 Secondary user: Quality-control staff

**Goal:** Review preliminary inspection results and maintain sample records.

User stories:

* As a quality-control staff member, I want structured results so that I can review samples consistently.
* As a quality-control staff member, I want to know which model generated the report so that I can trace the assessment.
* As a quality-control staff member, I want to see uncertain predictions so that I can prioritize manual review.

## 5.3 Administrative or technical user

**Goal:** Maintain a reliable application.

User stories:

* As an administrator, I want processing failures recorded so that I can troubleshoot them.
* As a technical operator, I want model versions recorded so that changes in predictions can be investigated.
* As a system operator, I want upload and inference limits so that the application cannot be easily overloaded.

Administrative features are secondary to the initial user workflow.

---

# 6. Functional Requirements

| ID    | Requirement                                                                   | Priority    |
| ----- | ----------------------------------------------------------------------------- | ----------- |
| FR-01 | Display project information and instructions                                  | Must        |
| FR-02 | Allow users to select or upload an image                                      | Must        |
| FR-03 | Validate file type and file size                                              | Must        |
| FR-04 | Reject unreadable or unsupported images                                       | Must        |
| FR-05 | Send valid images to the inference pipeline                                   | Must        |
| FR-06 | Detect supported defects using the selected model                             | Must        |
| FR-07 | Return structured predictions to the backend                                  | Must        |
| FR-08 | Calculate counts from model predictions where supported                       | Must        |
| FR-09 | Display results and confidence information                                    | Must        |
| FR-10 | Display annotated images if localization is supported                         | Should      |
| FR-11 | Save assessment metadata and results                                          | Must        |
| FR-12 | Show previous assessment records                                              | Should      |
| FR-13 | Handle timeouts and processing failures                                       | Must        |
| FR-14 | Record model version and assessment timestamp                                 | Should      |
| FR-15 | Support authentication and record ownership if private user accounts are used | Conditional |
| FR-16 | Export or download reports                                                    | Could       |
| FR-17 | Compare multiple samples over time                                            | Could       |

**Priority definitions**

* Must: required for the core demonstration.
* Should: important, but may be deferred if time is limited.
* Could: optional enhancement.

# 7. Non-Functional Requirements

## 7.1 Performance

* Image processing should return results within a practical waiting period for the selected model and hosting configuration.
* Large images should be resized or processed according to the model's documented input requirements.
* The UI should display loading and processing states.
* Long-running inference must not block unrelated API requests indefinitely.

A numerical response-time objective will be defined after benchmarking.

## 7.2 Reliability

* Failed uploads must not create misleading successful reports.
* Partial processing failures must be recorded.
* Retrying a request must not unintentionally create duplicate assessment records.
* Missing or invalid model outputs must be handled safely.

## 7.3 Security

* Use HTTPS in the deployed environment.
* Validate all uploaded files on the backend.
* Restrict storage access to authorized application components.
* Keep AWS credentials and secrets out of source code.
* Enforce ownership checks on private assessment records.
* Limit request size and upload frequency.
* Avoid storing unnecessary personal information.

## 7.4 Usability

* The interface should be simple and responsive.
* Upload instructions should explain the required sample arrangement and lighting.
* Results should distinguish model predictions from verified findings.
* Error messages should explain what the user can do next.

## 7.5 Maintainability

* Separate frontend, backend, AI inference, and storage responsibilities.
* Use environment variables for deployment-specific configuration.
* Version the model and keep the inference interface stable.
* Document API contracts and deployment steps.

---

# 8. System Architecture

## 8.1 Proposed architecture

The initial architecture uses a React web frontend, a Python backend, an existing computer-vision model, Amazon S3 for image storage, and a persistent database for assessment records.

The exact AWS compute and database services will be finalized after the model has been selected and tested.

```text
                 USER
                   |
                   v
          React + TypeScript UI
                   |
             HTTPS / REST API
                   |
                   v
         Python Backend (FastAPI)
                   |
         +---------+----------+
         |         |          |
         v         v          v
    Validation  AI Inference  Metadata
         |         |          |
         |         v          v
         |     CV Model     Database
         |         |
         v         v
      Amazon S3  Structured Predictions
                   |
                   v
            Report Generation
                   |
                   v
             Results UI
```

This is a logical architecture, not a final AWS deployment diagram. The actual deployment may use a containerized service, serverless functions, or another appropriate compute option.

## 8.2 Main components

### A. Frontend

Responsibilities:

* Display project information.
* Accept sample images.
* Show upload and processing status.
* Present predictions and annotated images.
* Display assessment history.
* Provide error and retry states.

Proposed technology:

* React
* TypeScript
* Tailwind CSS
* A charting or visualization library only if useful

### B. Backend API

Responsibilities:

* Validate requests and uploads.
* Coordinate image storage and inference.
* Normalize model predictions.
* Calculate supported counts and summary metrics.
* Persist assessment records.
* Return structured results to the frontend.

Proposed technology:

* Python
* FastAPI
* Pydantic for request and response validation

### C. Computer-vision inference

Responsibilities:

* Load the selected model.
* Preprocess input images.
* Perform inference.
* Convert model output into a consistent format.
* Generate annotated images if the model supports localization.
* Report inference errors and timing.

The model should be wrapped behind a stable inference interface so that it can be replaced without redesigning the frontend.

### D. Object storage

Amazon S3 is the proposed storage service for uploaded and annotated images.

Responsibilities:

* Store original images when retention is enabled.
* Store annotated images when generated.
* Support controlled access through backend authorization or presigned URLs.
* Apply appropriate retention and lifecycle policies.

### E. Database

The database stores structured metadata rather than large image files.

Potential choices:

* Amazon DynamoDB for a simple key-based assessment history.
* Amazon RDS PostgreSQL if relational queries and structured reporting become important.

**Decision status:** Not finalized. Choose one database for the MVP; do not introduce both without a concrete need.

---

# 9. AI and Computer-Vision Design

## 9.1 Model strategy

BunaVision will start with an existing model or pretrained model rather than training a large model from scratch.

However, a pretrained model is not automatically suitable for coffee defects. The model must support the actual task and relevant defect categories.

The team must establish:

1. What the model predicts: whole-image classes, individual bean detections, or defect regions.
2. Which defect classes it supports.
3. Whether its training data contains green coffee beans and representative defects.
4. Whether its license permits the intended use.
5. Whether inference can run on the selected AWS environment.
6. How its predictions compare with labeled test images.

## 9.2 Dataset strategy

The team should investigate available labeled green coffee bean datasets, including the CBD_Coffee Bean Dataset previously identified during project brainstorming.

Its availability, license, labeling quality, defect taxonomy, image conditions, and compatibility with the selected model must be verified before relying on it.

Dataset plan:

* Obtain the dataset and record its source and license.
* Inspect the number of images and examples per class.
* Review labels and confirm what each class means.
* Identify duplicate images and labeling problems.
* Split data into training, validation, and test sets when training or fine-tuning is needed.
* Keep test images separate from model tuning.
* Include realistic lighting, backgrounds, bean arrangements, and image quality variations where possible.

If the dataset is too small or lacks reliable labels, reduce the supported defect categories rather than claim broad detection coverage.

## 9.3 Model selection options

### Option A: Existing object-detection model

Use this if the available model can localize individual beans or defects and provide bounding boxes.

Advantages:

* Supports annotated images.
* Can provide per-detection confidence scores.
* May support counting visible beans or defects.

Limitations:

* Requires compatible labels and output interpretation.
* Overlapping beans and small defects may be difficult to detect.

### Option B: Image-classification model

Use this if the model classifies an entire sample image or crop into predefined categories.

Advantages:

* Potentially simpler to deploy.
* May work with smaller, curated datasets.

Limitations:

* Does not automatically localize defects.
* Cannot reliably provide individual defect counts from a whole-image classification alone.

### Option C: Segmentation model

Use this if pixel-level defect masks are available and localization at that level is necessary.

Advantages:

* Can estimate defect regions.
* May provide more detailed visual evidence.

Limitations:

* Requires suitable segmentation labels and additional implementation effort.

**Recommendation:** Select the simplest model that can reliably demonstrate the desired task. Do not promise defect localization and counts until the selected model's outputs support them.

## 9.4 Image preprocessing

The inference pipeline may perform:

1. Image decoding.
2. Format and dimension checks.
3. Orientation correction.
4. Resizing and normalization.
5. Model-specific preprocessing.
6. Inference.
7. Confidence thresholding and non-maximum suppression if appropriate for the model.
8. Prediction normalization.
9. Annotation generation.
10. Result serialization.

Preprocessing parameters must match the model's training and inference requirements.

## 9.5 Counting rules

The report must define what is being counted.

Possible measures include:

* Number of detected beans.
* Number of beans predicted to belong to each defect class.
* Number of detected defect regions.
* Number of beans containing one or more detected defects.

These are not interchangeable. A single bean can contain multiple defect regions, and some defect classes may not be visually distinguishable in a photograph.

The report must not treat defect-region counts as bean counts.

## 9.6 Confidence scores

Confidence scores represent the model's estimated confidence in its predictions, not the probability that a sample meets official grading requirements.

The interface may display confidence values per prediction, with explanatory labels such as "model confidence." Thresholds should be selected through validation, not chosen solely to make the demo appear accurate.

Low-confidence results may be flagged for manual review.

## 9.7 Evaluation metrics

For object detection:

* Precision.
* Recall.
* Mean Average Precision (mAP), with the selected IoU threshold specified.
* Per-class performance.
* Inference latency.

For classification:

* Precision, recall, and F1-score per class.
* Confusion matrix.
* Accuracy, where appropriate.

For counting:

* Mean Absolute Error between predicted and reference counts.
* Count error by defect class.

The evaluation must use held-out labeled examples. Results should not be invented or presented as measured until testing has been completed.

## 9.8 Model limitations

The model may struggle with:

* Poor lighting or shadows.
* Blurry images.
* Overlapping beans.
* Very small or subtle defects.
* Defects hidden from the camera.
* Backgrounds unlike the training dataset.
* Defect categories absent from training data.

BunaVision should communicate these limitations and recommend manual verification when necessary.

---

# 10. Image Capture and Upload Requirements

Consistent input images are essential for meaningful model evaluation.

## 10.1 User instructions

The upload interface should ask users to:

* Spread beans in a single layer where possible.
* Use a plain, contrasting background.
* Provide bright, even lighting.
* Avoid harsh shadows and reflections.
* Keep the camera focused.
* Ensure beans are sufficiently separated if individual detection is required.
* Include the complete sample within the image.

These instructions are preliminary and should be adapted to the chosen model.

## 10.2 Supported formats

Proposed initial formats:

* JPEG/JPG
* PNG

The backend must validate actual file content, not just the filename or MIME type.

The maximum file size and image dimensions remain configurable until tested.

## 10.3 Rejection cases

The system should reject or request a new image when:

* The file is not a supported image.
* The file cannot be decoded.
* The image exceeds configured resource limits.
* The image is too small for the model's requirements.
* The image is visibly unsuitable according to implemented quality checks.

Automated blur, lighting, and sample-presence checks are optional enhancements, not assumed existing capabilities.

---

# 11. User Interface Specification

## 11.1 Page structure

### Page 1: Home

Purpose: Explain the product and direct the user to sample assessment.

Components:

* BunaVision logo/name.
* Short explanation.
* Primary "Assess a Sample" action.
* Three-step workflow.
* Disclaimer that the result is preliminary.

### Page 2: Upload Sample

Components:

* Image upload area.
* Capture instructions.
* Selected-image preview.
* File validation messages.
* Analyze button.
* Loading state.

### Page 3: Assessment Results

Components:

* Assessment ID and timestamp.
* Overall processing status.
* Original image.
* Annotated image, if supported.
* Detected defect classes.
* Counts and confidence information.
* Important limitations.
* Save or return actions.

Do not show an overall grade unless a validated and documented grading method has been implemented.

### Page 4: Assessment History

Components:

* Assessment date.
* Assessment ID.
* Processing status.
* Summary of detected categories.
* Link to open the report.

If private user accounts are enabled, history must be scoped to the authenticated user.

### Page 5: Assessment Details

Components:

* Original image.
* Annotated image.
* Full model results.
* Model version.
* Assessment timestamp.
* Warnings and processing status.

## 11.2 UI states

The frontend should support:

* Idle.
* Image selected.
* Uploading.
* Processing.
* Success.
* Validation error.
* Inference failure.
* Network failure.
* Loading history.
* Empty history.

The application must never show fabricated or stale results as if they belong to the current image.

---

# 12. API Specification

The following API is a proposed contract. Endpoint names and response fields may be adjusted during implementation, but the team should keep the frontend and backend consistent.

Base path: `/api/v1`

## 12.1 Create assessment

`POST /api/v1/assessments`

Purpose: Submit an image for analysis.

Initial implementation may use multipart form data:

* `image`: image file.
* Optional metadata: sample reference or user-provided notes.

Successful response example:

```json
{
  "assessment_id": "asmt_12345",
  "status": "completed",
  "model_version": "model-v1",
  "created_at": "2026-10-09T08:00:00Z",
  "summary": {
    "detected_classes": 2,
    "detection_count": 7
  },
  "predictions": [
    {
      "class_name": "example_defect",
      "confidence": 0.91,
      "count": 4
    }
  ],
  "annotated_image_url": null,
  "limitations": [
    "Preliminary AI assessment; verify results manually."
  ]
}
```

**Important:** The class name, confidence, count, and sample values above are illustrative placeholders, not actual model outputs. The real response must contain only supported predictions.

For a longer-running inference process, the API can return `202 Accepted` with a processing status and assessment ID. The frontend can then poll the assessment endpoint.

## 12.2 Get assessment

`GET /api/v1/assessments/{assessment_id}`

Returns the status, results, and permitted image references for a specific assessment.

Possible statuses:

* `pending`
* `processing`
* `completed`
* `failed`

The initial synchronous implementation may use only `completed` or `failed` for accepted requests.

## 12.3 List assessments

`GET /api/v1/assessments`

Returns assessment history with pagination.

If authentication is enabled, only assessments the current user is authorized to view may be returned.

## 12.4 Health check

`GET /health`

Returns the service health status. This endpoint should not expose credentials, internal configuration, or sensitive infrastructure details.

## 12.5 Error response

Example:

```json
{
  "error": {
    "code": "INVALID_IMAGE",
    "message": "The uploaded file is not a supported image."
  }
}
```

Potential error codes:

* `INVALID_IMAGE`
* `IMAGE_TOO_LARGE`
* `UNSUPPORTED_FORMAT`
* `INFERENCE_FAILED`
* `ASSESSMENT_NOT_FOUND`
* `UNAUTHORIZED`
* `RATE_LIMITED`
* `INTERNAL_ERROR`

---

# 13. Database Design

## 13.1 Assessment entity

Suggested fields:

| Field               | Type                                 | Purpose                      |
| ------------------- | ------------------------------------ | ---------------------------- |
| assessment_id       | String/UUID                          | Unique assessment identifier |
| user_id             | String/UUID, nullable if public demo | Record owner                 |
| original_image_key  | String                               | S3 object key                |
| annotated_image_key | String, nullable                     | Annotated image object key   |
| status              | String                               | Processing state             |
| model_version       | String                               | Model used                   |
| predictions         | JSON                                 | Structured prediction output |
| summary             | JSON                                 | Counts and summary metrics   |
| created_at          | Timestamp                            | Creation time                |
| completed_at        | Timestamp, nullable                  | Completion time              |
| error_code          | String, nullable                     | Failure classification       |

## 13.2 Design rules

* Store images in object storage, not as database blobs.
* Store S3 object keys rather than public URLs.
* Generate access URLs only when required and authorized.
* Store predictions in a consistent schema.
* Keep the model version with each result.
* Avoid storing credentials or unnecessary personal data.
* Add an index for user and creation date if history queries require it.

## 13.3 Database decision

For a small hackathon MVP, choose one persistence service:

**Option A — DynamoDB:** suitable for straightforward assessment records keyed by assessment ID, with a user/date access pattern if designed appropriately.

**Option B — PostgreSQL:** suitable for relational records, filtering, and future analytical queries.

The choice should depend on the team's familiarity, available AWS resources, and implementation time. A second database is not required for the MVP.

---

# 14. AWS Cloud Architecture

## 14.1 Proposed services

| Service                                        | Responsibility                                              | Status                                      |
| ---------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------- |
| Amazon S3                                      | Store uploaded and annotated images                         | Proposed core                               |
| AWS compute service                            | Run backend and inference                                   | Decision pending                            |
| Amazon API Gateway                             | API entry point if using a serverless backend               | Optional                                    |
| AWS Lambda                                     | Run short backend tasks if model/runtime constraints permit | Optional                                    |
| Amazon DynamoDB                                | Persist assessment records                                  | Alternative database                        |
| Amazon RDS PostgreSQL                          | Persist relational assessment records                       | Alternative database                        |
| Amazon CloudWatch                              | Logs, metrics, and alarms                                   | Recommended                                 |
| AWS IAM                                        | Service permissions                                         | Required                                    |
| AWS KMS                                        | Encryption key management where required                    | Recommended                                 |
| Amazon CloudFront                              | Deliver static frontend assets                              | Optional                                    |
| AWS Amplify Hosting or S3-based static hosting | Host frontend                                               | Choose one                                  |
| AWS Secrets Manager                            | Store sensitive configuration when needed                   | Recommended for production-like deployments |

Not every service in this table needs to be deployed. Select the smallest architecture that meets the model's runtime and resource requirements.

## 14.2 Compute decision

The model's size and dependencies determine the best inference environment.

### Option A: Containerized backend

Use a containerized FastAPI service on a suitable managed compute environment.

Advantages:

* Familiar Python runtime.
* Greater control over system libraries and dependencies.
* Often easier for models that require larger packages or more memory.

Trade-offs:

* Requires container image management and deployment configuration.
* Can incur ongoing compute costs.

### Option B: AWS Lambda

Use Lambda if the model's dependencies, memory requirements, execution duration, and cold-start behavior are compatible with the configured limits.

Advantages:

* Event-driven execution.
* No continuously running server required.
* Good fit for short processing tasks.

Trade-offs:

* Large model loading and inference may be inefficient.
* Runtime and resource limits must be verified.
* Cold starts can affect demo latency.

### Option C: Managed ML inference endpoint

Consider a managed inference endpoint if the model needs dedicated ML serving resources.

Advantages:

* Model-serving-oriented infrastructure.
* Potentially more predictable inference behavior.

Trade-offs:

* More configuration and potentially higher cost.
* May be excessive for a short hackathon.

**Recommendation:** Benchmark the selected model locally first. Then choose the least complex AWS compute environment that can run it reliably.

## 14.3 Data flow

1. The browser submits an image through the application API.
2. The backend validates the image and request.
3. The backend stores the original image in S3 if retention is enabled.
4. The backend invokes the inference function or service.
5. The model returns structured predictions.
6. The backend validates and normalizes the predictions.
7. The backend generates an annotated image if supported.
8. Images and assessment metadata are persisted.
9. The API returns the assessment result or a processing status.
10. The frontend displays the report.

For a synchronous MVP, steps 4–9 may happen in one request. For slower inference, use an asynchronous workflow with a job status and retry strategy.

## 14.4 Security controls

* Use least-privilege IAM roles.
* Block public access to private S3 buckets.
* Use HTTPS.
* Use short-lived presigned URLs when direct object access is necessary.
* Validate file content and dimensions.
* Configure request size limits.
* Do not commit AWS keys to Git.
* Configure CORS for the actual frontend origin.
* Log errors without logging secrets or image contents unnecessarily.
* Define a retention policy for uploaded images.

## 14.5 Cost management

Although the AWS budget is flexible, the system should not use expensive services without a clear need.

Before deployment:

* Estimate expected image uploads and inference frequency.
* Check compute uptime and pricing.
* Configure AWS Budgets alerts.
* Shut down unused billable resources.
* Avoid leaving a GPU-backed endpoint running unnecessarily.
* Apply S3 lifecycle rules if image retention is required.
* Monitor logs and storage growth.

Actual cost estimates should be calculated using the selected AWS region, service configuration, expected traffic, and current pricing.

---

# 15. Security, Privacy, and Responsible AI

## 15.1 Upload security

The backend must not trust the client to determine whether a file is safe. It should check content, size, dimensions, and supported encoding before processing.

## 15.2 Data privacy

The initial application should collect only the information needed to create and retrieve assessments.

If sample records contain customer or business information, avoid including that information in filenames, logs, or public URLs.

## 15.3 AI transparency

Every report should explain that:

* Results are generated by an AI model.
* Confidence values describe model predictions, not guaranteed correctness.
* Only supported visible defect classes are assessed.
* Hidden defects cannot be reliably determined from a photograph.
* Results are preliminary and require appropriate human verification.

## 15.4 Fair and reliable assessment

Evaluate performance across the available image conditions and relevant defect classes. A model that performs well on one dataset may perform poorly on real-world images from different cameras, backgrounds, lighting, or coffee varieties.

The team should report limitations rather than claim universal performance.

## 15.5 Human oversight

BunaVision is a decision-support tool. It should not independently certify coffee quality, determine export eligibility, or guarantee commercial outcomes.

---

# 16. Testing and Quality Assurance

## 16.1 Frontend tests

* Upload a valid image.
* Reject an unsupported file.
* Display upload progress.
* Display processing status.
* Render predictions correctly.
* Display an appropriate failure state.
* Open an existing assessment.
* Verify responsive layout on common screen sizes.

## 16.2 Backend tests

* Valid image upload.
* Invalid image content.
* Oversized upload.
* Missing file.
* Malformed request.
* Model inference exception.
* Database write failure.
* Missing assessment ID.
* Unauthorized access, if authentication is enabled.
* Repeated request handling.

## 16.3 AI tests

* Evaluate on held-out labeled examples.
* Measure per-class precision and recall.
* Check false positives and false negatives.
* Compare predicted counts against reference counts.
* Review difficult and ambiguous images.
* Confirm that confidence values are interpreted correctly.
* Test images with poor lighting and overlapping beans.
* Confirm unsupported classes are not reported as confidently detected classes.

## 16.4 Integration tests

Verify the complete flow:

Image upload → backend validation → S3 storage → inference → result normalization → database persistence → report retrieval.

Test the flow both on valid images and on images that cause failures.

## 16.5 Demo acceptance test

The team should prepare a small set of known test images with reference labels and expected behavior.

The final demonstration should use real model outputs. If an example is simulated, it must be clearly labeled as simulated rather than presented as a successful inference.

---

# 17. Team Structure and Responsibilities

Four members should have clearly defined areas of ownership, while agreeing on API contracts and integration points.

## Member 1 — Frontend Development

Responsibilities:

* Build the React application.
* Implement upload and preview.
* Build loading and error states.
* Render assessment results.
* Build assessment history.
* Integrate the backend API.

Deliverables:

* Responsive UI.
* API-connected upload flow.
* Results and history pages.

## Member 2 — AI and Computer Vision

Responsibilities:

* Find and validate the dataset.
* Inspect existing models.
* Verify licenses and model compatibility.
* Implement preprocessing and inference.
* Evaluate predictions.
* Define supported defect categories.
* Produce annotation and evaluation outputs if supported.

Deliverables:

* Working inference module.
* Model documentation.
* Test results and known limitations.

## Member 3 — Backend and Database

Responsibilities:

* Build FastAPI endpoints.
* Validate image uploads.
* Integrate inference.
* Normalize prediction outputs.
* Persist assessment records.
* Implement error handling and access control.

Deliverables:

* API implementation.
* Database schema.
* API documentation.
* Backend tests.

## Member 4 — AWS, Integration, and Quality Assurance

Responsibilities:

* Set up AWS resources.
* Configure storage and IAM permissions.
* Deploy frontend and backend.
* Configure environment variables and secrets.
* Set up monitoring.
* Test end-to-end behavior.
* Track integration issues and deployment readiness.

Deliverables:

* Working AWS deployment.
* Deployment instructions.
* Integration test checklist.
* Operational and cost-monitoring configuration.

## Shared responsibilities

All members should:

* Review the architecture.
* Agree on API schemas.
* Use Git branches and pull requests.
* Test the integrated system.
* Prepare the final presentation.
* Understand the full user workflow.

Role allocation can be adjusted according to actual experience. Each member should have a primary owner area and a secondary support responsibility.

---

# 18. Development Workflow

## 18.1 Repository structure

Proposed monorepo:

```text
bunavision/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   ├── public/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── ai/
│   ├── model/
│   ├── preprocessing/
│   ├── inference.py
│   ├── evaluation/
│   └── README.md
├── infrastructure/
│   ├── README.md
│   └── deployment/
├── docs/
│   ├── PROJECT_SPECIFICATION.md
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── AI_MODEL.md
│   ├── TESTING.md
│   └── DEPLOYMENT.md
├── .env.example
├── .gitignore
└── README.md
```

This is a proposed structure, not a requirement to create every file immediately. The AI module may live inside the backend if separating it would add unnecessary complexity.

## 18.2 Git workflow

Suggested branches:

* `main`: stable, demonstrable code.
* `feature/frontend-upload`
* `feature/ai-inference`
* `feature/backend-api`
* `feature/aws-deployment`

Use pull requests for integration and test the main branch regularly.

## 18.3 Integration contract

Before parallel development, agree on:

* Upload endpoint and request format.
* Assessment response schema.
* Prediction class names.
* Meaning of counts and confidence values.
* Image-storage behavior.
* Error response structure.
* Assessment status values.

This prevents frontend, backend, and AI components from making incompatible assumptions.

---

# 19. Implementation Plan and Milestones

The deadline is unknown, so the plan uses milestones rather than fixed calendar dates.

## Milestone 1 — Validate feasibility

Tasks:

* Inspect candidate datasets.
* Verify licensing and label quality.
* Run an existing model on sample images.
* Confirm that its output supports the intended report.
* Decide the initial defect categories.

**Exit condition:** A real image produces inspectable model output.

## Milestone 2 — Build the vertical slice

Tasks:

* Create the basic web interface.
* Implement one upload endpoint.
* Connect the inference module.
* Return a structured result.
* Render the result in the frontend.

**Exit condition:** One end-to-end local assessment works.

## Milestone 3 — Add persistence

Tasks:

* Configure S3.
* Select and configure the database.
* Save assessment metadata.
* Store image references.
* Retrieve previous results.

**Exit condition:** Completed assessments can be retrieved after the original request finishes.

## Milestone 4 — Deploy to AWS

Tasks:

* Choose compatible compute.
* Configure environment variables and IAM.
* Deploy the backend and frontend.
* Configure CORS and HTTPS.
* Verify S3 and database access.
* Test the public deployment.

**Exit condition:** A remote user can complete an assessment.

## Milestone 5 — Test and refine

Tasks:

* Run AI evaluation.
* Test invalid inputs and inference failures.
* Improve loading and error states.
* Verify image annotations.
* Check resource use and AWS costs.

**Exit condition:** The core workflow is repeatable and the known limitations are documented.

## Milestone 6 — Final demonstration

Tasks:

* Select representative test images.
* Prepare the demonstration sequence.
* Prepare architecture and AI evaluation slides.
* Rehearse the presentation.
* Confirm fallback materials in case the network or live inference fails.

**Exit condition:** Every team member understands the project, and the demo can be completed reliably.

---

# 20. Risks and Mitigation

| Risk                                       | Impact      | Mitigation                                                      |
| ------------------------------------------ | ----------- | --------------------------------------------------------------- |
| Dataset lacks relevant labels              | High        | Validate dataset before committing to model choice              |
| Existing model is not suitable             | High        | Run an early inference experiment and change approach if needed |
| Dataset license is unsuitable              | High        | Check the license before use or redistribution                  |
| Detection counts are unreliable            | High        | Evaluate count error and limit claims                           |
| Model is too large for chosen AWS compute  | High        | Benchmark locally and select compatible hosting                 |
| AWS deployment takes too long              | Medium–High | Deploy a minimal vertical slice early                           |
| Integration conflicts                      | Medium–High | Agree on API and schemas before parallel work                   |
| Time is insufficient                       | High        | Prioritize the MVP and defer optional features                  |
| Demo internet is unavailable               | Medium      | Prepare recorded evidence and a local fallback                  |
| AWS costs increase unexpectedly            | Medium      | Set budget alerts and shut down unused resources                |
| Images are inconsistent                    | High        | Provide capture instructions and test real-world inputs         |
| Results are interpreted as official grades | High        | Clearly label reports as preliminary AI assessments             |

---

# 21. Demo and Presentation Plan

## 21.1 Suggested demo sequence

1. Introduce the problem faced by coffee-sector users.
2. Open the BunaVision web application.
3. Explain the sample-image requirements.
4. Upload a representative green coffee bean image.
5. Show image validation and processing.
6. Display actual model predictions and annotations.
7. Explain what the counts and confidence scores mean.
8. Open the saved assessment.
9. Briefly show the AWS architecture and data flow.
10. Present measured model performance and known limitations.

## 21.2 Suggested presentation structure

* Slide 1: Project name and value proposition.
* Slide 2: Problem and target users.
* Slide 3: Proposed solution and user workflow.
* Slide 4: AI approach and dataset.
* Slide 5: AWS architecture.
* Slide 6: Live demo or recorded workflow.
* Slide 7: Evaluation results and limitations.
* Slide 8: Impact, future development, and conclusion.

## 21.3 Demo principles

* Use real inference results.
* Keep the main workflow short.
* Show the system working rather than spending too long on architecture slides.
* Explain the role of each AWS service.
* Present actual measured model metrics.
* Distinguish demonstrated functionality from future plans.

---

# 22. Future Development

After the hackathon, possible extensions include:

* Collecting additional labeled Ethiopian coffee images.
* Fine-tuning a model for locally relevant defect categories.
* Improving counting and localization.
* Adding sample metadata and batch management.
* Supporting repeated assessments and comparisons.
* Developing a mobile-friendly offline capture workflow.
* Adding multilingual interface support.
* Providing more detailed quality-control analytics.
* Validating the system with experienced coffee graders.
* Exploring integration with formal quality-assessment workflows.

These are future possibilities, not MVP commitments.

---

# 23. Assumptions and Open Decisions

The following items must be resolved during development.

| Item                         | Current status                 | Required action                                     |
| ---------------------------- | ------------------------------ | --------------------------------------------------- |
| Web application              | Confirmed                      | Use a responsive web interface                      |
| Team size                    | Confirmed: 4                   | Assign owners and backups                           |
| Existing model approach      | Confirmed                      | Evaluate compatible candidates                      |
| AWS as primary cloud         | Assumed from hackathon context | Confirm the required AWS usage                      |
| Exact dataset                | Undecided                      | Inspect candidate datasets and licenses             |
| Defect taxonomy              | Undecided                      | Match supported classes to available labels         |
| Model architecture           | Undecided                      | Compare classification, detection, and segmentation |
| Fine-tuning                  | Conditional                    | Decide after baseline evaluation                    |
| Frontend framework           | Proposed: React + TypeScript   | Confirm with the team                               |
| Backend framework            | Proposed: FastAPI              | Confirm with the team                               |
| AWS compute                  | Undecided                      | Benchmark the model and choose a compatible service |
| Database                     | Undecided                      | Choose one persistence option                       |
| Authentication               | Undecided                      | Decide whether the MVP needs private user accounts  |
| Maximum upload size          | Undecided                      | Set after testing                                   |
| Accuracy target              | Undecided                      | Establish a measurable target after the baseline    |
| Deadline                     | Unknown                        | Convert milestones into a schedule                  |
| AWS budget                   | Flexible                       | Establish a practical spending limit                |
| Official grading integration | Out of scope                   | Reconsider only after expert validation             |

---

# 24. Definition of Done

BunaVision's hackathon MVP is complete when:

* [ ] The problem and intended users are clearly documented.
* [ ] The chosen model and dataset have been inspected.
* [ ] Dataset and model licenses have been reviewed.
* [ ] The application accepts valid images and rejects invalid inputs.
* [ ] A real model produces structured predictions.
* [ ] Counts and confidence information are interpreted correctly.
* [ ] The results interface displays the supported outputs.
* [ ] Assessments are persisted and retrievable.
* [ ] The application is deployed to AWS.
* [ ] Basic security and access controls are implemented.
* [ ] Core frontend, backend, and inference tests pass.
* [ ] AI evaluation results and limitations are documented.
* [ ] AWS costs and deployed resources are reviewed.
* [ ] The final demo has been rehearsed.
* [ ] All four team members can explain their contributions and the complete system.

---

# 25. Conclusion

BunaVision aims to make preliminary green coffee defect assessment more accessible by combining computer vision with cloud engineering.

Its success depends on three things: selecting a model suitable for the actual defect-detection task, presenting its results honestly, and delivering a reliable end-to-end web application.

For the hackathon, the priority is to demonstrate a working image-to-report workflow, validate it with real test images, and explain clearly how the AI and AWS components work together.

BunaVision is a preliminary screening tool—not an official grading authority. That distinction is essential to building a technically credible and useful system.
