import logging
import os
import sys
import time
import yaml


class SambaServerDeployment:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        volumes_config_path = os.getenv('VOLUMES_CONFIG_PATH', '/config/volumes.yaml')
        self.logger.info("VOLUMES_CONFIG_PATH=%s", volumes_config_path)
        self._load_config(volumes_config_path)


    def _wait_start_delay(self) -> None:
        start_delay_in_seconds = int(str(os.getenv('START_DELAY_IN_SECONDS', 0)))
        if start_delay_in_seconds > 0:
            self.logger.info('Wait %d seconds', start_delay_in_seconds)
            time.sleep(start_delay_in_seconds)


    def _load_config(self, config_path: str) -> None:
        with open(config_path, 'r') as fd:
            try:
                self.config = yaml.safe_load(fd)
            except yaml.YAMLError as e:
                self.logger.error('Parse volume config %s FAILED', config_path)
                raise e

        self.logger.debug("volume config: %s", str(self.config))

        for k in ["apiVersion", "kind", "spec"]:
            if k not in self.config:
                raise KeyError(f"'{k}' is not defined in volumes config")

        if self.config["apiVersion"] != "longhorn-volume-manager/v1":
            self.logger.error("Invalid apiVersion defined in volume config")
            raise ValueError(f"apiVersion: {self.config['apiVersion']}' not supported")

        if self.config["kind"] != "LonghornVolumeSpec":
            self.logger.error("Invalid kind defined in volume config")
            raise ValueError(f"'kind: {self.config['kind']}' not supported")

        for k in ["volumes"]:
            if k not in self.config["spec"]:
                raise KeyError(f"'{k}' is not defined in volumes config")


    def create_deployment(self):
        self._wait_start_delay()
        time.sleep(1)


def setup_logging():
    logging.basicConfig(
        level=os.getenv('LOG_LEVEL', "INFO"),
        format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(stream=sys.stdout)
        ]
    )


if __name__ == "__main__":
    setup_logging()
    samba_server = SambaServerDeployment()
    samba_server.create_deployment()
