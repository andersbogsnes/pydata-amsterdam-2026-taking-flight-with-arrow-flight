terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket    = "terraform-state-449650107887-eu-north-1-an"
    use_lockfile = true
    key       = "arrow-flight"
    region = "eu-north-1"
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.region
}
