# Seeed SenseCraft-AI UI

- Deploy SenseCraft-AI-Ui from Seeed Studio, See [its github](https://github.com/Seeed-Studio/SenseCraft-AI-Ui) for more details.

## Build dist/

```sh
# maybe don't clone others repo in Edge repo
cd .. 
# download Ui repo
git clone https://github.com/Seeed-Studio/SenseCraft-AI-Ui
# go to the Ui repo
cd Seeed-SenseCraft-AI-Ui
# follow documents to build `dist/`
ls dist/
```

## Method 1: copy dist into this project

```sh
# back to Edge repo
cd ../Seeed-SenseCraft-AI-Edge
# copy dist to Edge repo
cp ../Seeed-SenseCraft-AI-Ui/dist/ ./ 
# scipts/run.sh => `-v $PWD/dist:/opt/dev/dist/ \` will be ok, just run
bash scipts/run.sh
```

## Method 2: set dist to other project

```sh
# set EDGEAI_WEB_DIST_PATH to ../xxxx/dist/
vim scripts/run.sh
# replace `-v $PWD/dist:/opt/dev/dist/ \` to `-v /path/to/Seeed-SenseCraft-AI-Ui/dist:/opt/dev/dist/ \`
bash scipts/run.sh
```
