# IMPORTANT

im just posting this so i know where to download it if i lose it. Thou shalt not expect much,
but if youre interested, there are some instructions down below

# bot-code-avengers

This project mainly about automating a website to get my school assignments done. Thou shouldst know
its basically for my classes 
( 1% finished, need to upgrade so much things omg im gonna die hereat )

# also need this to work properly

**Stable Wi-Fi**
**Docker**

# STEPS AFTER INSTALL DOCKER

To protect your credentials, this bot requires a local config.json file. You can choose one of the following three methods depending on where you prefer to keep your configuration file.

### Option 1: Current Folder (Recommended)
Use this if you want to keep the config.json in the same folder where you are opening your terminal.
```bash
docker run -it \
  -v $(pwd)/config.json:/app/config.json \
  ghcr.io/tachirula/bot-code-avengers:latest

```
### Option 2: Desktop Location
Use this if you want to keep your config.json permanently on your Desktop for easy access.
```bash
docker run -it \
  -v /home/tomas/Desktop/config.json:/app/config.json \
  ghcr.io/tachirula/bot-code-avengers:latest

```
### Option 3: Home Directory
Use this if you prefer to keep the file in your main User folder (~).
```bash
docker run -it \
  -v ~/config.json:/app/config.json \
  ghcr.io/tachirula/bot-code-avengers:latest

```
### Important Note for Users:
Before running any of the commands above, ensure you have created a config.json file with the following format:
```json
{
  "user": "your_email@example.com",
  "pass": "your_password"
}

```
> **Why use volumes?** This method ensures your personal credentials never touch the cloud or the Docker image itself. Your keys stay on your computer, and Docker only "borrows" them while the bot is running.
> 
