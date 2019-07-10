# Hume
BBN's machine reading system for DARPA World Modelers.

**Acknowledgement**: This work was supported by DARPA/I2O Contract No. W911NF-18-C-0003 under the World Modelers program. The views, opinions, and/or findings contained in this article are those of the author and should not be interpreted as representing the official views or policies, either expressed or implied, of the Department of Defense or the U.S. Government. This repository does not contain technology or technical data controlled under either the U.S. International Traffic in Arms Regulations or the U.S. Export Administration Regulations

## Hume Processor

Given a folder of txt files, the dockerized `hume_pipeline` will return a CAG in JSON-LD format. Currently, the CAG will be a json-ld file.

### Data preparation

Please download this file to your local machine (Please email [Haoling](mailto:haoling.qiu@raytheon.com) for downloading these files. Download the tgz files and unzip):

1. `Hume-dependency.tar.gz`
2. `docker_pipeline_wrapped_example.tar.gz`


```bash
mkdir -p hume_runtime
cp Hume-dependency.tar.gz .
tar --xattrs -xpf Hume-dependency.tar.gz
cp docker_pipeline_wrapped_example.tar.gz .
tar --xattrs -xpf docker_pipeline_wrapped_example.tar.gz
```

### Pull docker image

```
docker pull wmbbn/hume:v1.0.0
```

> Note: It's very important for our wrapper to call `/usr/bin/docker` directly without any privilege issue(a.k.a, no sudo, no user interaction happens in between.). if you don’t have permission to run this step, please add your Linux account into group “docker” by “sudo gpasswd -a [YOUR_LINUX_USERNAME_HERE] docker”. You may need to re-login to make it work.

### Test Hume

Navigate to the `docker_pipeline_wrapped_example` directory.

Edit `entry_point.py`: change line 42 `docker_image_id` to `wmbbn/hume:v1.0.0`. Change line 43 `wm_dependency_root` to be the the path to `hume_runtime/hume_dependency`. Next, change line 44 `scratch_space` to a temp folder, e.g., `/tmp/hume`. Warning: this will remove all content in this folder.Line 45 `input_text_folder` to a folder, which contains flatten text files that consist a corpus. Only files ending with `.txt` will be handled.

You’re all set for running experiments. Just run:

```
python3 entry_point.py
```

The result will appear in the `scratch_space/jsonld` folder, as indicated in stdout.

