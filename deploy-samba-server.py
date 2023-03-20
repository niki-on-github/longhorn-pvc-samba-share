import logging
import os
import sys
import time
import yaml
import tempfile
import jinja2



class SambaServerDeployment:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._load_environment_variables()
        self._load_volumes_config()
        self._load_helmrelease_template()


    def _load_environment_variables(self):
        self.env = {
            "IMAGE_REPOSITORY": os.getenv("IMAGE_REPOSITORY", "ghcr.io/crazy-max/samba"),
            "IMAGE_TAG": os.getenv("IMAGE_TAG", "4.16.8"),
            "BJWS_CHART_VERSION": os.getenv("BJWS_CHART_VERSION", "1.3.2"),
            "HELMRELEASE_NAME": os.getenv("HELMRELEASE_NAME", "longhorn-samba"),
            "AFFINITY_HOSTNAME": os.getenv("AFFINITY_HOSTNAME", ""),
            "ADDITIONAL_HOST_VOLUME_PATHS": os.getenv("ADDITIONAL_HOST_VOLUME_PATHS", "").split(";")
        }

        for item in ["SVC_SAMBA_IP", "SAMBA_PASSWORD", "NAMESPACE"]:
            value = os.getenv(item, None)
            if value is None:
                raise ValueError(f"The env var '{item}' is required")
            self.env[item] = value

        self.logger.debug("env vars = %s", str(self.env))


    def _load_helmrelease_template(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="./")
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template("template.yaml.j2")
        self.helm_release = yaml.safe_load(template.render(**self.env))


    def _wait_start_delay(self) -> None:
        start_delay_in_seconds = int(str(os.getenv('START_DELAY_IN_SECONDS', 0)))
        if start_delay_in_seconds > 0:
            self.logger.info('Wait %d seconds', start_delay_in_seconds)
            time.sleep(start_delay_in_seconds)


    def _load_volumes_config(self) -> None:
        volumes_config_path = os.getenv('VOLUMES_CONFIG_PATH', '/config/volumes.yaml')
        self.logger.info("VOLUMES_CONFIG_PATH=%s", volumes_config_path)
        with open(volumes_config_path, 'r') as fd:
            try:
                self.config = yaml.safe_load(fd)
            except yaml.YAMLError as e:
                self.logger.error('Parse volume config %s FAILED', volumes_config_path)
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


    def generate_helmrelease_file(self, dest_name):
        for k in self.config["spec"]["volumes"]:
            if any(x not in self.config["spec"]["volumes"][k] for x in ["createPVC", "namespace"]):
                continue

            if not self.config["spec"]["volumes"][k]["createPVC"]:
                continue

            if self.config["spec"]["volumes"][k]["namespace"] != self.env["NAMESPACE"]:
                self.logger.info("cross namespace not implemented, skip pvc %s", k)
                continue

            self.helm_release["spec"]["values"]["persistence"][k] = {
                "enabled": True,
                "type": "pvc",
                "existingClaim": k,
                "mountPath": "/srv/" + k
            }


        if self.env["AFFINITY_HOSTNAME"] != "":
            for k in self.env["ADDITIONAL_HOST_VOLUME_PATHS"]:
                if len(k) > 1:
                    basename = os.path.basename(k)
                    self.logger.info("add aditional host volume %s:%s", basename, k)
                    self.helm_release["spec"]["values"]["persistence"][basename] = {
                        "enabled": True,
                        "type": "hostPath",
                        "hostPath": k,
                        "mountPath": "/srv/host-volume-" + basename
                    }

            self.helm_release["spec"]["values"]["affinity"] = {
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [{
                            "matchExpressions": [{
                                "key": "kubernetes.io/hostname",
                                "operator": "In",
                                "values": [
                                    self.env["AFFINITY_HOSTNAME"]
                                ]
                                }]
                            }]
                        }
                    }
                }

        with open(dest_name, 'w') as f:
            yaml.dump(self.helm_release, f)

        os.system("cat {}".format(dest_name))


    def process(self):
        self._wait_start_delay()
        self.delete_helmrelease(self.env["NAMESPACE"], self.env["HELMRELEASE_NAME"])
        with tempfile.NamedTemporaryFile(suffix='.yaml') as tmp:
            self.generate_helmrelease_file(tmp.name)
            self.apply_helmrelease(tmp.name)
        time.sleep(1)


    def delete_helmrelease(self, namespace, name):
        os.system(f"kubectl delete HelmRelease --namespace={namespace} {name}")
        os.system(f"kubectl delete deployment --namespace={namespace} {name}")
        self.logger.info("HelmRelease %s deleted.", name)


    def apply_helmrelease(self, file_path):
        os.system(f"kubectl apply -f {file_path}")
        self.logger.info("HelmRelease created")


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
    samba_server.process()
