# Taking Flight: Zero Copy Data Transfer at Scale with Apache Arrow Flight and Friends

Welcome to this workshop on Apache Arrow Flight! The goal of this workshop is to give you an understanding of the Arrow
Flight Protocol, how to write a full Server + Client setup in Python and give you the confidence to get started with
your own implementations.

# Getting set up

1. Install Docker
2. Download the dataset
3. Install the CLI
4. Get Started!

## 1. Install Docker

You will need Docker and Docker Compose installed, as we will be running some containers for the backing services we
need. Once the data and images are downloaded, there is no further internet access required - the material itself is
100% offline.

### ***Troubleshooting Note***

To run all the containers, you will need a decent amount of RAM. 
If you are memory constrained, remember to close the notebooks as we finish them.

Most Non-linux Docker engines limit the amount of RAM available to containers, so you will need to adjust your Docker
settings accordingly.

<details>

<summary><strong>Linux</strong></summary>

See https://docs.docker.com/engine/install/ and https://docs.docker.com/compose/install/

Linux users do not need to adjust Docker settings for memory consumption since docker is running natively.

</details>

<details>

<summary><strong>Windows</strong></summary>

See https://docs.docker.com/desktop/

For changing memory settings, see
https://docs.docker.com/desktop/settings-and-maintenance/settings/#resources

</details>

<details>

<summary><strong>MacOS</strong></summary>

I recommend Orbstack: https://orbstack.dev/. Though Docker Desktop is also an option: https://docs.docker.com/desktop/

For changing memory settings in Orbstack, see https://docs.orbstack.dev/settings#memory-limit to set the memory limit.
For Docker Desktop, see
https://docs.docker.com/desktop/settings-and-maintenance/settings/#resources

</details>

## 2. Dataset

For this demonstration, we'll be using the NYC Bike Trip dataset.

- https://citibikenyc.com/system-data
- https://s3.amazonaws.com/tripdata/index.html

## 3. Install the CLI

This tutorial comes with a `fly` CLI to manage the different services. To install it, use `uv`

### UV

If you don't have `uv` already installed, see
https://docs.astral.sh/uv/getting-started/installation/

## 4. Fetch the data

Fetch the data using the `fly` cli

```bash
uv run fly data download
```

This will fetch the data and place it in the `data` directory. If you want to play around with larger data volumes, you
can download other months using
`fly data download --month <month> --year <year>`

## 5. Start services

To start the services, use the following command

```bash
uv run fly local up
```

This will start the backing services, upload the data and start the notebook server.

To shut down the services again, run

```bash
uv run fly local down
```

This will tear down the services