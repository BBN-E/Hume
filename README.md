# Hume
BBN's machine reading system with support from
 DARPA [World Modelers](https://www.darpa.mil/program/world-modelers)
and [Causal Exploration](https://www.darpa.mil/program/causal-exploration) programs. 

## System Requirements

To run Hume, you need a machine with at least 2 cores, 16GB RAM. We're also assuming a Linux machine with [Docker](https://www.docker.com/) installed. 

## Data Preparation

Please pull our docker from Docker Hub:

```bash
docker pull docker.io/wmbbn/hume:R2022_03_21
```

## BYOD Workflows

### W1 (Hume Standalone) workflow

For this mode, we assume you're running Hume as a standalone machine reading system and user will provide the reading materials and fetch results manually. Detailed instructions are at [W1.md](docs/W1.md)

### W1+W2+W3 (Hume integrated with DART) workflow

For this mode, we assume the reading requests come from DART and Hume will get reading materials and pass back reading results automatically with DART. Detailed instructions are at [W1+W2+W3.md](docs/W1+W2+W3.md)

## OIAD (Clustering) workflow

For this mode, Hume deploys a HTTP service as part of a concept discovery system that is joint work with DART and Eidos. Detailed instruction are at [OIAD.md](docs/OIAD.md)

## OIAD (Clustering) API specification

Please refer to [OIAD_API.md](docs/OIAD_API.md) for how to connect to OIAD HTTP service from client

## Acknowledgments

This work was supported in part by DARPA/I2O and U.S. Air Force Research Laboratory Contract No. FA8650-17-C-7716 under the Causal Exploration program, DARPA/I2O and U.S. Army Research Office Contract No. W911NF-18-C-0003 under the World Modelers program, and the Office of the Director of National Intelligence (ODNI), Intelligence Advanced Research Projects Activity (IARPA), via Contract No.: 2021-20102700002. The views, opinions, and/or findings expressed are those of the author(s) and should not be interpreted as necessarily representing the official policies, either expressed or implied, of ODNI, IARPA, the Department of Defense or the U.S. Government. This document does not contain technology or technical data controlled under either the U.S. International Traffic in Arms Regulations or the U.S. Export Administration Regulations.
