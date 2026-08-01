# Taking Flight: Zero Copy Data Transfer at Scale with Apache Arrow Flight and Friends

Welcome to this workshop on Apache Arrow Flight! The goal of this workshop is to give you an
understanding of the Arrow Flight Protocol, how to write a full Server + Client setup in Python and
give you the confidence to get started with your own implementations.

# Getting set up

1. Install Docker
2. Download the dataset
3. Install the CLI
4. Get Started!

## 1. Install Docker

You will need Docker and Docker Compose installed, as we will be running some containers for the
backing services we need. Once the data and images are downloaded, there is no further internet
access required - the material itself is 100% offline.

### ***Troubleshooting Note***

To run all the containers, you will need a decent amount of RAM. I would recommend at least 16GB.

Most Non-linux Docker engines limit the amount of RAM available to containers, so you will need to
adjust your Docker settings accordingly.

<details>

<summary><strong>Linux</strong></summary>

See https://docs.docker.com/engine/install/ and https://docs.docker.com/compose/install/

Linux users do not need to adjust Docker settings for memory consumption since docker is running
natively.

</details>

<details>

<summary><strong>Windows</strong></summary>

See https://docs.docker.com/desktop/

For changing memory settings, see
https://docs.docker.com/desktop/settings-and-maintenance/settings/#resources

</details>

<details>

<summary><strong>MacOS</strong></summary>

I recommend Orbstack: https://orbstack.dev/. Though Docker Desktop is also an
option: https://docs.docker.com/desktop/

For changing memory settings in Orbstack, see https://docs.orbstack.dev/settings#memory-limit to set
the memory limit. For Docker Desktop, see
https://docs.docker.com/desktop/settings-and-maintenance/settings/#resources

</details>

## 2. Dataset

For this demonstration, we'll be using a dataset from Kaggle, which requires a Kaggle account.

For this demo, you will need the following two files:

- https://www.kaggle.com/datasets/mkechinov/direct-messaging?select=campaigns.csv
- https://www.kaggle.com/datasets/mkechinov/direct-messaging?select=messages-demo.csv

Download them, and place them in the `./data` folder

## 3. Install the CLI

This tutorial comes with a `fly` CLI to manage the different services. To install it, use either
`uv` or `pip`.

### UV

If you don't have `uv` already installed, see
https://docs.astral.sh/uv/getting-started/installation/

With uv installed, starting everything:

```bash
uv run fly bootstrap up
```

To shut down the services again, run

```bash
uv run fly bootstrap down
```

To start individual services

```bash
uv run fly start <service>
```

To stop individual services

```bash
uv run fly stop <service>
```

### Pip

If you want to use pip, install the CLI with

```bash
pip install .
```

This will give you access to the `fly` command.

```bash
fly bootstrap up
```

To shut down the services again, run

```bash
fly bootstrap down
```