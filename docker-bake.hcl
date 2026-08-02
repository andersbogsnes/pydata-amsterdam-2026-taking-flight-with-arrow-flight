group "default" {
  targets = ["rest", "flight_server"]
}

variable "flight_rest_version" {
  default = "1.0.0"
}

variable "flight_server_version" {
  default = "1.0.0"
}

target "rest" {
  context    = "."
  dockerfile = "rest/Dockerfile"
  tags = ["docker.io/andersbogsnes/flight_rest:${flight_rest_version}"]
  output = [{ type = "registry" }]
}

target "flight_server" {
  context    = "."
  dockerfile = "flight_server/Dockerfile"
  tags = ["docker.io/andersbogsnes/flight_server:${flight_server_version}"]
  output = [{ type = "registry" }]
}