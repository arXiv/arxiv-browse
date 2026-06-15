output "service_url" {
  description = "The URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.arxiv_browse.uri
}

output "service_name" {
  description = "The name of the Cloud Run service"
  value       = google_cloud_run_v2_service.arxiv_browse.name
}

output "service_location" {
  description = "The location of the Cloud Run service"
  value       = google_cloud_run_v2_service.arxiv_browse.location
}

output "service_id" {
  description = "The ID of the Cloud Run service"
  value       = google_cloud_run_v2_service.arxiv_browse.id
}
