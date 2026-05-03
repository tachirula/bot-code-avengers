# IMPORTANT

im just posting this so i know where to download it if i lose it. Thou shalt not expect much,
but if youre interested, there are some instructions down below

# bot-code-avengers

This project mainly about automating a website to get my school assignments done. Thou shouldst know
its basically for my classes 
( 1% finished, need to upgrade so much things omg im gonna die hereat )

# also need this to work properly

**Docker**

STEPS AFTER INSTALL DOCKER

build docker
```
docker run -it mi-bot .
```
run docker with your own config.json
```
docker run -it \
  -v $(pwd)/config.json:/app/config.json \
  mi-bot
```
> Keep your config.json private and never commit it to the repository
