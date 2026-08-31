group "default" {
  targets = ["rest", "flight_server"]
}

variable "flight_rest_version" {
  default = "1.0.2"
}

variable "flight_server_version" {
  default = "1.0.3"
}

target "rest" {
  context    = "."
  platforms = ["linux/amd64"]
  dockerfile = "rest/Dockerfile"
  tags = ["registry.fly.io/arrow-flight-rest:${flight_rest_version}"]
  output = [{ type = "registry" }]
}

target "flight_server" {
  context    = "."
  platforms = ["linux/amd64"]
  dockerfile = "flight_server/Dockerfile"
  tags = ["registry.fly.io/arrow-flight-server:${flight_server_version}"]
  output = [{ type = "registry" }]
}