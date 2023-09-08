# SenseCraft-AI-webUI

- Deploy SenseCraft-AI-webUI from Seeed Studio, See [its github](https://github.com/Seeed-Studio/SenseCraft-AI-webUI) for more details.

## Build dist/

```sh
# maybe don't clone others repo in Edge repo
cd .. 
# download Ui repo
git clone https://github.com/Seeed-Studio/SenseCraft-AI-webUI
# go to the Ui repo
cd SenseCraft-AI-webUI
# follow documents to build `dist/`
ls dist/
```

## Method 1: copy dist into this project

```sh
# back to Edge repo
cd ../SenseCraft-AI_Server
# copy dist to Edge repo
cp ../SenseCraft-AI-webUI/dist/ ./ 
# scipts/run.sh => `-v $PWD/dist:/opt/dev/dist/ \` will be ok, just run
bash scipts/run.sh
```

## Method 2: set dist to other project

```sh
# set EDGEAI_WEB_DIST_PATH to ../xxxx/dist/
vim scripts/run.sh
# replace `-v $PWD/dist:/opt/dev/dist/ \` to `-v /path/to/SenseCraft-AI-webUI/dist:/opt/dev/dist/ \`
bash scipts/run.sh
```
