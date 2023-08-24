# mqtt-output

To obtain recognition result data by enabling mqtt, please first confirm that mqtt is deployed locally

```sh
# (optional) install mqtt clients tool if you don't have mqtt-tool.
sudo apt install mosquitto-clients
# if your mqtt-broker do not set auth
mosquitto_sub -t edgeai/result
# if your mqtt-broker need username and password
mosquitto_sub -t edgeai/result -u seeed -P BP6Y6XT4PvE4 -h 127.0.0.1 -p 1883
```
