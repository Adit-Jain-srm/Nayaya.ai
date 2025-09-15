# Configure the Google Cloud Provider
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Google Cloud Zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Configure providers
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Local values
locals {
  app_name = "nayaya-ai"
  common_labels = {
    environment = var.environment
    project     = local.app_name
    managed-by  = "terraform"
  }
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "documentai.googleapis.com",
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
    "firestore.googleapis.com",
    "dlp.googleapis.com",
    "translate.googleapis.com",
    "discoveryengine.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudkms.googleapis.com",
    "secretmanager.googleapis.com",
    "vpcaccess.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy        = false
}

# Create KMS key ring and keys for encryption
resource "google_kms_key_ring" "nayaya_keyring" {
  name     = "${local.app_name}-keyring-${var.environment}"
  location = var.region

  depends_on = [google_project_service.required_apis]
}

resource "google_kms_crypto_key" "storage_key" {
  name     = "storage-encryption-key"
  key_ring = google_kms_key_ring.nayaya_keyring.id
  purpose  = "ENCRYPT_DECRYPT"

  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Create Cloud Storage buckets
resource "google_storage_bucket" "documents" {
  name          = "${local.app_name}-documents-${var.environment}-${random_string.bucket_suffix.result}"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_key.id
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = local.common_labels

  depends_on = [google_project_service.required_apis]
}

resource "google_storage_bucket" "processed_documents" {
  name          = "${local.app_name}-processed-${var.environment}-${random_string.bucket_suffix.result}"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_key.id
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }

  labels = local.common_labels

  depends_on = [google_project_service.required_apis]
}

# Random string for bucket naming
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Create Firestore database
resource "google_firestore_database" "nayaya_db" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.required_apis]
}

# Create Document AI processor
resource "google_document_ai_processor" "form_parser" {
  location     = "us"
  display_name = "${local.app_name}-form-parser-${var.environment}"
  type         = "FORM_PARSER_PROCESSOR"

  depends_on = [google_project_service.required_apis]
}

# Create Artifact Registry repository
resource "google_artifact_registry_repository" "nayaya_repo" {
  location      = var.region
  repository_id = "${local.app_name}-repo"
  description   = "Docker repository for Nayaya.ai"
  format        = "DOCKER"

  labels = local.common_labels

  depends_on = [google_project_service.required_apis]
}

# Create VPC Connector for Cloud Run
resource "google_vpc_access_connector" "nayaya_connector" {
  name          = "${local.app_name}-connector-${var.environment}"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = "default"

  depends_on = [google_project_service.required_apis]
}

# Create Cloud Run service for backend
resource "google_cloud_run_v2_service" "backend" {
  name     = "${local.app_name}-backend-${var.environment}"
  location = var.region

  template {
    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.environment == "prod" ? 10 : 3
    }

    vpc_access {
      connector = google_vpc_access_connector.nayaya_connector.id
    }

    containers {
      image = "gcr.io/${var.project_id}/${local.app_name}-backend:latest"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_REGION"
        value = var.region
      }

      env {
        name  = "DOCUMENT_AI_PROCESSOR_ID"
        value = google_document_ai_processor.form_parser.name
      }

      env {
        name  = "CLOUD_STORAGE_BUCKET"
        value = google_storage_bucket.documents.name
      }

      env {
        name  = "CLOUD_STORAGE_BUCKET_PROCESSED"
        value = google_storage_bucket.processed_documents.name
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      # Secret environment variables would be managed via Secret Manager
      # env {
      #   name = "SECRET_KEY"
      #   value_source {
      #     secret_key_ref {
      #       secret  = google_secret_manager_secret.app_secret.secret_id
      #       version = "latest"
      #     }
      #   }
      # }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  labels = local.common_labels

  depends_on = [
    google_project_service.required_apis,
    google_vpc_access_connector.nayaya_connector
  ]
}

# Create Cloud Run service for frontend
resource "google_cloud_run_v2_service" "frontend" {
  name     = "${local.app_name}-frontend-${var.environment}"
  location = var.region

  template {
    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.environment == "prod" ? 5 : 2
    }

    containers {
      image = "gcr.io/${var.project_id}/${local.app_name}-frontend:latest"

      ports {
        container_port = 3000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
      }

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }

      env {
        name  = "NODE_ENV"
        value = var.environment == "prod" ? "production" : "development"
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  labels = local.common_labels

  depends_on = [google_project_service.required_apis]
}

# IAM policy for Cloud Run services to be publicly accessible
resource "google_cloud_run_service_iam_policy" "backend_public" {
  location = google_cloud_run_v2_service.backend.location
  service  = google_cloud_run_v2_service.backend.name

  policy_data = data.google_iam_policy.public_access.policy_data
}

resource "google_cloud_run_service_iam_policy" "frontend_public" {
  location = google_cloud_run_v2_service.frontend.location
  service  = google_cloud_run_v2_service.frontend.name

  policy_data = data.google_iam_policy.public_access.policy_data
}

data "google_iam_policy" "public_access" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

# Create service account for the application
resource "google_service_account" "nayaya_service_account" {
  account_id   = "${local.app_name}-sa-${var.environment}"
  display_name = "Nayaya.ai Service Account"
  description  = "Service account for Nayaya.ai application"
}

# Grant necessary permissions to service account
resource "google_project_iam_member" "service_account_permissions" {
  for_each = toset([
    "roles/documentai.apiUser",
    "roles/aiplatform.user",
    "roles/storage.objectAdmin",
    "roles/datastore.user",
    "roles/dlp.user",
    "roles/cloudtranslate.user",
    "roles/discoveryengine.editor"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.nayaya_service_account.email}"
}

# Create BigQuery dataset for analytics
resource "google_bigquery_dataset" "nayaya_analytics" {
  dataset_id  = "${replace(local.app_name, "-", "_")}_analytics_${var.environment}"
  description = "Analytics dataset for Nayaya.ai"
  location    = var.region

  labels = local.common_labels

  depends_on = [google_project_service.required_apis]
}

# Outputs
output "project_id" {
  description = "Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud Region"
  value       = var.region
}

output "backend_url" {
  description = "Backend Cloud Run URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "Frontend Cloud Run URL"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "document_processor_id" {
  description = "Document AI Processor ID"
  value       = google_document_ai_processor.form_parser.name
}

output "documents_bucket" {
  description = "Documents storage bucket name"
  value       = google_storage_bucket.documents.name
}

output "processed_documents_bucket" {
  description = "Processed documents storage bucket name"
  value       = google_storage_bucket.processed_documents.name
}

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.nayaya_service_account.email
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = google_artifact_registry_repository.nayaya_repo.name
}
