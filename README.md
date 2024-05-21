# trafficgen

Traffic generation framework that runs an android emulator and interact with it for a determined amount of time, generating a traffic capture in form of `.pcap` files in the process.

The framework is split into different types of experiments. Each experiments is an a separate interaction scenario that all utilizes the android emulator. The following experiments are available:

1. RandomApp:
    - pick a random app from 8 programmed apps (youtube, twitter, instagram, candycrush, spotify, discord, amazon shopping, reddit)
    - interact randomly with the app to simulate normal usage (watch videos, send messages, like posts, add items to cart etc)
    - switch apps after a predetermined amount of time.
2. RandomBrowse: (adapted from Hao Yun's version)
    - pick a random website from a list of 500+ websites
    - scroll and click randomly with the website to simulate normal usage
3. RandomVpn: (adapted from QCRI's test bed)
    - pick a random apk known to be affiliated with a VPN
    - interact with it and/or idle with the app open in the foreground

The following are instructions to get set up and run this framework on your machine. We are assuming you are using a linux environment. Running on macOS or Windows might need some extra setup.

## Setting up

The minimum required python version is 3.10. Run `python --version` to check.

To start, clone the project and make sure you are at the project's root folder.

It is recommended that you use a virtual python environment for this. There are many ways to set an a virtual environment and you may choose between `venv`, `virtualenv` or `pyenv`. This guide includes the instructions for `pyenv`. The use of virtual environment is optional.

### Setting up python virtual environment with pyenv (optional)

`pyenv` is a tool that helps you install any old or new versions of python, create and manage virtual environment using any specific version of python, and bind any virtualenv to a certain directory.

Install pyenv:

```shell
# install some dependencies that enable pyenv to install arbitrary python versions
sudo apt update
sudo apt install build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl git libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
# install pyenv
curl https://pyenv.run | bash
# add pyenv to .bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
```

Install python 3.10, create virtual environment:

```shell
pyenv install 3.10
pyenv virtualenv 3.10 trafficgen
pyenv local trafficgen
```

Install requirements and the program itself:

```shell
pip install -r requirements.txt
pip install -e .
```

Your python environment should now be set up and good to go

### Download apks

In order to properly run the experiments, this program needs some APK files. Since it is relatively big, the APK files are not included in this repository.

1. Download [https://drive.google.com/file/d/1IFbtKbOupwqqLs9DPEF7GNMj1ruXE5Td/view?usp=drive_link] and extract the contents into the folder `trafficgen/experiments/randomapp/apks/`
2. Download [https://drive.google.com/file/d/1mORNYFOuzHebs-Ef8xExYo5d9eh1MXhB/view?usp=drive_link] and extract the contents into the folder `trafficgen/experiments/randomvpn/apkfiles/`

### Set up Android Virtual Devices (avd)

In order for the program to run and control Android emulator, some setting up must be done before hand. In particular, you will have to create an Android Virtual Device (avd).

- Install Android Studio, along with Android SDK suite that comes with it. More instructions on the [official site](https://developer.android.com/studio/install).
- Make sure you can run the android emulator from the commandline. Check with `emulator -version`
- Make sure you can run the android debug bridge from the commandline. Check with `adb --version`
- Open Android Studio, create a new device with the following settings:
  - Device Preset: Use Pixel 4
  - Android Image: Use android R, x86, Google Play image (API level 30)
  - create it and note the name of the AVD (should be Pixel_4_API_30)
- Now you should be ready to run the experiments

### Create a config file

```shell
cp config.yaml.example config.yaml
```

Available config options should be explained in the config file itself.

### Set up credentials for the RandomApp experiment

The RandomApp experiment involve running and interacting with apps that requires an account, like YouTube, Instagram, Discord, etc. You have to sign up for those services prior to running the experiment. Here are the steps:

- Create a new gmail account only for testing purposes. Put the email and password in the config file
- Start up the emulator, log into Google Play Store using the email.
- Download and install Instagram
- Sign up for an instagram account and log in, make sure you can browse normally.
- Download and install Twitter (X). Create a new account with Google Login.
- Download and install Spotify. Create a new account with Google Login.
- Download and install Reddit. Create a new account with Google Login.
- Download and install Discord. Create a new account with the email, and set a password. Write the password into the config file. Create a new Discord Server (or join an existing one if you have your own). In the server create two text channels: spammable and watchable. In watchable, send a few sample video clips into the channel. This will be the only two channel that the script will interact with.

After that is done, setup is completed and ready to be run.

## Running the program

You can now run the program with `python trafficgen` from the project root directory

Here is the usage in details:

```text
# python trafficgen --help
usage: trafficgen [-h] [-c CONFIG] [experiment] ...

Generate traffic in android emulator and capture them into pcap files.

positional arguments:
  experiment            Name of the experiment to execute
  args                  Arguments for the experiment if any

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Config file, must be in yaml/yml format
```

To run other experiments:

```shell
python trafficgen randombrowse
python trafficgen randomvpn
```

You can override config files using --config flag. Notice this must comes before the experiment name:

```shell
python trafficgen --config /path/to/config.yaml randomapp
```

Some experiments will take in optional commandline flags

```shell
python trafficgen --config /path/to/config.yaml randomapp --init
python trafficgen --config /path/to/config.yaml randomapp --init-only
python trafficgen --config /path/to/config.yaml randombrowse --init
```

Find explanations of what the flag does for each experiments:

```text
# python trafficgen randomapp --help
usage: trafficgen [-h] [--init] [--init-only]

Experiment randomapp.

options:
  -h, --help   show this help message and exit
  --init       If set, emulator will first do a separate session with -wipe-data, to install apks
               and setups and logins, then restart and do the actual experiment.
  --init-only  If set, emulator will only start up and do setups, install apks and logins, then shut
               off without doing experiments. Will override --init.
```

```text
# python trafficgen randombrowse --help
usage: trafficgen [-h] [--init] [--existing-emulator]

Experiment randomapp.

options:
  -h, --help           show this help message and exit
  --init               If set, emulator will start up fresh with -wipe-data, and do initial chrome
                       set up.
  --existing-emulator  If set, will not start (nor kill) any emulators. Assuming an emulator process
                       is already running and will only take control of it.
```

```text
# python trafficgen randomvpn --help
usage: trafficgen [-h] [--init] [--existing-emulator]

Experiment randomvpn.

options:
  -h, --help           show this help message and exit
  --init               If set, emulator will start up fresh with -wipe-data, and do initial chrome
                       set up.
  --existing-emulator  If set, will not start (nor kill) any emulators. Assuming an emulator process
                       is already running and will only take control of it.
```

## Running in Docker

An alternative way to run is to run inside docker containers. The following are instructions to set up and run on docker.

1. Ensure that docker is installed on your system
2. Build the container image with `docker build -t trafficgen .`
3. Start the container with

```shell
docker run -it --privileged --name trafficgen trafficgen
```

You can customize various aspect of the AVD, Android image, and APK version by taking a look at the Dockerfile and changing appropriate values to suit your needs.

If the emulator report errors and unable to start, you may need to manually install android studio and use it to create the AVD, then copy the AVD into the container image.
