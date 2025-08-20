```
           _      __                  _       
 _ __ ___ | |__  / _|_ __   ___  _ __| |_ ___ 
| '_ ` _ \| '_ \| |_| '_ \ / _ \| '__| __/ __|
| | | | | | | | |  _| |_) | (_) | |  | |_\__ \
|_| |_| |_|_| |_|_| | .__/ \___/|_|   \__|___/
                    |_|                       

```

> [!WARNING]
> `mhfports` is in early development!

The `mighf` port-manager and package manager.

## Intro
> What does `port-manager` mean?
A `port-manager`, in this case, is a tool that allows people to make ports of the `mighf` architecture to multiple platforms, which is source-code independent from the `mighf` github repository. It uses a toml-based spec file to define configurations and instructions for the port, the `mhfports --new <portname>` helps you to make a common mighf port with a default spec, which has everything that common mighf has.

## Installation
You can install mhfports with [eget](https://github.com/<?>/eget)
```bash
eget mighf/mhfports
```
Or you can install it with cargo:
```bash
pip install -E https://github.com/oakymacintosh/mhfports
```

## Usage
### Package management
```bash
mhfports get <ghUser/repoName> # install a package from github
mhfports list # list all installed packages
mhfports remove <packageName> # remove a package
mhfports update <packageName> # update a package
mhfports build --target=self-mighf --mighf-base=spec:mighf-ommi # build a package for the mighf architecture
```
